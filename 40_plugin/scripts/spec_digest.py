#!/usr/bin/env python3
"""
Content digests shared by renderers, the validator, and the eval suite (`40_plugin/scripts/spec_digest.py`).

A digest of the parsed `slide_spec.yaml` (not of the file bytes) is embedded in every compiled
deck and render manifest, so stale `.pptx`/`.png` outputs are detected regardless of YAML
formatting or line endings (`D-020`).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SPEC_DIGEST_PREFIX = "slide_spec_sha256:"


def canonical_json(data: Any) -> str:
    """Deterministic JSON serialization of a parsed YAML/JSON structure."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def spec_sha256(spec: Any) -> str:
    """SHA-256 of the canonical JSON form of a parsed slide spec."""
    return hashlib.sha256(canonical_json(spec).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    """SHA-256 of a file's raw bytes."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# D-090 (Editorial step 5): what the finish pass may change. Everything else in the spec is SWD content (words,
# numbers, Color Tie spans, focal and context roles, layout and chart types, sources) and is digested. Listing the
# few free fields, rather than the protected ones, keeps any field added later protected by default.
FINISH_FREE_KEYS = ("finish",)                      # the design layer's adjustments, at deck or slide level
QA_RESULT_KEYS = ("g4_review_audit", "rendered_png_qa")  # generated QA results, rewritten by every render


def content_view(node: Any) -> Any:
    """The spec without its finish blocks and generated QA results."""
    if isinstance(node, dict):
        return {k: content_view(v) for k, v in node.items() if k not in FINISH_FREE_KEYS + QA_RESULT_KEYS}
    if isinstance(node, list):
        return [content_view(v) for v in node]
    return node


def content_digest(spec: Any) -> str:
    """SHA-256 of the spec's SWD content; a finish pass that changes it is rejected (D-080 §6, D-090)."""
    return spec_sha256(content_view(spec))
