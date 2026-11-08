#!/usr/bin/env python3
"""
Sync the plugin's bundled resources from their canonical sources (`50_evals/scripts/sync_plugin_resources.py`).

The distributable plugin (`40_plugin/`) must be self-contained (`D-022`), but the canonical files stay where
`AGENTS.md` assigns them. This script copies, byte for byte:
  - `30_design/contracts/*` and `30_design/workflow.md`  ->  `40_plugin/contracts/`
  - accepted knowledge cards, `GLOSSARY.md`, `INDEX.md`   ->  `40_plugin/knowledge/`
  - `LICENSE`, `LICENSE-CONTENT`, `NOTICE`                ->  `40_plugin/`
Never edit the copies; edit the source and re-run this script. `--check` exits 1 when the copies drift
(the eval suite runs it).

Usage:
  python 50_evals/scripts/sync_plugin_resources.py [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "40_plugin"
CARD_DIRS = ("principles", "patterns", "anti-patterns", "checklists", "examples", "language-rules")


def card_status(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    fm = yaml.safe_load(text.split("---", 2)[1]) or {}
    return str(fm.get("status", ""))


def expected_files() -> Dict[Path, Path]:
    """Map of plugin destination -> canonical source."""
    mapping: Dict[Path, Path] = {}
    for src in sorted((REPO_ROOT / "30_design" / "contracts").glob("*")):
        if src.is_file():
            mapping[PLUGIN / "contracts" / src.name] = src
    mapping[PLUGIN / "contracts" / "workflow.md"] = REPO_ROOT / "30_design" / "workflow.md"
    for name in ("LICENSE", "LICENSE-CONTENT", "NOTICE"):  # marketplaces copy only the plugin folder
        mapping[PLUGIN / name] = REPO_ROOT / name
    kb = REPO_ROOT / "20_knowledge"
    for name in ("GLOSSARY.md", "INDEX.md", "CONFLICTS.md"):
        mapping[PLUGIN / "knowledge" / name] = kb / name
    for sub in CARD_DIRS:
        for card in sorted((kb / sub).glob("*.md")):
            if card_status(card) == "accepted":
                mapping[PLUGIN / "knowledge" / sub / card.name] = card
    return mapping


# `30_design/workflow.md` sits beside `contracts/` in the repo but inside it in the plugin; keep its links live.
WORKFLOW_LINKS = (("](./contracts/", "](./"), ("](../20_knowledge/", "](../knowledge/"))


def bundled_bytes(dst: Path, src: Path) -> bytes:
    data = src.read_bytes()
    if dst == PLUGIN / "contracts" / "workflow.md":
        text = data.decode("utf-8")
        for old, new in WORKFLOW_LINKS:
            text = text.replace(old, new)
        data = text.encode("utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy canonical contracts and accepted knowledge cards into 40_plugin/.")
    parser.add_argument("--check", action="store_true", help="Report drift and exit 1 instead of writing.")
    args = parser.parse_args()

    mapping = expected_files()
    managed_roots = [PLUGIN / "contracts", PLUGIN / "knowledge"]
    existing = {p for root in managed_roots if root.exists() for p in root.rglob("*") if p.is_file()}
    stale = sorted(existing - set(mapping))
    drift = [dst for dst, src in mapping.items() if not dst.exists() or dst.read_bytes() != bundled_bytes(dst, src)]

    if args.check:
        for p in drift:
            print(f"DRIFT: {p.relative_to(REPO_ROOT)} differs from its source")
        for p in stale:
            print(f"STALE: {p.relative_to(REPO_ROOT)} has no source")
        print(f"{len(mapping)} bundled files, {len(drift)} drifted, {len(stale)} stale")
        return 1 if drift or stale else 0

    for dst in drift:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(bundled_bytes(dst, mapping[dst]))
    for p in stale:
        p.unlink()
    print(f"[OK] {len(mapping)} bundled files ({len(drift)} written, {len(stale)} removed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
