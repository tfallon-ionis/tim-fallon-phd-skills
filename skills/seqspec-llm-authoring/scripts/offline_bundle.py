#!/usr/bin/env python3
"""Package and verify an attested source-linked Seqspec for offline use."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

try:
    from scripts.validate import (
        archive_member_bytes,
        fetch_remote_bytes,
        match_container,
        root_member_bytes,
        uncompressed_bytes,
    )
except ModuleNotFoundError:
    from validate import (  # type: ignore[no-redef]
        archive_member_bytes,
        fetch_remote_bytes,
        match_container,
        root_member_bytes,
        uncompressed_bytes,
    )

class BundleFailure(Exception):
    """Raised when an offline bundle cannot be safely produced or verified."""


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BundleFailure(f"cannot read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BundleFailure(f"expected a YAML mapping in {path}")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def collect_onlists(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            native = node.get("onlist")
            if isinstance(native, dict):
                file_id = native.get("file_id")
                if not isinstance(file_id, str) or not file_id:
                    raise BundleFailure("every Seqspec onlist requires a nonempty file_id")
                if file_id in found:
                    raise BundleFailure(f"duplicate Seqspec onlist file_id: {file_id}")
                found[file_id] = native
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(spec)
    return found


def safe_filename(value: Any, file_id: str) -> str:
    if not isinstance(value, str) or not value:
        raise BundleFailure(f"onlist {file_id} requires a filename")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1 or path.name != value or value in (".", ".."):
        raise BundleFailure(f"onlist {file_id} filename must be a safe basename")
    return value


def indexed_sidecar_onlists(sidecar: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = sidecar.get("onlists")
    if not isinstance(records, list):
        raise BundleFailure("provenance sidecar requires an onlists list")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("file_id"), str):
            raise BundleFailure("every sidecar onlist requires a file_id")
        file_id = record["file_id"]
        if file_id in indexed:
            raise BundleFailure(f"duplicate sidecar onlist file_id: {file_id}")
        indexed[file_id] = record
    return indexed


def require_attested_source(
    source_profile: Path,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    seqspec_path = source_profile / "seqspec.yaml"
    sidecar_path = source_profile / "provenance.sidecar.yaml"
    if not source_profile.is_dir() or not seqspec_path.is_file() or not sidecar_path.is_file():
        raise BundleFailure(
            "source profile must contain seqspec.yaml and provenance.sidecar.yaml"
        )
    spec = load_yaml(seqspec_path)
    sidecar = load_yaml(sidecar_path)
    validation = sidecar.get("validation", {})
    confirmation = validation.get("user_confirmation", {}) if isinstance(validation, dict) else {}
    complete = (
        sidecar.get("status") == "complete"
        and validation.get("status") == "complete"
        and bool(validation.get("validated_at"))
        and confirmation.get("status") == "confirmed"
        and bool(confirmation.get("confirmed_at"))
    )
    if not complete:
        raise BundleFailure("offline packaging requires an attested complete source-linked profile; drafts are rejected")
    assay_id = spec.get("assay_id")
    sidecar_assay_id = sidecar.get("profile", {}).get("seqspec_assay_id")
    if not isinstance(assay_id, str) or assay_id != sidecar_assay_id:
        raise BundleFailure("Seqspec assay_id and sidecar profile.seqspec_assay_id must match")
    if source_profile.name != assay_id:
        raise BundleFailure("source profile directory name must equal the Seqspec assay_id")
    return sidecar_path, spec, sidecar


def verify_digests(
    file_id: str,
    filename: str,
    native: dict[str, Any],
    record: dict[str, Any],
    stored: bytes,
) -> None:
    try:
        content = uncompressed_bytes(filename, stored)
    except Exception as exc:
        raise BundleFailure(str(exc)) from exc
    if native.get("filesize") != len(stored):
        raise BundleFailure(f"stored filesize mismatch for {file_id}")
    if hashlib.md5(content).hexdigest() != native.get("md5"):
        raise BundleFailure(f"native Seqspec MD5 mismatch for {file_id}")
    for label, value in (
        ("uncompressed", record.get("content_digest")),
        ("stored-artifact", record.get("stored_artifact_digest")),
    ):
        if not isinstance(value, dict) or value.get("algorithm") != "sha256":
            raise BundleFailure(f"onlist {file_id} requires a {label} SHA-256 digest")
    if sha256_bytes(content) != record["content_digest"]["value"]:
        raise BundleFailure(f"uncompressed SHA-256 mismatch for {file_id}")
    if sha256_bytes(stored) != record["stored_artifact_digest"]["value"]:
        raise BundleFailure(f"stored-artifact SHA-256 mismatch for {file_id}")


def resolve_source_onlist(
    source_profile: Path,
    native: dict[str, Any],
    record: dict[str, Any],
    supplied: list[Path],
) -> bytes:
    file_id = record["file_id"]
    filename = safe_filename(native.get("filename"), file_id)
    if record.get("filename") != filename:
        raise BundleFailure(f"onlist filename mismatch for {file_id}")
    availability = record.get("availability")
    urltype = native.get("urltype")
    url = native.get("url")
    try:
        if availability == "authoritative_public":
            if urltype not in ("http", "https", "ftp") or not isinstance(url, str):
                raise BundleFailure(f"public onlist {file_id} requires a direct source URL")
            stored = fetch_remote_bytes(url)
        elif availability == "documentary_transcription":
            if urltype != "local" or url != filename:
                raise BundleFailure(f"documentary onlist {file_id} must use its local basename")
            stored = (source_profile / filename).read_bytes()
        elif availability == "supplied_container":
            expected = record.get("container")
            if not isinstance(expected, dict):
                raise BundleFailure(f"container-backed onlist {file_id} lacks container metadata")
            container = match_container(expected, supplied)
            if container.is_dir():
                stored = root_member_bytes(container, expected["member_path"])
            else:
                stored = archive_member_bytes(container, expected["member_path"])
        else:
            raise BundleFailure(
                f"onlist {file_id} availability {availability!r} cannot be packaged"
            )
    except BundleFailure:
        raise
    except Exception as exc:
        raise BundleFailure(f"cannot resolve onlist {file_id}: {exc}") from exc
    verify_digests(file_id, filename, native, record, stored)
    return stored


def semantic_source_form(spec: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(spec)
    for native in collect_onlists(normalized).values():
        native["url"] = "<onlist-location>"
        native["urltype"] = "<onlist-location-type>"
    return normalized


def require_contained_regular_file(bundle: Path, target: Path, label: str) -> None:
    if target.is_symlink() or not target.is_file():
        raise BundleFailure(f"{label} must be a regular, non-symlink file")
    try:
        target.resolve().relative_to(bundle.resolve())
    except ValueError as exc:
        raise BundleFailure(f"{label} escapes the offline bundle") from exc


def run_seqspec_check(seqspec_path: Path) -> None:
    environment = os.environ.copy()
    offline_proxy = "http://127.0.0.1:9"
    environment.update(
        {
            "ALL_PROXY": offline_proxy,
            "HTTP_PROXY": offline_proxy,
            "HTTPS_PROXY": offline_proxy,
            "NO_PROXY": "",
            "all_proxy": offline_proxy,
            "http_proxy": offline_proxy,
            "https_proxy": offline_proxy,
            "no_proxy": "",
        }
    )
    try:
        result = subprocess.run(
            ["seqspec", "check", str(seqspec_path)],
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BundleFailure(f"cannot run offline seqspec check: {exc}") from exc
    detail = (result.stdout + "\n" + result.stderr).strip()
    reported_errors = any(line.lstrip().startswith("[error ") for line in detail.splitlines())
    if result.returncode != 0 or reported_errors:
        raise BundleFailure(f"offline seqspec check failed:\n{detail}")


def verify_offline_bundle(
    source_profile: Path,
    bundle: Path,
    *,
    run_check: bool = True,
) -> None:
    source_sidecar, source_spec, source_provenance = require_attested_source(source_profile)
    if not bundle.is_dir() or bundle.name != source_profile.name:
        raise BundleFailure("offline bundle directory must exist and be named for the Seqspec assay_id")
    bundle_seqspec = bundle / "seqspec.yaml"
    bundle_sidecar = bundle / "provenance.sidecar.yaml"
    for path in (bundle_seqspec, bundle_sidecar):
        require_contained_regular_file(bundle, path, path.name)
    if bundle_sidecar.read_bytes() != source_sidecar.read_bytes():
        raise BundleFailure("offline provenance sidecar must be byte-identical to the source-linked sidecar")

    packaged_spec = load_yaml(bundle_seqspec)
    source_onlists = collect_onlists(source_spec)
    packaged_onlists = collect_onlists(packaged_spec)
    sidecar_onlists = indexed_sidecar_onlists(source_provenance)
    if set(source_onlists) != set(packaged_onlists) or set(source_onlists) != set(sidecar_onlists):
        raise BundleFailure("source, packaged, and sidecar onlist file_id sets must match")
    filenames: list[str] = []
    for file_id, native in packaged_onlists.items():
        filename = safe_filename(native.get("filename"), file_id)
        expected_url = f"onlists/{filename}"
        if native.get("urltype") != "local" or native.get("url") != expected_url:
            raise BundleFailure(f"packaged onlist {file_id} must resolve under onlists/")
        target = bundle / "onlists" / filename
        require_contained_regular_file(bundle, target, expected_url)
        verify_digests(file_id, filename, native, sidecar_onlists[file_id], target.read_bytes())
        filenames.append(filename)
    if semantic_source_form(source_spec) != semantic_source_form(packaged_spec):
        raise BundleFailure("source-linked and offline Seqspec differ beyond onlist locations")

    expected_payloads = {
        "seqspec.yaml",
        "provenance.sidecar.yaml",
        *(f"onlists/{filename}" for filename in filenames),
    }
    actual_files = {
        path.relative_to(bundle).as_posix()
        for path in bundle.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_payloads:
        raise BundleFailure("offline bundle contains unexpected files")
    if run_check:
        run_seqspec_check(bundle_seqspec)


def package_offline_bundle(
    source_profile: Path,
    output_root: Path,
    *,
    onlist_containers: list[Path] | None = None,
    run_check: bool = True,
) -> Path:
    source_profile = source_profile.resolve()
    source_sidecar, spec, sidecar = require_attested_source(source_profile)
    source_onlists = collect_onlists(spec)
    sidecar_onlists = indexed_sidecar_onlists(sidecar)
    if set(source_onlists) != set(sidecar_onlists):
        raise BundleFailure("source Seqspec and sidecar onlist file_id sets must match")

    filenames: dict[str, str] = {}
    for file_id, native in source_onlists.items():
        filename = safe_filename(native.get("filename"), file_id)
        other = filenames.get(filename)
        if other is not None:
            raise BundleFailure(f"onlist filename collision: {other} and {file_id} both use {filename}")
        filenames[filename] = file_id

    destination_parent = output_root.resolve() / "offline-bundles"
    destination = destination_parent / source_profile.name
    if destination.exists():
        raise BundleFailure(f"offline bundle already exists: {destination}")
    destination_parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{source_profile.name}.tmp-", dir=destination_parent)
    )
    temporary = staging_root / source_profile.name
    temporary.mkdir()
    try:
        (temporary / "onlists").mkdir()
        packaged_spec = copy.deepcopy(spec)
        packaged_onlists = collect_onlists(packaged_spec)
        supplied = onlist_containers or []
        for file_id, native in source_onlists.items():
            filename = native["filename"]
            stored = resolve_source_onlist(
                source_profile,
                native,
                sidecar_onlists[file_id],
                supplied,
            )
            (temporary / "onlists" / filename).write_bytes(stored)
            packaged_onlists[file_id]["url"] = f"onlists/{filename}"
            packaged_onlists[file_id]["urltype"] = "local"
        rendered = yaml.safe_dump(packaged_spec, sort_keys=False, allow_unicode=True)
        (temporary / "seqspec.yaml").write_text(rendered, encoding="utf-8")
        shutil.copyfile(source_sidecar, temporary / "provenance.sidecar.yaml")
        verify_offline_bundle(source_profile, temporary, run_check=run_check)
        temporary.replace(destination)
        staging_root.rmdir()
    except Exception:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    package = subparsers.add_parser("package", help="materialize and verify an offline bundle")
    package.add_argument("--source-profile", required=True, type=Path)
    package.add_argument("--output-root", required=True, type=Path)
    package.add_argument("--onlist-container", action="append", default=[], type=Path)
    verify = subparsers.add_parser("verify", help="verify an existing offline bundle")
    verify.add_argument("--source-profile", required=True, type=Path)
    verify.add_argument("--bundle", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "package":
            bundle = package_offline_bundle(
                args.source_profile,
                args.output_root,
                onlist_containers=args.onlist_container,
            )
            print(f"PACKAGED AND VERIFIED: {bundle}")
        else:
            verify_offline_bundle(args.source_profile, args.bundle)
            print(f"VERIFIED: {args.bundle}")
        return 0
    except BundleFailure as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
