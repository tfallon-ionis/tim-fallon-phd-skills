from __future__ import annotations

import gzip
import hashlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml

from scripts.validate import (
    ValidationFailure,
    fetch_remote_bytes,
    load_spec,
    stage_and_check,
    validate_allowed_index_pairs,
    validate_lifecycle,
)

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate.py"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_seqspec(*, onlist: dict | None = None) -> dict:
    barcode = {
        "region_id": "barcode",
        "region_type": "barcode",
        "name": "demultiplexing barcode",
        "sequence_type": "onlist" if onlist else "random",
        "sequence": "NNNN" if onlist else "XXXX",
        "min_len": 4,
        "max_len": 4,
        "onlist": onlist,
        "regions": [],
    }
    return {
        "seqspec_version": "0.4.0",
        "assay_id": "example-illumina-r1-4",
        "name": "Example",
        "doi": "https://doi.org/10.0000/example",
        "date": "15 July 2026",
        "description": "Validator fixture",
        "modalities": ["rna"],
        "lib_struct": "",
        "library_protocol": "Example protocol",
        "library_kit": "Example Library Kit",
        "sequence_protocol": "Illumina",
        "sequence_kit": "Example Sequence Kit",
        "sequence_spec": [
            {
                "read_id": "R1",
                "name": "Read 1",
                "modality": "rna",
                "primer_id": "primer",
                "min_len": 4,
                "max_len": 4,
                "strand": "pos",
                "files": [],
            }
        ],
        "library_spec": [
            {
                "region_id": "rna",
                "region_type": "rna",
                "name": "RNA modality",
                "sequence_type": "joined",
                "sequence": "ANNNN" if onlist else "AXXXX",
                "min_len": 5,
                "max_len": 5,
                "onlist": None,
                "regions": [
                    {
                        "region_id": "primer",
                        "region_type": "custom_primer",
                        "name": "Read 1 primer",
                        "sequence_type": "fixed",
                        "sequence": "A",
                        "min_len": 1,
                        "max_len": 1,
                        "onlist": None,
                        "regions": [],
                    },
                    barcode,
                ],
            }
        ],
    }


def base_sidecar() -> dict:
    source_id = "example_vendor_2026_kit_guide"
    claims = [
        "library_format.representative_kit.product_name",
        "library_format.representative_kit.manufacturer_id",
        "library_format.representative_kit.catalog_number",
        "sequencing.sequence_kit.product_name",
        "sequencing.sequence_kit.manufacturer_id",
        "sequencing.sequence_kit.catalog_number",
    ]
    return {
        "sources_schema_version": "1.1.0",
        "status": "complete",
        "profile": {
            "seqspec_assay_id": "example-illumina-r1-4",
            "internal_colloquial_names": ["example"],
            "family_id": "example",
            "version": None,
            "previous_version": None,
            "variant_of": "example",
        },
        "library_format": {
            "technical_name": "Example",
            "version": None,
            "family_id": "example",
            "representative_kit": {
                "seqspec_value": "Example Library Kit",
                "product_name": "Example Library Kit",
                "manufacturer_id": "example_vendor",
                "catalog_number": "LIB-1",
                "version": None,
                "source_ids": [source_id],
            },
        },
        "sequencing": {
            "platform": "Illumina",
            "index_read_configuration": "unknown",
            "reads": [{"read_id": "R1", "cycles": 4, "basis": "user_supplied"}],
            "sequence_kit": {
                "seqspec_value": "Example Sequence Kit",
                "product_name": "Example Sequence Kit",
                "manufacturer_id": "example_vendor",
                "catalog_number": "SEQ-1",
                "catalog_number_status": "documented",
                "version": None,
                "source_ids": [source_id],
            },
        },
        "vendors": [
            {
                "vendor_id": "example_vendor",
                "name": "Example Vendor",
                "wikidata_uri": "https://www.wikidata.org/entity/Q2068984",
                "verified_at": "2026-07-15",
            }
        ],
        "sources": [
            {
                "source_id": source_id,
                "authority": "authoritative",
                "title": "Example kit guide",
                "url": "https://example.org/kit-guide.pdf",
                "accessed": "2026-07-15",
                "year_basis": "accessed",
                "zotero_ieee": "[1] “Example kit guide.” Accessed: Jul. 15, 2026. [Online]. Available: https://example.org/kit-guide.pdf",
            }
        ],
        "artifacts": [],
        "onlists": [],
        "claims": [
            {
                "claim_id": f"claim-{index}",
                "target": target,
                "basis": "documentary",
                "source_ids": [source_id],
            }
            for index, target in enumerate(claims, 1)
        ],
        "barcode_semantics": {
            "vocabulary_version": "1.1.0",
            "regions": [
                {
                    "region_id": "barcode",
                    "semantic_type": "demultiplexing_barcode",
                    "observed_in": "R1",
                    "groups_reads_by": "library_preparation_input",
                }
            ],
            "index_schemes": [],
        },
        "conflicts": [],
        "validation": {
            "status": "draft",
            "validated_at": None,
            "seqspec_cli_version": None,
            "sidecar_schema_version": "1.1.0",
            "accepted_warnings": [],
            "blocking_gaps": [],
            "user_confirmation": {
                "status": "confirmed",
                "confirmed_at": "2026-07-15T00:00:00Z",
            },
        },
    }


class ValidateTests(unittest.TestCase):
    def run_validator(self, directory: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--seqspec",
                str(directory / "seqspec.yaml"),
                "--sidecar",
                str(directory / "provenance.sidecar.yaml"),
                *extra,
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )

    def write_pair(self, directory: Path, spec: dict, sidecar: dict) -> None:
        (directory / "seqspec.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))
        (directory / "provenance.sidecar.yaml").write_text(yaml.safe_dump(sidecar, sort_keys=False))

    def test_public_fetch_uses_identified_http_client(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"AAAA\n"
        with mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
            self.assertEqual(fetch_remote_bytes("https://example.org/onlist.txt"), b"AAAA\n")

        request = urlopen.call_args.args[0]
        self.assertIn("seqspec-llm-authoring", request.get_header("User-agent"))

    def test_complete_lifecycle_requires_canonical_provenance_filename(self) -> None:
        sidecar = base_sidecar()

        validate_lifecycle(
            sidecar,
            Path("seqspec.yaml"),
            Path("provenance.sidecar.yaml"),
        )

        with self.assertRaisesRegex(ValidationFailure, "provenance.sidecar.yaml"):
            validate_lifecycle(
                sidecar,
                Path("seqspec.yaml"),
                Path("seqspec.sidecar.yaml"),
            )

    def test_complete_pair_validates_and_writes_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write_pair(directory, base_seqspec(), base_sidecar())
            result = self.run_validator(directory)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            updated = yaml.safe_load((directory / "provenance.sidecar.yaml").read_text())
            self.assertEqual(updated["validation"]["status"], "complete")
            self.assertIsNotNone(updated["validation"]["validated_at"])

    def test_preflight_allows_pending_confirmation_without_attesting(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            sidecar = base_sidecar()
            sidecar["validation"]["user_confirmation"] = {
                "status": "pending",
                "confirmed_at": None,
            }
            self.write_pair(directory, base_seqspec(), sidecar)
            result = self.run_validator(directory, "--no-write-attestation")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            unchanged = yaml.safe_load((directory / "provenance.sidecar.yaml").read_text())
            self.assertIsNone(unchanged["validation"]["validated_at"])

    def test_sidecar_schema_version_1_0_0_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            sidecar = base_sidecar()
            sidecar["sources_schema_version"] = "1.0.0"
            sidecar["validation"]["sidecar_schema_version"] = "1.0.0"
            self.write_pair(directory, base_seqspec(), sidecar)

            result = self.run_validator(directory)

            self.assertEqual(result.returncode, 1)
            self.assertIn("sources_schema_version: '1.1.0' was expected", result.stderr)

    def test_barcode_vocabulary_version_1_0_0_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            sidecar = base_sidecar()
            sidecar["barcode_semantics"]["vocabulary_version"] = "1.0.0"
            self.write_pair(directory, base_seqspec(), sidecar)

            result = self.run_validator(directory)

            self.assertEqual(result.returncode, 1)
            self.assertIn("barcode_semantics.vocabulary_version: '1.1.0' was expected", result.stderr)

    def test_unqualified_sidecar_assay_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            sidecar = base_sidecar()
            value = sidecar["profile"].pop("seqspec_assay_id")
            sidecar["profile"]["assay_id"] = value
            self.write_pair(directory, base_seqspec(), sidecar)

            result = self.run_validator(directory)

            self.assertEqual(result.returncode, 1)
            self.assertIn("profile: 'seqspec_assay_id' is a required property", result.stderr)
            self.assertIn("profile: Additional properties are not allowed ('assay_id' was unexpected)", result.stderr)

    def test_seqspec_assay_id_must_match_native_field(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            sidecar = base_sidecar()
            sidecar["profile"]["seqspec_assay_id"] = "different-profile"
            self.write_pair(directory, base_seqspec(), sidecar)

            result = self.run_validator(directory)

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "profile.seqspec_assay_id does not match native Seqspec assay_id",
                result.stderr,
            )

    def test_sidecar_platform_accepts_exact_illumina_model(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            spec = base_seqspec()
            spec["sequence_protocol"] = "Illumina NovaSeq X Plus"
            sidecar = base_sidecar()
            sidecar["sequencing"]["platform"] = "NovaSeq X Plus"
            self.write_pair(directory, spec, sidecar)

            result = self.run_validator(directory)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_onlist_inside_zip_is_resolved_without_persistent_copy(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            content = b"AAAA\nCCCC\nGGGG\nTTTT\n"
            stored = gzip.compress(content, mtime=0)
            archive = directory / "cellranger-test.zip"
            member = "cellranger/barcodes/test.txt.gz"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr(member, stored)
            native_onlist = {
                "file_id": "test.txt.gz",
                "filename": "test.txt.gz",
                "filetype": "txt.gz",
                "filesize": len(stored),
                "url": "test.txt.gz",
                "urltype": "local",
                "md5": hashlib.md5(content).hexdigest(),
            }
            sidecar = base_sidecar()
            source_id = sidecar["sources"][0]["source_id"]
            sidecar["onlists"] = [
                {
                    "file_id": "test.txt.gz",
                    "filename": "test.txt.gz",
                    "availability": "supplied_container",
                    "source_ids": [source_id],
                    "content_digest": {"algorithm": "sha256", "value": sha256(content)},
                    "stored_artifact_digest": {"algorithm": "sha256", "value": sha256(stored)},
                    "container": {
                        "kind": "archive",
                        "filename": archive.name,
                        "sha256": sha256(archive.read_bytes()),
                        "member_path": member,
                    },
                }
            ]
            self.write_pair(directory, base_seqspec(onlist=native_onlist), sidecar)
            result = self.run_validator(directory, "--onlist-container", str(archive))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((directory / "test.txt.gz").exists())

    def test_tabular_onlist_projection_preserves_authoritative_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            content = b"well barcode\nA01 AAAA\nA02 CCCC\n"
            archive = directory / "vendor-test.zip"
            member = "barcodes/plate.tsv"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr(member, content)
            native_onlist = {
                "file_id": "plate.tsv",
                "filename": "plate.tsv",
                "filetype": "tsv",
                "filesize": len(content),
                "url": "plate.tsv",
                "urltype": "local",
                "md5": hashlib.md5(content).hexdigest(),
                "sequence_column_index": 1,
                "skip_rows": 1,
            }
            sidecar = base_sidecar()
            source_id = sidecar["sources"][0]["source_id"]
            sidecar["onlists"] = [
                {
                    "file_id": "plate.tsv",
                    "filename": "plate.tsv",
                    "availability": "supplied_container",
                    "source_ids": [source_id],
                    "content_digest": {
                        "algorithm": "sha256",
                        "value": sha256(content),
                    },
                    "stored_artifact_digest": {
                        "algorithm": "sha256",
                        "value": sha256(content),
                    },
                    "container": {
                        "kind": "archive",
                        "filename": archive.name,
                        "sha256": sha256(archive.read_bytes()),
                        "member_path": member,
                    },
                }
            ]
            self.write_pair(directory, base_seqspec(onlist=native_onlist), sidecar)

            result = self.run_validator(
                directory,
                "--onlist-container",
                str(archive),
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((directory / "plate.tsv").exists())

    def test_public_tabular_onlist_is_staged_for_native_check(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            content = b"well barcode\nA01 AAAA\nA02 CCCC\n"
            native_onlist = {
                "file_id": "plate.tsv",
                "filename": "plate.tsv",
                "filetype": "tsv",
                "filesize": len(content),
                "url": "http://127.0.0.1:9/unreachable/plate.tsv",
                "urltype": "http",
                "md5": hashlib.md5(content).hexdigest(),
                "sequence_column_index": 1,
                "skip_rows": 1,
            }
            spec_path = directory / "seqspec.yaml"
            spec_path.write_text(yaml.safe_dump(base_seqspec(onlist=native_onlist), sort_keys=False))
            spec = load_spec(spec_path)

            result = stage_and_check(spec_path, spec, {"plate.tsv": content})

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((directory / "plate.tsv").exists())

    def test_documentary_transcription_validates_as_emitted_local_onlist(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            content = b"AAAA\nCCCC\n"
            filename = "documented-indexes.txt"
            (directory / filename).write_bytes(content)
            native_onlist = {
                "file_id": filename,
                "filename": filename,
                "filetype": "txt",
                "filesize": len(content),
                "url": filename,
                "urltype": "local",
                "md5": hashlib.md5(content).hexdigest(),
            }
            sidecar = base_sidecar()
            source_id = sidecar["sources"][0]["source_id"]
            sidecar["onlists"] = [
                {
                    "file_id": filename,
                    "filename": filename,
                    "availability": "documentary_transcription",
                    "source_ids": [source_id],
                    "content_digest": {"algorithm": "sha256", "value": sha256(content)},
                    "stored_artifact_digest": {"algorithm": "sha256", "value": sha256(content)},
                    "derivation": {
                        "kind": "documentary_transcription",
                        "source_locator": "Page 12, index table, i7 column",
                        "operations": [
                            "Transcribe sequences in source row order.",
                            "Write uppercase sequences with LF and a terminal newline.",
                        ],
                        "verification": "manually_compared_to_source",
                    },
                }
            ]
            self.write_pair(directory, base_seqspec(onlist=native_onlist), sidecar)

            result = self.run_validator(directory)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((directory / filename).read_bytes(), content)

    def test_documentary_transcription_requires_derivation_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            content = b"AAAA\n"
            filename = "documented-indexes.txt"
            (directory / filename).write_bytes(content)
            native_onlist = {
                "file_id": filename,
                "filename": filename,
                "filetype": "txt",
                "filesize": len(content),
                "url": filename,
                "urltype": "local",
                "md5": hashlib.md5(content).hexdigest(),
            }
            sidecar = base_sidecar()
            source_id = sidecar["sources"][0]["source_id"]
            sidecar["onlists"] = [
                {
                    "file_id": filename,
                    "filename": filename,
                    "availability": "documentary_transcription",
                    "source_ids": [source_id],
                    "content_digest": {"algorithm": "sha256", "value": sha256(content)},
                    "stored_artifact_digest": {"algorithm": "sha256", "value": sha256(content)},
                }
            ]
            self.write_pair(directory, base_seqspec(onlist=native_onlist), sidecar)

            result = self.run_validator(directory)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires derivation metadata", result.stderr)

    def test_unique_dual_index_pairs_must_exist_in_marginal_onlists(self) -> None:
        i7 = SimpleNamespace(
            region_id="i7",
            regions=[],
            onlist=SimpleNamespace(file_id="i7.txt"),
        )
        i5 = SimpleNamespace(
            region_id="i5",
            regions=[],
            onlist=SimpleNamespace(file_id="i5.txt"),
        )
        spec = SimpleNamespace(library_spec=[SimpleNamespace(region_id="rna", regions=[i7, i5], onlist=None)])
        sidecar = {
            "barcode_semantics": {
                "vocabulary_version": "1.1.0",
                "regions": [
                    {"region_id": "i7", "index_role": "i7"},
                    {"region_id": "i5", "index_role": "i5"},
                ],
                "index_schemes": [
                    {
                        "scheme_id": "udi",
                        "type": "unique_dual_index",
                        "members": ["i7", "i5"],
                        "pair_sequence_basis": "seqspec_region",
                        "allowed_pairs": [{"pair_id": "UDI01", "i7": "AAAAAAAA", "i5": "CCCCCCCC"}],
                    }
                ],
            }
        }
        projected = {"i7.txt": ["AAAAAAAA"], "i5.txt": ["CCCCCCCC"]}

        validate_allowed_index_pairs(spec, sidecar, projected)
        sidecar["barcode_semantics"]["index_schemes"][0]["allowed_pairs"][0]["i5"] = "GGGGGGGG"

        with self.assertRaisesRegex(ValidationFailure, "absent from region i5 onlist"):
            validate_allowed_index_pairs(spec, sidecar, projected)

    def test_local_onlist_path_is_rejected_even_when_basename_matches(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            content = b"AAAA\n"
            stored = gzip.compress(content, mtime=0)
            archive = directory / "cellranger-test.zip"
            member = "barcodes/test.txt.gz"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr(member, stored)
            native_onlist = {
                "file_id": "test.txt.gz",
                "filename": "test.txt.gz",
                "filetype": "txt.gz",
                "filesize": len(stored),
                "url": "/private/tmp/test.txt.gz",
                "urltype": "local",
                "md5": hashlib.md5(content).hexdigest(),
            }
            sidecar = base_sidecar()
            source_id = sidecar["sources"][0]["source_id"]
            sidecar["onlists"] = [
                {
                    "file_id": "test.txt.gz",
                    "filename": "test.txt.gz",
                    "availability": "supplied_container",
                    "source_ids": [source_id],
                    "content_digest": {"algorithm": "sha256", "value": sha256(content)},
                    "stored_artifact_digest": {"algorithm": "sha256", "value": sha256(stored)},
                    "container": {
                        "kind": "archive",
                        "filename": archive.name,
                        "sha256": sha256(archive.read_bytes()),
                        "member_path": member,
                    },
                }
            ]
            self.write_pair(directory, base_seqspec(onlist=native_onlist), sidecar)
            result = self.run_validator(directory, "--onlist-container", str(archive))
            self.assertEqual(result.returncode, 1)
            self.assertIn("paths are not allowed", result.stderr)

    def test_missing_documentary_claim_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            sidecar = base_sidecar()
            sidecar["claims"] = sidecar["claims"][:-1]
            self.write_pair(directory, base_seqspec(), sidecar)
            result = self.run_validator(directory)
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing field-level documentary claims", result.stderr)

    def test_seqspec_reported_errors_fail_even_when_cli_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            spec = base_seqspec()
            spec["library_spec"][0]["sequence"] = "XXXXX"
            self.write_pair(directory, spec, base_sidecar())
            result = self.run_validator(directory)
            self.assertEqual(result.returncode, 1)
            self.assertIn("vanilla seqspec check failed", result.stderr)

    def test_draft_reports_blocking_gaps_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            sidecar = base_sidecar()
            sidecar["status"] = "draft"
            sidecar["validation"]["user_confirmation"] = {
                "status": "pending",
                "confirmed_at": None,
            }
            sidecar["validation"]["blocking_gaps"] = [
                {"code": "onlist_bytes_unavailable", "message": "Vendor archive is access controlled."}
            ]
            seqspec_path = directory / "seqspec.draft.yaml"
            sidecar_path = directory / "provenance.draft.sidecar.yaml"
            seqspec_path.write_text(yaml.safe_dump(base_seqspec(), sort_keys=False))
            sidecar_path.write_text(yaml.safe_dump(sidecar, sort_keys=False))
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--seqspec",
                    str(seqspec_path),
                    "--sidecar",
                    str(sidecar_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("DRAFT — NOT VALIDATED", result.stdout)


if __name__ == "__main__":
    unittest.main()
