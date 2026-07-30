#!/usr/bin/env python3
"""Compare parent and child seqspec bundles against an allowed change set."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

LIFECYCLE_FILES = {"seqspec.yaml", "provenance.sidecar.yaml"}
IDENTITY_KEYS = (
    "read_id",
    "region_id",
    "source_id",
    "claim_id",
    "file_id",
    "vendor_id",
    "scheme_id",
    "pair_id",
    "artifact_id",
    "conflict_id",
)


class ComparisonFailure(Exception):
    """Raised for invalid input or changes outside the allowlist."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", required=True, type=Path, help="Validated parent profile directory.")
    parser.add_argument("--child", required=True, type=Path, help="Candidate child profile directory.")
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Allowed semantic path; repeat as needed. Shell-style wildcards are supported.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the comparison report as JSON.")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ComparisonFailure(f"cannot read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ComparisonFailure(f"expected a YAML mapping in {path}")
    return value


def list_key(value: list[Any]) -> str | None:
    if not value or not all(isinstance(item, dict) for item in value):
        return None
    for key in IDENTITY_KEYS:
        if all(key in item for item in value):
            return key
    if all("type" in item and "target" in item for item in value):
        return "__relation__"
    return None


def flatten(value: Any, prefix: str, result: dict[str, Any]) -> None:
    if isinstance(value, dict):
        if not value:
            result[prefix] = {}
            return
        for key in sorted(value):
            flatten(value[key], f"{prefix}.{key}" if prefix else str(key), result)
        return
    if isinstance(value, list):
        if not value:
            result[prefix] = []
            return
        key = list_key(value)
        if key:
            for index, item in enumerate(value):
                identity = (
                    f"{item['type']}->{item['target']}"
                    if key == "__relation__"
                    else str(item[key])
                )
                flatten(item, f"{prefix}[{identity}]", result)
            return
        for index, item in enumerate(value):
            flatten(item, f"{prefix}[{index}]", result)
        return
    result[prefix] = value


def file_digests(directory: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        paths = sorted(path for path in directory.rglob("*") if path.is_file())
    except OSError as exc:
        raise ComparisonFailure(f"cannot inspect bundle {directory}: {exc}") from exc
    for path in paths:
        relative = path.relative_to(directory).as_posix()
        if relative in LIFECYCLE_FILES or path.name == ".DS_Store":
            continue
        result[f"files.{relative}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def bundle_values(directory: Path) -> dict[str, Any]:
    if not directory.is_dir():
        raise ComparisonFailure(f"profile directory does not exist: {directory}")
    values: dict[str, Any] = {}
    flatten(load_yaml(directory / "seqspec.yaml"), "seqspec", values)
    flatten(load_yaml(directory / "provenance.sidecar.yaml"), "sidecar", values)
    values.update(file_digests(directory))
    return values


def compare(parent: Path, child: Path) -> list[dict[str, Any]]:
    before = bundle_values(parent)
    after = bundle_values(child)
    changes: list[dict[str, Any]] = []
    for path in sorted(before.keys() | after.keys()):
        if before.get(path) != after.get(path) or (path in before) != (path in after):
            changes.append(
                {
                    "path": path,
                    "parent": before.get(path),
                    "child": after.get(path),
                }
            )
    return changes


def allowed(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def render_text(changes: list[dict[str, Any]], patterns: list[str]) -> str:
    lines = []
    for change in changes:
        status = "ALLOWED" if allowed(change["path"], patterns) else "UNEXPECTED"
        lines.append(
            f"{status} {change['path']}: "
            f"{json.dumps(change['parent'], sort_keys=True)} -> "
            f"{json.dumps(change['child'], sort_keys=True)}"
        )
    return "\n".join(lines) if lines else "No semantic or payload changes."


def main() -> int:
    args = parse_args()
    try:
        changes = compare(args.parent, args.child)
    except ComparisonFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    unexpected = [change for change in changes if not allowed(change["path"], args.allow)]
    if args.json:
        print(
            json.dumps(
                {
                    "changes": [
                        {**change, "allowed": allowed(change["path"], args.allow)}
                        for change in changes
                    ],
                    "unexpected_count": len(unexpected),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render_text(changes, args.allow))
    if unexpected:
        print(
            f"ERROR: {len(unexpected)} change(s) fall outside the allowlist.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
