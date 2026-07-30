from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPARATOR = ROOT / "scripts" / "compare_profiles.py"


class CompareProfilesTests(unittest.TestCase):
    def write_bundle(
        self,
        directory: Path,
        *,
        assay_id: str,
        platform: str = "NextSeq 2000",
        onlist: bytes = b"AAAA\n",
    ) -> None:
        directory.mkdir()
        seqspec = {
            "assay_id": assay_id,
            "sequence_protocol": f"Illumina {platform}",
            "sequence_spec": [{"read_id": "R1", "min_len": 4, "max_len": 4}],
        }
        sidecar = {
            "profile": {
                "seqspec_assay_id": assay_id,
                "relations": [],
            },
            "sequencing": {
                "platform": platform,
                "reads": [{"read_id": "R1", "cycles": 4}],
            },
            "validation": {"validated_at": "2026-07-15T00:00:00Z"},
        }
        (directory / "seqspec.yaml").write_text(yaml.safe_dump(seqspec, sort_keys=False))
        (directory / "provenance.sidecar.yaml").write_text(yaml.safe_dump(sidecar, sort_keys=False))
        (directory / "barcodes.txt").write_bytes(onlist)
        (directory / "seqspec.html").write_text(f"<h1>{assay_id}</h1>\n")

    def run_comparator(
        self,
        parent: Path,
        child: Path,
        *allowed: str,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(COMPARATOR),
            "--parent",
            str(parent),
            "--child",
            str(child),
        ]
        for pattern in allowed:
            command.extend(["--allow", pattern])
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def test_allows_confirmed_semantic_and_generated_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            parent = root / "parent"
            child = root / "child"
            self.write_bundle(parent, assay_id="parent")
            self.write_bundle(child, assay_id="child", platform="NovaSeq X Plus")

            result = self.run_comparator(
                parent,
                child,
                "seqspec.assay_id",
                "seqspec.sequence_protocol",
                "sidecar.profile.seqspec_assay_id",
                "sidecar.sequencing.platform",
                "files.seqspec.html",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ALLOWED sidecar.sequencing.platform", result.stdout)
            self.assertNotIn("UNEXPECTED", result.stdout)

    def test_rejects_change_outside_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            parent = root / "parent"
            child = root / "child"
            self.write_bundle(parent, assay_id="parent")
            self.write_bundle(child, assay_id="parent", platform="NovaSeq X Plus")

            result = self.run_comparator(parent, child)

            self.assertEqual(result.returncode, 1)
            self.assertIn("UNEXPECTED seqspec.sequence_protocol", result.stdout)
            self.assertIn("UNEXPECTED sidecar.sequencing.platform", result.stdout)

    def test_rejects_changed_local_payload_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            parent = root / "parent"
            child = root / "child"
            self.write_bundle(parent, assay_id="same")
            self.write_bundle(child, assay_id="same", onlist=b"CCCC\n")

            result = self.run_comparator(parent, child)

            self.assertEqual(result.returncode, 1)
            self.assertIn("UNEXPECTED files.barcodes.txt", result.stdout)


if __name__ == "__main__":
    unittest.main()
