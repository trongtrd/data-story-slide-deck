#!/usr/bin/env python3
"""
Export and audit the public release tree (`50_evals/scripts/export_public_tree.py`) — D-016, D-017, D-018.

1. Copies every git-tracked file except the private ones (`10_sources/notes/`, `10_sources/raw/`, dated session
   handoffs, dated reports in `50_evals/reports/` (`D-101`), `90_archive/`) into `--out`, rewriting links that
   would point at excluded files.
2. Audits the exported tree and exits 1 on any finding:
   - verbatim overlap with the raw sources (shared 12-word runs, or > 5% of a file covered by shared 8-word runs),
     when `10_sources/raw/` is available locally (it is gitignored and never published);
   - names from the source articles' own case studies (`D-017`);
   - secrets (API keys, tokens, private keys) and personal absolute paths;
   - raw sources ever committed to git history;
   - commits that credit an AI tool, which GitHub would list among the Contributors (`D-042`, `D-098`);
   - missing LICENSE, LICENSE-CONTENT, or NOTICE.

Usage:
  python 50_evals/scripts/export_public_tree.py --out ../data-story-slide-deck-public
  python 50_evals/scripts/export_public_tree.py --audit-only
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
EXCLUDE_PREFIXES = ("10_sources/notes/", "10_sources/raw/", "90_archive/")
HANDOFF_RE = re.compile(r"^00_admin/handoffs/\d{4}-\d{2}-\d{2}_.*\.md$")
# Dated design proposals and platform test reports are internal process records, like handoffs (D-101).
REPORT_RE = re.compile(r"^50_evals/reports/\d{4}-\d{2}-\d{2}_.*\.md$")
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".csv", ".txt", ".html", ".toml", ""}

# Proper nouns from the source articles' own worked examples; original scenarios replace them (D-017).
SOURCE_CASE_NAMES = [
    "Alunis", "Vyrenta", "Wholesome Goodness", "Fran's Recipe", "Fran’s Recipe",
    "Diana", "Priya", "Marcus", "People Analytics Manager",
]
SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "API key (sk-…)"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
]
PERSONAL_PATH_RE = re.compile(r"(?:[A-Za-z]:\\\\?Users\\\\?[^\\/\s\"']+|/Users/[^/\s\"']+|/home/[^/\s\"']+)", re.IGNORECASE)
AI_IDENTITY_RE = re.compile(r"claude|anthropic|copilot|chatgpt|openai|gemini|codex", re.IGNORECASE)
AI_CREDIT_RE = re.compile(r"generated (?:with|by) \[?(?:claude|chatgpt|copilot|gemini|codex)", re.IGNORECASE)
REQUIRED_FILES = ("LICENSE", "LICENSE-CONTENT", "NOTICE", "40_plugin/LICENSE", "40_plugin/LICENSE-CONTENT", "40_plugin/NOTICE")


def tracked_files() -> List[str]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_public(rel: str) -> bool:
    if rel.startswith(EXCLUDE_PREFIXES) or HANDOFF_RE.match(rel) or REPORT_RE.match(rel):
        return False
    return True


def rewrite_links(rel: str, text: str) -> str:
    """Point links at excluded files to plain text so the public tree has no dead links."""
    text = re.sub(r"\[`?([^\]`]+)`?\]\(\./notes/[^)]+\)", r"`\1` (private study note, not published)", text)
    text = re.sub(r"\[`?([^\]`]+)`?\]\((?:\./)?(?:00_admin/)?handoffs/\d{4}[^)]*\)", r"`\1` (internal handoff, not published)", text)
    text = re.sub(r"\[`?([^\]`]+)`?\]\((?:[./]*)(?:50_evals/)?reports/\d{4}[^)]*\)", r"`\1` (internal report, not published)", text)
    return text


def export(out: Path) -> List[str]:
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"[ERROR] {out} is not empty.")
    files = [f for f in tracked_files() if is_public(f)]
    for rel in files:
        src, dst = REPO_ROOT / rel, out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() == ".md":
            dst.write_text(rewrite_links(rel, src.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        else:
            shutil.copy2(src, dst)
    return files


# ------------------------------------------------------------------------------
# Audit
# ------------------------------------------------------------------------------

def words(text: str) -> List[str]:
    """Lower-case word tokens; URLs are dropped so citations of the source articles do not count as overlap."""
    return re.findall(r"[a-z0-9']+", re.sub(r"https?://\S+", " ", text.lower()))


def raw_ngrams(n: int) -> Set[str]:
    raw_dir = REPO_ROOT / "10_sources" / "raw"
    texts: List[str] = []
    for p in sorted(raw_dir.glob("*")) if raw_dir.exists() else []:
        if p.suffix == ".md":
            texts.append(p.read_text(encoding="utf-8", errors="ignore"))
        elif p.suffix == ".pdf":
            try:
                import pypdfium2 as pdfium

                doc = pdfium.PdfDocument(str(p))
                texts.append(" ".join(doc[i].get_textpage().get_text_range() for i in range(len(doc))))
            except Exception as exc:  # the PDF is optional for the audit
                print(f"[WARN] could not read {p.name}: {exc}")
    grams: Set[str] = set()
    for t in texts:
        w = words(t)
        grams.update(" ".join(w[i:i + n]) for i in range(len(w) - n + 1))
    return grams


def ai_attribution_in_history() -> List[str]:
    """Commits that would list an AI tool among the GitHub Contributors (D-042, D-098).

    GitHub builds Contributors from author and committer emails and from `Co-authored-by` trailers, so all three
    are checked; this also catches commits made on GitHub's web interface, which local hooks never see.
    """
    log = subprocess.run(["git", "log", "--all", "--format=%h%x00%an <%ae>%x00%cn <%ce>%x00%B%x01"],
                         cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    findings: List[str] = []
    for entry in filter(str.strip, log.split("\x01")):
        sha, author, committer, body = (entry.strip("\n").split("\x00") + ["", "", ""])[:4]
        people = [author, committer] + [l for l in body.splitlines() if l.lower().startswith("co-authored-by:")]
        if any(AI_IDENTITY_RE.search(p) for p in people) or AI_CREDIT_RE.search(body):
            findings.append(f"commit {sha}: credits an AI tool (author, committer, trailer or 'Generated with' line)")
    return findings


def audit(root: Path, files: List[str]) -> List[str]:
    findings: List[str] = []
    for req in REQUIRED_FILES:
        if not (root / req).exists():
            findings.append(f"missing {req}")

    history = subprocess.run(["git", "log", "--all", "--format=%h", "--", "10_sources/raw"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    if history:
        findings.append(f"10_sources/raw appears in git history (commits: {history.split()[:5]})")
    findings.extend(ai_attribution_in_history())

    g8, g12 = raw_ngrams(8), raw_ngrams(12)
    if not g8:
        print("[INFO] 10_sources/raw not available; overlap audit skipped (run it from the private working copy).")

    for rel in files:
        p = root / rel
        if p.suffix.lower() not in TEXT_SUFFIXES or not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if rel.startswith("50_evals/scripts/export_public_tree.py"):
            continue  # holds the name list itself
        for name in SOURCE_CASE_NAMES:
            if re.search(r"\b" + re.escape(name) + r"\b", text):
                findings.append(f"{rel}: source case-study name '{name}' (D-017)")
        for pattern, what in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{rel}: possible {what}")
        m = PERSONAL_PATH_RE.search(text)
        if m:
            findings.append(f"{rel}: personal absolute path '{m.group(0)}'")
        if g8 and p.suffix.lower() in (".md", ".yaml", ".yml"):
            w = words(text)
            covered: Set[int] = set()
            long_run = False
            for i in range(len(w) - 7):
                if " ".join(w[i:i + 8]) in g8:
                    covered.update(range(i, i + 8))
                    if i + 12 <= len(w) and " ".join(w[i:i + 12]) in g12:
                        long_run = True
            share = len(covered) / max(len(w), 1)
            if long_run or share > 0.05:
                findings.append(f"{rel}: verbatim overlap with raw sources ({share:.1%} of words in shared 8-word runs{', incl. a 12-word run' if long_run else ''})")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Export and audit the public release tree.")
    parser.add_argument("--out", type=Path, help="Empty folder to export into (outside Dropbox, per D-014).")
    parser.add_argument("--audit-only", action="store_true", help="Audit the public subset of this working copy without exporting.")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.audit_only:
        files, root = [f for f in tracked_files() if is_public(f)], REPO_ROOT
    elif args.out:
        files, root = export(args.out), args.out
        print(f"[OK] Exported {len(files)} files to {args.out}")
    else:
        parser.error("Pass --out DIR or --audit-only.")

    findings = audit(root, files)
    for f in findings:
        print(f"FINDING: {f}")
    print(f"{len(files)} public files audited, {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
