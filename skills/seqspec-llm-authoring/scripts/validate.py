#!/usr/bin/env python3
"""Validate a vanilla seqspec and its provenance sidecar as one artifact."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.metadata
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema
import yaml

MIN_SEQSPEC_VERSION = (0, 4, 0)
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "seqspec-sources.schema.json"
COMPLETE_NAMES = ("seqspec.yaml", "provenance.sidecar.yaml")
DRAFT_NAMES = ("seqspec.draft.yaml", "provenance.draft.sidecar.yaml")


class ValidationFailure(Exception):
    """Raised for one or more user-correctable validation errors."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seqspec", required=True, type=Path)
    parser.add_argument("--sidecar", required=True, type=Path, help="Provenance sidecar.")
    parser.add_argument(
        "--onlist-container",
        action="append",
        default=[],
        type=Path,
        help="Vendor archive or decompressed root; repeat as needed.",
    )
    parser.add_argument(
        "--no-write-attestation",
        action="store_true",
        help="Validate without updating the successful attestation.",
    )
    return parser.parse_args()


def version_tuple(value: str) -> tuple[int, int, int]:
    numeric: list[int] = []
    for part in value.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        if not digits:
            break
        numeric.append(int(digits))
        if len(numeric) == 3:
            break
    return tuple((numeric + [0, 0, 0])[:3])  # type: ignore[return-value]


def installed_seqspec_version() -> str:
    try:
        value = importlib.metadata.version("seqspec")
    except importlib.metadata.PackageNotFoundError as exc:
        raise ValidationFailure("the supported seqspec implementation is not installed") from exc
    if version_tuple(value) < MIN_SEQSPEC_VERSION:
        raise ValidationFailure(f"seqspec {value} is too old; require >=0.4.0")
    try:
        from seqspec.Region import Onlist
    except ImportError as exc:
        raise ValidationFailure("installed seqspec lacks the Onlist model") from exc
    required_fields = {"sequence_column_index", "skip_rows"}
    missing_fields = sorted(required_fields - set(Onlist.model_fields))
    if missing_fields:
        raise ValidationFailure(
            "installed seqspec is not the supported projection-capable implementation; "
            f"missing Onlist fields: {', '.join(missing_fields)}"
        )
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValidationFailure(f"cannot read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationFailure(f"expected a YAML mapping in {path}")
    return value


def requested_onlist_projections(path: Path) -> dict[str, tuple[int, int]]:
    """Read projection fields without relying on the installed seqspec model."""
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise ValidationFailure(f"cannot inspect onlist projections in {path}: {exc}") from exc

    projections: dict[str, tuple[int, int]] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            if "file_id" in node and ("sequence_column_index" in node or "skip_rows" in node):
                try:
                    projections[str(node["file_id"])] = (
                        int(node.get("sequence_column_index", 0)),
                        int(node.get("skip_rows", 0)),
                    )
                except (TypeError, ValueError) as exc:
                    raise ValidationFailure(f"onlist {node['file_id']} projection fields must be integers") from exc
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return projections


def validate_json_schema(sidecar: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(sidecar), key=lambda err: list(err.path))
    if errors:
        lines = []
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            lines.append(f"{location}: {error.message}")
        raise ValidationFailure("sidecar schema errors:\n  - " + "\n  - ".join(lines))


def require_unique(records: Iterable[dict[str, Any]], key: str, label: str) -> set[str]:
    values: list[str] = [record[key] for record in records]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValidationFailure(f"duplicate {label}: {', '.join(duplicates)}")
    return set(values)


def validate_references(sidecar: dict[str, Any]) -> None:
    sources = sidecar["sources"]
    source_ids = require_unique(sources, "source_id", "source_id values")
    if not any(source["authority"] == "authoritative" for source in sources):
        raise ValidationFailure("at least one authoritative source is required")

    vendor_ids = require_unique(sidecar["vendors"], "vendor_id", "vendor_id values")
    require_unique(sidecar["claims"], "claim_id", "claim_id values")

    def assert_sources(ids: list[str], context: str, *, nonempty: bool = True) -> None:
        if nonempty and not ids:
            raise ValidationFailure(f"{context} requires at least one source_id")
        unknown = sorted(set(ids) - source_ids)
        if unknown:
            raise ValidationFailure(f"{context} references unknown source_id: {', '.join(unknown)}")

    library_kit = sidecar["library_format"]["representative_kit"]
    sequence_kit = sidecar["sequencing"]["sequence_kit"]
    for label, kit in (("representative library kit", library_kit), ("sequencing kit", sequence_kit)):
        if kit["manufacturer_id"] not in vendor_ids:
            raise ValidationFailure(f"{label} references unknown manufacturer_id {kit['manufacturer_id']}")
        assert_sources(kit["source_ids"], label)

    if not library_kit["catalog_number"]:
        raise ValidationFailure("representative library kit requires a catalog_number")
    if sequence_kit.get("catalog_number_status") not in ("documented", "not_available"):
        raise ValidationFailure("sequencing kit requires catalog_number_status")
    if sequence_kit.get("catalog_number_status") == "documented" and not sequence_kit.get("catalog_number"):
        raise ValidationFailure("documented sequencing-kit catalog_number cannot be null")
    if sequence_kit.get("catalog_number_status") == "not_available" and sequence_kit.get("catalog_number"):
        raise ValidationFailure("sequencing-kit catalog_number must be null when status is not_available")

    for artifact in sidecar["artifacts"]:
        assert_sources(artifact["source_ids"], f"artifact {artifact['artifact_id']}")
    for onlist in sidecar["onlists"]:
        assert_sources(onlist["source_ids"], f"onlist {onlist['file_id']}")
        availability = onlist["availability"]
        if availability == "documentary_transcription":
            if "derivation" not in onlist:
                raise ValidationFailure(f"documentary transcription {onlist['file_id']} requires derivation metadata")
        elif "derivation" in onlist:
            raise ValidationFailure(f"onlist {onlist['file_id']} may only use derivation with documentary_transcription")
        if availability == "supplied_container":
            if "container" not in onlist:
                raise ValidationFailure(f"onlist {onlist['file_id']} requires container metadata")
        elif "container" in onlist:
            raise ValidationFailure(f"onlist {onlist['file_id']} may only use container with supplied_container")
    for claim in sidecar["claims"]:
        assert_sources(
            claim["source_ids"],
            f"claim {claim['claim_id']}",
            nonempty=claim["basis"] == "documentary",
        )
    for conflict in sidecar["conflicts"]:
        assert_sources(conflict["selected"]["source_ids"], f"conflict {conflict['conflict_id']} selected")
        for rejected in conflict["rejected"]:
            assert_sources(rejected["source_ids"], f"conflict {conflict['conflict_id']} rejected")

    documentary_targets = {claim["target"] for claim in sidecar["claims"] if claim["basis"] == "documentary"}
    required_targets = {
        "library_format.representative_kit.product_name",
        "library_format.representative_kit.manufacturer_id",
        "library_format.representative_kit.catalog_number",
        "sequencing.sequence_kit.product_name",
        "sequencing.sequence_kit.manufacturer_id",
    }
    if sequence_kit.get("catalog_number_status") == "documented":
        required_targets.add("sequencing.sequence_kit.catalog_number")
    missing = sorted(required_targets - documentary_targets)
    if missing:
        raise ValidationFailure("missing field-level documentary claims: " + ", ".join(missing))


def validate_lifecycle(sidecar: dict[str, Any], seqspec_path: Path, sidecar_path: Path) -> None:
    status = sidecar["status"]
    validation = sidecar["validation"]
    if validation["sidecar_schema_version"] != sidecar["sources_schema_version"]:
        raise ValidationFailure("validation.sidecar_schema_version must match sources_schema_version")
    confirmation = validation["user_confirmation"]
    if confirmation["status"] == "confirmed" and not confirmation["confirmed_at"]:
        raise ValidationFailure("confirmed user_confirmation requires confirmed_at")
    if confirmation["status"] == "pending" and confirmation["confirmed_at"] is not None:
        raise ValidationFailure("pending user_confirmation requires confirmed_at: null")
    if status == "complete":
        if (seqspec_path.name, sidecar_path.name) != COMPLETE_NAMES:
            raise ValidationFailure("complete artifacts must use seqspec.yaml and provenance.sidecar.yaml")
        if validation["blocking_gaps"]:
            raise ValidationFailure("complete artifacts cannot contain blocking_gaps")
    else:
        if (seqspec_path.name, sidecar_path.name) != DRAFT_NAMES:
            raise ValidationFailure(
                "draft artifacts must use seqspec.draft.yaml and provenance.draft.sidecar.yaml"
            )
        if validation["status"] != "draft":
            raise ValidationFailure("draft artifact validation.status must be draft")
        if not validation["blocking_gaps"]:
            raise ValidationFailure("draft artifacts must enumerate blocking_gaps")


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_member_path(value: str) -> PurePosixPath:
    member = PurePosixPath(value)
    if member.is_absolute() or ".." in member.parts:
        raise ValidationFailure(f"unsafe archive member_path: {value}")
    return member


def archive_member_bytes(container: Path, member_path: str) -> bytes:
    member = safe_member_path(member_path).as_posix()
    if zipfile.is_zipfile(container):
        with zipfile.ZipFile(container) as archive:
            try:
                return archive.read(member)
            except KeyError as exc:
                raise ValidationFailure(f"{member} not found in {container.name}") from exc
    if tarfile.is_tarfile(container):
        with tarfile.open(container, "r:*") as archive:
            try:
                entry = archive.getmember(member)
            except KeyError as exc:
                raise ValidationFailure(f"{member} not found in {container.name}") from exc
            handle = archive.extractfile(entry)
            if handle is None:
                raise ValidationFailure(f"{member} in {container.name} is not a regular file")
            return handle.read()
    raise ValidationFailure(f"unsupported archive format: {container}")


def root_member_bytes(root: Path, member_path: str) -> bytes:
    member = safe_member_path(member_path)
    target = (root / Path(*member.parts)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValidationFailure(f"member escapes supplied root: {member_path}") from exc
    try:
        return target.read_bytes()
    except OSError as exc:
        raise ValidationFailure(f"cannot read {member_path} under {root.name}: {exc}") from exc


def uncompressed_bytes(filename: str, stored: bytes) -> bytes:
    if filename.lower().endswith(".gz"):
        try:
            return gzip.decompress(stored)
        except OSError as exc:
            raise ValidationFailure(f"{filename} has .gz suffix but is not valid gzip data") from exc
    return stored


def match_container(expected: dict[str, Any], supplied: list[Path]) -> Path:
    missing = [str(path) for path in supplied if not path.exists()]
    if missing:
        raise ValidationFailure("supplied onlist containers do not exist: " + ", ".join(missing))
    if expected["kind"] == "archive" and not expected.get("sha256"):
        raise ValidationFailure(f"archive container {expected['filename']} requires SHA-256")
    if expected["kind"] == "directory" and expected.get("sha256"):
        raise ValidationFailure(f"directory container {expected['filename']} cannot claim an archive SHA-256")
    name_matches = [path for path in supplied if path.name == expected["filename"]]
    candidates = name_matches or supplied
    if expected["kind"] == "archive":
        matches = [path for path in candidates if path.is_file() and file_sha256(path) == expected["sha256"]]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise ValidationFailure(f"no supplied archive matches container SHA-256 for {expected['filename']}")
        raise ValidationFailure(f"multiple supplied archives match {expected['filename']}")
    root_matches = [path for path in name_matches if path.is_dir()]
    if len(root_matches) == 1:
        return root_matches[0]
    if not root_matches:
        raise ValidationFailure(f"no supplied decompressed root matches {expected['filename']}")
    raise ValidationFailure(f"multiple supplied roots could match {expected['filename']}")


def fetch_remote_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; seqspec-llm-authoring/1.1; "
                "+https://github.com/tfallon-ionis/tim-fallon-phd-skills)"
            )
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except OSError as exc:
        raise ValidationFailure(f"cannot fetch authoritative onlist {url}: {exc}") from exc


def resolve_onlists(
    sidecar: dict[str, Any],
    supplied: list[Path],
    native_onlists: dict[str, Any],
    local_root: Path,
) -> dict[str, bytes]:
    resolved: dict[str, bytes] = {}
    for record in sidecar["onlists"]:
        availability = record["availability"]
        if availability == "access_controlled_unavailable":
            if sidecar["status"] == "complete":
                raise ValidationFailure(f"onlist {record['file_id']} is unavailable in a complete artifact")
            continue
        native = native_onlists.get(record["file_id"])
        if native is None:
            raise ValidationFailure(f"sidecar onlist {record['file_id']} is absent from seqspec")
        if not record.get("content_digest") or not record.get("stored_artifact_digest"):
            raise ValidationFailure(f"onlist {record['file_id']} requires content and stored-artifact SHA-256 digests")
        if availability == "authoritative_public":
            if native.urltype not in ("http", "https", "ftp"):
                raise ValidationFailure(f"public onlist {record['file_id']} requires a direct http/https/ftp URL")
            stored = fetch_remote_bytes(native.url)
        elif availability == "documentary_transcription":
            if native.urltype != "local" or native.url != record["filename"]:
                raise ValidationFailure(
                    f"documentary transcription {record['file_id']} must use its local basename in seqspec"
                )
            try:
                stored = (local_root / record["filename"]).read_bytes()
            except OSError as exc:
                raise ValidationFailure(
                    f"cannot read documentary transcription {record['filename']} beside seqspec: {exc}"
                ) from exc
        else:
            container = match_container(record["container"], supplied)
            if container.is_dir():
                stored = root_member_bytes(container, record["container"]["member_path"])
            else:
                stored = archive_member_bytes(container, record["container"]["member_path"])
        content = uncompressed_bytes(record["filename"], stored)
        expected_content = record.get("content_digest", {}).get("value")
        if expected_content and hash_bytes(content) != expected_content:
            raise ValidationFailure(f"uncompressed SHA-256 mismatch for {record['file_id']}")
        expected_stored = record.get("stored_artifact_digest", {}).get("value")
        if expected_stored and hash_bytes(stored) != expected_stored:
            raise ValidationFailure(f"stored-artifact SHA-256 mismatch for {record['file_id']}")
        if hashlib.md5(content).hexdigest() != native.md5:
            raise ValidationFailure(f"native seqspec MD5 mismatch for {record['file_id']}")
        resolved[record["file_id"]] = stored
    return resolved


def load_spec(path: Path) -> Any:
    try:
        from seqspec.utils import load_spec as seqspec_load_spec

        return seqspec_load_spec(str(path))
    except Exception as exc:
        raise ValidationFailure(f"seqspec could not load {path}: {exc}") from exc


def walk_regions(regions: Iterable[Any]) -> Iterable[Any]:
    for region in regions:
        yield region
        yield from walk_regions(getattr(region, "regions", []) or [])


def values_from_kit(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, (list, tuple)):
        result: set[str] = set()
        for item in value:
            result.update(values_from_kit(item))
        return result
    if hasattr(value, "model_dump"):
        data = value.model_dump()
        return {str(data[key]) for key in ("kit_id", "name") if data.get(key)}
    return {str(value)}


def validate_seqspec_crosslinks(
    spec: Any,
    sidecar: dict[str, Any],
    installed_version: str,
    requested_projections: dict[str, tuple[int, int]],
) -> None:
    if version_tuple(str(spec.seqspec_version)) != version_tuple(installed_version):
        raise ValidationFailure(
            "seqspec_version must track the installed seqspec version: "
            f"file={spec.seqspec_version}, installed={installed_version}"
        )
    if spec.assay_id != sidecar["profile"]["seqspec_assay_id"]:
        raise ValidationFailure("profile.seqspec_assay_id does not match native Seqspec assay_id")

    for field, expected in (
        ("library_kit", sidecar["library_format"]["representative_kit"]["seqspec_value"]),
        ("sequence_kit", sidecar["sequencing"]["sequence_kit"]["seqspec_value"]),
    ):
        actual_values = values_from_kit(getattr(spec, field, None))
        if expected not in actual_values:
            raise ValidationFailure(
                f"{field} sidecar seqspec_value {expected!r} not present in seqspec values {sorted(actual_values)}"
            )

    protocols = values_from_kit(getattr(spec, "sequence_protocol", None))
    if not any("illumina" in value.lower() for value in protocols):
        raise ValidationFailure("seqspec sequence_protocol must identify Illumina for V1")

    reads = {read.read_id: read for read in spec.sequence_spec}
    sidecar_read_ids = {record["read_id"] for record in sidecar["sequencing"]["reads"]}
    if set(reads) != sidecar_read_ids:
        raise ValidationFailure(
            f"read_id mismatch between seqspec and sidecar: seqspec={sorted(reads)}, sidecar={sorted(sidecar_read_ids)}"
        )
    for record in sidecar["sequencing"]["reads"]:
        read = reads.get(record["read_id"])
        if read is None:
            raise ValidationFailure(f"sidecar read {record['read_id']} not found in seqspec")
        if read.min_len != record["cycles"] or read.max_len != record["cycles"]:
            raise ValidationFailure(f"seqspec {record['read_id']} length does not equal sidecar cycles")
    if sidecar["sequencing"]["index_read_configuration"] == "unknown" and ({"I1", "I2"} & reads.keys()):
        raise ValidationFailure("index_read_configuration is unknown but seqspec contains I1/I2 reads")

    regions = list(walk_regions(spec.library_spec))
    region_ids = {region.region_id for region in regions}
    onlist_regions = {region.onlist.file_id: region for region in regions if getattr(region, "onlist", None)}
    sidecar_onlists = {record["file_id"]: record for record in sidecar["onlists"]}
    if set(onlist_regions) != set(sidecar_onlists):
        raise ValidationFailure(
            "onlist file_id mismatch between seqspec and sidecar: "
            f"seqspec={sorted(onlist_regions)}, sidecar={sorted(sidecar_onlists)}"
        )
    for file_id, region in onlist_regions.items():
        record = sidecar_onlists[file_id]
        if Path(record["filename"]).name != record["filename"]:
            raise ValidationFailure(f"onlist {file_id} filename must be a basename")
        if region.onlist.filename != record["filename"]:
            raise ValidationFailure(f"onlist filename mismatch for {file_id}")
        if region.onlist.urltype == "local" and region.onlist.url != record["filename"]:
            raise ValidationFailure(f"onlist {file_id} local URL must be exactly its basename; paths are not allowed")
        if file_id in requested_projections:
            if not hasattr(region.onlist, "sequence_column_index") or not hasattr(region.onlist, "skip_rows"):
                raise ValidationFailure(
                    "installed seqspec lacks tabular-onlist projection support; "
                    "require sequence_column_index and skip_rows"
                )
            actual = (
                region.onlist.sequence_column_index,
                region.onlist.skip_rows,
            )
            if actual != requested_projections[file_id]:
                raise ValidationFailure(f"installed seqspec did not preserve projection fields for {file_id}")

    semantics = sidecar["barcode_semantics"]
    semantic_regions = {record["region_id"]: record for record in semantics["regions"]}
    unknown_regions = sorted(set(semantic_regions) - region_ids)
    if unknown_regions:
        raise ValidationFailure("barcode semantics reference unknown region_id: " + ", ".join(unknown_regions))
    for scheme in semantics["index_schemes"]:
        unknown_members = sorted(set(scheme["members"]) - set(semantic_regions))
        if unknown_members:
            raise ValidationFailure(
                f"index scheme {scheme['scheme_id']} has unknown members: {', '.join(unknown_members)}"
            )
        if scheme["type"] == "unique_dual_index":
            if not scheme.get("allowed_pairs") or scheme.get("pair_sequence_basis") != "seqspec_region":
                raise ValidationFailure(
                    f"unique dual-index scheme {scheme['scheme_id']} requires allowed_pairs in seqspec_region basis"
                )
        elif scheme.get("allowed_pairs"):
            raise ValidationFailure(f"allowed_pairs is only valid for a unique_dual_index scheme")

    try:
        from seqspec.seqspec_index import get_coordinate_by_read_id

        for region_id, record in semantic_regions.items():
            observed = record["observed_in"]
            if observed not in reads:
                raise ValidationFailure(
                    f"barcode region {region_id} says observed_in {observed}, but that read is absent"
                )
            read = reads[observed]
            coordinate = get_coordinate_by_read_id(spec, read.modality, read.read_id)
            projected_ids = {part.region_id for part in coordinate.rcv}
            if region_id not in projected_ids:
                raise ValidationFailure(f"barcode region {region_id} is not projected into {observed}")
    except ImportError as exc:
        raise ValidationFailure("installed seqspec lacks read-projection support") from exc


def validate_resolved_onlist_contents(spec: Any, resolved: dict[str, bytes]) -> dict[str, list[str]]:
    """Exercise seqspec's reader and verify projected sequence lengths."""
    from seqspec.utils import yield_onlist_contents

    onlist_regions = {
        region.onlist.file_id: region for region in walk_regions(spec.library_spec) if getattr(region, "onlist", None)
    }
    projected: dict[str, list[str]] = {}
    for file_id, stored in resolved.items():
        region = onlist_regions[file_id]
        onlist = region.onlist
        content = uncompressed_bytes(onlist.filename, stored)
        try:
            stream = io.StringIO(content.decode("utf-8"))
            if hasattr(onlist, "sequence_column_index") and hasattr(onlist, "skip_rows"):
                sequences = list(
                    yield_onlist_contents(
                        stream,
                        onlist.sequence_column_index,
                        onlist.skip_rows,
                    )
                )
            else:
                sequences = list(yield_onlist_contents(stream))
        except (TypeError, UnicodeDecodeError, ValueError) as exc:
            raise ValidationFailure(f"cannot project onlist {file_id}: {exc}") from exc
        if not sequences:
            raise ValidationFailure(f"onlist {file_id} projects to no sequences")
        invalid_lengths = sorted(
            {len(sequence) for sequence in sequences} - set(range(region.min_len, region.max_len + 1))
        )
        if invalid_lengths:
            raise ValidationFailure(
                f"onlist {file_id} projected sequence lengths {invalid_lengths} "
                f"fall outside region bounds {region.min_len}-{region.max_len}"
            )
        projected[file_id] = sequences
    return projected


def validate_allowed_index_pairs(spec: Any, sidecar: dict[str, Any], projected: dict[str, list[str]]) -> None:
    regions = {region.region_id: region for region in walk_regions(spec.library_spec)}
    semantics = sidecar["barcode_semantics"]
    semantic_regions = {record["region_id"]: record for record in semantics["regions"]}
    for scheme in semantics["index_schemes"]:
        pairs = scheme.get("allowed_pairs")
        if not pairs:
            continue
        role_to_region = {
            semantic_regions[region_id].get("index_role"): region_id
            for region_id in scheme["members"]
            if region_id in semantic_regions
        }
        if set(role_to_region) != {"i7", "i5"}:
            raise ValidationFailure(f"unique dual-index scheme {scheme['scheme_id']} must have one i7 and one i5 member")
        allowed: dict[str, set[str]] = {}
        for role, region_id in role_to_region.items():
            region = regions[region_id]
            if not getattr(region, "onlist", None):
                raise ValidationFailure(f"unique dual-index member {region_id} requires an onlist")
            allowed[role] = set(projected[region.onlist.file_id])
        pair_ids = [pair["pair_id"] for pair in pairs]
        if len(pair_ids) != len(set(pair_ids)):
            raise ValidationFailure(f"unique dual-index scheme {scheme['scheme_id']} has duplicate pair_id values")
        for pair in pairs:
            for role in ("i7", "i5"):
                if pair[role] not in allowed[role]:
                    raise ValidationFailure(
                        f"pair {pair['pair_id']} {role} value is absent from region {role_to_region[role]} onlist"
                    )


def stage_and_check(seqspec_path: Path, spec: Any, resolved: dict[str, bytes]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="seqspec-validate-") as directory:
        root = Path(directory)
        staged_spec = root / "seqspec.yaml"
        onlists = {
            region.onlist.file_id: region.onlist
            for region in walk_regions(spec.library_spec)
            if getattr(region, "onlist", None)
        }
        staged_value = load_yaml(seqspec_path)

        def localize_resolved_onlists(node: Any) -> None:
            if isinstance(node, dict):
                native = node.get("onlist")
                if isinstance(native, dict) and native.get("file_id") in resolved:
                    file_id = native["file_id"]
                    filename = Path(onlists[file_id].filename).name
                    if not filename:
                        raise ValidationFailure(f"onlist {file_id} has no usable filename")
                    native["filename"] = filename
                    native["url"] = filename
                    native["urltype"] = "local"
                for child in node.values():
                    localize_resolved_onlists(child)
            elif isinstance(node, list):
                for child in node:
                    localize_resolved_onlists(child)

        localize_resolved_onlists(staged_value)
        staged_spec.write_text(yaml.safe_dump(staged_value, sort_keys=False), encoding="utf-8")
        for file_id, stored in resolved.items():
            target = root / Path(onlists[file_id].filename).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(stored)
        result = subprocess.run(
            ["seqspec", "check", str(staged_spec)],
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
    detail = (result.stdout + "\n" + result.stderr).strip()
    reported_errors = any(line.lstrip().startswith("[error ") for line in detail.splitlines())
    if result.returncode != 0 or reported_errors:
        raise ValidationFailure(f"vanilla seqspec check failed:\n{detail}")
    return result


def write_attestation(path: Path, sidecar: dict[str, Any], seqspec_version: str) -> None:
    from datetime import datetime, timezone

    updated = copy.deepcopy(sidecar)
    validation = updated["validation"]
    validation["status"] = "complete"
    validation["validated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    validation["seqspec_cli_version"] = seqspec_version
    validation["sidecar_schema_version"] = updated["sources_schema_version"]
    rendered = yaml.safe_dump(updated, sort_keys=False, allow_unicode=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    args = parse_args()
    try:
        seqspec_version = installed_seqspec_version()
        sidecar = load_yaml(args.sidecar)
        validate_json_schema(sidecar)
        validate_lifecycle(sidecar, args.seqspec, args.sidecar)
        validate_references(sidecar)
        if sidecar["status"] == "draft":
            print("DRAFT — NOT VALIDATED")
            for gap in sidecar["validation"]["blocking_gaps"]:
                print(f"- {gap['code']}: {gap['message']}")
            return 2
        spec = load_spec(args.seqspec)
        requested_projections = requested_onlist_projections(args.seqspec)
        validate_seqspec_crosslinks(
            spec,
            sidecar,
            seqspec_version,
            requested_projections,
        )
        native_onlists = {
            region.onlist.file_id: region.onlist
            for region in walk_regions(spec.library_spec)
            if getattr(region, "onlist", None)
        }
        resolved = resolve_onlists(sidecar, args.onlist_container, native_onlists, args.seqspec.parent)
        projected = validate_resolved_onlist_contents(spec, resolved)
        validate_allowed_index_pairs(spec, sidecar, projected)
        result = stage_and_check(args.seqspec, spec, resolved)
        if result.stdout.strip():
            print(result.stdout.strip())
        if not args.no_write_attestation:
            if sidecar["validation"]["user_confirmation"]["status"] != "confirmed":
                raise ValidationFailure(
                    "final attestation requires explicit user_confirmation; use "
                    "--no-write-attestation for preflight validation"
                )
            write_attestation(args.sidecar, sidecar, seqspec_version)
        print(f"VALID: seqspec {seqspec_version}; sidecar {sidecar['sources_schema_version']}")
        return 0
    except (ValidationFailure, subprocess.TimeoutExpired) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
