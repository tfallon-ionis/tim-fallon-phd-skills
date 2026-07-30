from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from scripts.offline_bundle import (
    BundleFailure,
    package_offline_bundle,
    verify_offline_bundle,
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def native_onlist(filename: str, content: bytes, *, url: str, urltype: str) -> dict:
    return {
        "file_id": filename,
        "filename": filename,
        "filetype": "txt",
        "filesize": len(content),
        "url": url,
        "urltype": urltype,
        "md5": hashlib.md5(content).hexdigest(),
        "sequence_column_index": 1,
        "skip_rows": 1,
    }


def fixture_pair(root: Path) -> tuple[Path, bytes, bytes]:
    profile = root / "example-illumina-r1-4"
    profile.mkdir()
    public = b"well barcode\nA01 AAAA\n"
    local = b"well barcode\nB01 CCCC\n"
    (profile / "local.txt").write_bytes(local)

    spec = {
        "seqspec_version": "0.4.0",
        "assay_id": profile.name,
        "library_spec": [
            {
                "region_id": "rna",
                "onlist": None,
                "regions": [
                    {
                        "region_id": "public",
                        "onlist": native_onlist(
                            "public.txt",
                            public,
                            url="https://example.org/public.txt",
                            urltype="https",
                        ),
                        "regions": [],
                    },
                    {
                        "region_id": "local",
                        "onlist": native_onlist(
                            "local.txt",
                            local,
                            url="local.txt",
                            urltype="local",
                        ),
                        "regions": [],
                    },
                ],
            }
        ],
    }
    sidecar = {
        "sources_schema_version": "1.1.0",
        "status": "complete",
        "profile": {"seqspec_assay_id": profile.name},
        "onlists": [
            {
                "file_id": "public.txt",
                "filename": "public.txt",
                "availability": "authoritative_public",
                "content_digest": {"algorithm": "sha256", "value": sha256(public)},
                "stored_artifact_digest": {"algorithm": "sha256", "value": sha256(public)},
            },
            {
                "file_id": "local.txt",
                "filename": "local.txt",
                "availability": "documentary_transcription",
                "content_digest": {"algorithm": "sha256", "value": sha256(local)},
                "stored_artifact_digest": {"algorithm": "sha256", "value": sha256(local)},
            },
        ],
        "validation": {
            "status": "complete",
            "validated_at": "2026-07-30T00:00:00Z",
            "user_confirmation": {
                "status": "confirmed",
                "confirmed_at": "2026-07-30T00:00:00Z",
            },
        },
    }
    (profile / "seqspec.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))
    (profile / "provenance.sidecar.yaml").write_text(yaml.safe_dump(sidecar, sort_keys=False))
    return profile, public, local


class OfflineBundleTests(unittest.TestCase):
    def test_packages_public_and_local_onlists_without_changing_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, public, local = fixture_pair(root)
            output = root / "output"

            with mock.patch(
                "scripts.offline_bundle.fetch_remote_bytes",
                return_value=public,
            ), mock.patch("scripts.offline_bundle.run_seqspec_check"):
                bundle = package_offline_bundle(source, output)

            self.assertEqual(bundle, (output / "offline-bundles" / source.name).resolve())
            self.assertEqual((bundle / "onlists" / "public.txt").read_bytes(), public)
            self.assertEqual((bundle / "onlists" / "local.txt").read_bytes(), local)
            self.assertEqual(
                (bundle / "provenance.sidecar.yaml").read_bytes(),
                (source / "provenance.sidecar.yaml").read_bytes(),
            )

            source_spec = yaml.safe_load((source / "seqspec.yaml").read_text())
            bundled_spec = yaml.safe_load((bundle / "seqspec.yaml").read_text())
            source_onlists = collect_onlists(source_spec)
            bundled_onlists = collect_onlists(bundled_spec)
            for file_id in source_onlists:
                expected = copy.deepcopy(source_onlists[file_id])
                expected["url"] = f"onlists/{expected['filename']}"
                expected["urltype"] = "local"
                self.assertEqual(bundled_onlists[file_id], expected)

            self.assertEqual(
                {
                    path.relative_to(bundle).as_posix()
                    for path in bundle.rglob("*")
                    if path.is_file()
                },
                {
                    "seqspec.yaml",
                    "provenance.sidecar.yaml",
                    "onlists/public.txt",
                    "onlists/local.txt",
                },
            )

    def test_verifier_is_offline_and_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, public, _ = fixture_pair(root)
            with mock.patch(
                "scripts.offline_bundle.fetch_remote_bytes",
                return_value=public,
            ), mock.patch("scripts.offline_bundle.run_seqspec_check"):
                bundle = package_offline_bundle(source, root / "output")

            with mock.patch("urllib.request.urlopen") as urlopen, mock.patch(
                "scripts.offline_bundle.run_seqspec_check"
            ):
                verify_offline_bundle(source, bundle)
            urlopen.assert_not_called()

            (bundle / "onlists" / "public.txt").write_bytes(b"tampered\n")
            with self.assertRaisesRegex(BundleFailure, "mismatch"):
                verify_offline_bundle(source, bundle, run_check=False)

    def test_rejects_drafts_unsafe_paths_collisions_and_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, public, _ = fixture_pair(root)
            sidecar_path = source / "provenance.sidecar.yaml"
            sidecar = yaml.safe_load(sidecar_path.read_text())
            sidecar["status"] = "draft"
            sidecar_path.write_text(yaml.safe_dump(sidecar, sort_keys=False))
            with self.assertRaisesRegex(BundleFailure, "attested complete"):
                package_offline_bundle(source, root / "output", run_check=False)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, public, _ = fixture_pair(root)
            spec_path = source / "seqspec.yaml"
            spec = yaml.safe_load(spec_path.read_text())
            collect_onlists(spec)["local.txt"]["filename"] = "../local.txt"
            spec_path.write_text(yaml.safe_dump(spec, sort_keys=False))
            with self.assertRaisesRegex(BundleFailure, "safe basename"):
                package_offline_bundle(source, root / "output", run_check=False)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, public, _ = fixture_pair(root)
            spec_path = source / "seqspec.yaml"
            spec = yaml.safe_load(spec_path.read_text())
            collect_onlists(spec)["local.txt"]["filename"] = "public.txt"
            spec_path.write_text(yaml.safe_dump(spec, sort_keys=False))
            with self.assertRaisesRegex(BundleFailure, "filename collision"):
                package_offline_bundle(source, root / "output", run_check=False)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, public, _ = fixture_pair(root)
            output = root / "output"
            with mock.patch(
                "scripts.offline_bundle.fetch_remote_bytes",
                return_value=public,
            ), mock.patch("scripts.offline_bundle.run_seqspec_check"):
                package_offline_bundle(source, output)
            with self.assertRaisesRegex(BundleFailure, "already exists"):
                package_offline_bundle(source, output, run_check=False)

    def test_rejects_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, _, _ = fixture_pair(root)
            with mock.patch(
                "scripts.offline_bundle.fetch_remote_bytes",
                return_value=b"well barcode\nA01 TTTT\n",
            ):
                with self.assertRaisesRegex(BundleFailure, "digest|MD5|SHA-256"):
                    package_offline_bundle(source, root / "output", run_check=False)


def collect_onlists(value: object) -> dict[str, dict]:
    found: dict[str, dict] = {}

    def visit(node: object) -> None:
        if isinstance(node, dict):
            onlist = node.get("onlist")
            if isinstance(onlist, dict):
                found[onlist["file_id"]] = onlist
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return found


if __name__ == "__main__":
    unittest.main()
