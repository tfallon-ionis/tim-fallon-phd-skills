#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
seqspec_commit="5fb682b52c7ba9ad09e7796ca97a449726076530"
seqspec_source="seqspec @ git+https://github.com/tfallon-ionis/seqspec.git@${seqspec_commit}"

cd "${skill_dir}"
PYTHONDONTWRITEBYTECODE=1 uv run \
  --with pyyaml \
  --with jsonschema \
  --with "${seqspec_source}" \
  python -m unittest discover -s tests -v
