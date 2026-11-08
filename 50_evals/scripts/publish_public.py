#!/usr/bin/env python3
"""
Publish the private working copy to the public repository in one command (`D-098`).

Work happens only in the private working copy. This script audits it, exports the public subset with
`export_public_tree.py`, mirrors the export into the public clone (keeping its `.git`), commits there, audits the
public clone (files and history), and pushes only when `--push` is given. Never edit the public clone by hand.

The public clone's path is read from `--target` or from this repository's local git config, so no personal path is
stored in a tracked file:
  git config publish.target "<path to the public clone>"

Usage:
  # once: create the public clone (fresh history, noreply author, AI-credit hook enabled)
  python 50_evals/scripts/publish_public.py --init --author-email <id>+<login>@users.noreply.github.com -m "Initial public release"
  # each time
  python 50_evals/scripts/publish_public.py -m "Release 0.1.0"
  python 50_evals/scripts/publish_public.py -m "Release 0.1.0" --push
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORT = REPO_ROOT / "50_evals" / "scripts" / "export_public_tree.py"
HOOKS_PATH = ".github/hooks"


def git(args, cwd: Path, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        raise SystemExit(f"[ERROR] git {' '.join(args)} failed in {cwd}:\n{result.stderr.strip()}")
    return result.stdout.strip()


def fail(message: str) -> None:
    raise SystemExit(f"[ERROR] {message}")


def run_audit(script: Path, cwd: Path, *extra: str) -> None:
    result = subprocess.run([sys.executable, str(script), *extra], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = "\n".join(line for line in result.stdout.splitlines() if line.startswith(("FINDING", "[OK]", "[INFO]")) or "audited" in line)
    print(tail)
    if result.returncode != 0:
        fail(f"audit failed ({script.relative_to(script.parents[2])} {' '.join(extra)}); nothing was published.\n{result.stderr.strip()}")


def resolve_target(arg: str | None) -> Path:
    raw = arg or git(["config", "--get", "publish.target"], REPO_ROOT, check=False)
    if not raw:
        fail('no public clone set: pass --target DIR or run git config publish.target "DIR".')
    target = Path(raw).expanduser().resolve()
    if target == REPO_ROOT or REPO_ROOT in target.parents or target in REPO_ROOT.parents:
        fail(f"{target} overlaps the private working copy.")
    if "dropbox" in str(target).lower():
        fail(f"{target} is inside Dropbox; keep the public clone outside it (D-014, D-098).")
    return target


def init_target(target: Path, name: str, email: str) -> None:
    if (target / ".git").exists():
        fail(f"{target} is already a git repository; drop --init.")
    if target.exists() and any(target.iterdir()):
        fail(f"{target} is not empty.")
    if not email.endswith("@users.noreply.github.com"):
        fail("--author-email must be a GitHub noreply address (D-098).")
    target.mkdir(parents=True, exist_ok=True)
    git(["init", "-b", "main"], target)
    git(["config", "user.name", name], target)
    git(["config", "user.email", email], target)
    print(f"[OK] Initialised {target} (main, {name} <{email}>)")


def check_target(target: Path) -> None:
    if not (target / ".git").exists():
        fail(f"{target} is not a git repository; create it with --init.")
    email = git(["config", "--get", "user.email"], target, check=False)
    if not email.endswith("@users.noreply.github.com"):
        fail(f"the public clone commits as '{email}'; set a GitHub noreply user.email there (D-098).")
    if git(["status", "--porcelain"], target):
        fail(f"{target} has uncommitted changes; the public clone must never be edited by hand.")


def _force_remove(func, path, _exc) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def mirror(src: Path, dst: Path) -> None:
    for item in dst.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item, onerror=_force_remove)
        else:
            item.unlink()
    shutil.copytree(src, dst, dirs_exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit, export, mirror and commit the public repository (D-098).")
    parser.add_argument("-m", "--message", required=True, help="Commit message for the public repository.")
    parser.add_argument("--target", help="Public clone (default: git config publish.target).")
    parser.add_argument("--push", action="store_true", help="Push to the public clone's origin after committing.")
    parser.add_argument("--init", action="store_true", help="Create the public clone with a fresh history.")
    parser.add_argument("--author-name", help="Author name for --init (default: this repository's user.name).")
    parser.add_argument("--author-email", help="GitHub noreply address for --init.")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if git(["status", "--porcelain", "--untracked-files=no"], REPO_ROOT):
        fail("the private working copy has uncommitted changes to tracked files; commit them first so the public tree matches a commit.")
    target = resolve_target(args.target)
    if args.init:
        if not args.author_email:
            fail("--init needs --author-email (a GitHub noreply address).")
        init_target(target, args.author_name or git(["config", "--get", "user.name"], REPO_ROOT), args.author_email)
    check_target(target)

    print("== Audit of the private working copy (includes the raw-source overlap check)")
    run_audit(EXPORT, REPO_ROOT, "--audit-only")

    with tempfile.TemporaryDirectory(prefix="public_export_") as tmp:
        print("== Export")
        run_audit(EXPORT, REPO_ROOT, "--out", tmp)
        mirror(Path(tmp), target)

    git(["config", "core.hooksPath", HOOKS_PATH], target)
    git(["add", "-A"], target)
    git(["update-index", "--chmod=+x", f"{HOOKS_PATH}/commit-msg"], target)  # Windows does not keep the bit
    changed = git(["diff", "--cached", "--name-status"], target)
    if not changed:
        print("[OK] Nothing to publish: the public clone already matches.")
    else:
        git(["commit", "-q", "-m", args.message], target)
        print(f"[OK] Committed {len(changed.splitlines())} changed file(s) in {target}: {git(['log', '-1', '--format=%h %s'], target)}")

    print("== Audit of the public clone (files and history)")
    run_audit(target / "50_evals" / "scripts" / "export_public_tree.py", target, "--audit-only")

    if args.push:
        if not git(["remote"], target):
            fail("the public clone has no remote; add origin first (needs the owner's authorization).")
        git(["push", "origin", "main"], target)
        print("[OK] Pushed main to origin.")
    else:
        print("[INFO] Not pushed (add --push when the owner authorizes it).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
