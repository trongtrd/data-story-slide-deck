#!/usr/bin/env python3
"""
Data Story Slide Deck installer (`40_plugin/install.py`) — standard library only, Windows / macOS / Linux.

What it does:
  1. Creates a private virtual environment at `$DATA_STORY_SLIDE_DECK_HOME/venv` (default `~/.data-story-slide-deck/venv`)
     and installs `requirements.txt` into it. `deckctl.py` switches to this environment by itself.
  2. Copies this plugin to `$DATA_STORY_SLIDE_DECK_HOME/plugin` so skills have a stable root.
  3. Registers the seven `deck-*` skills with the chosen agents:
       claude-code   `claude plugin marketplace add <repo>` + `claude plugin install data-story-slide-deck@data-story-slide-deck`
                     (needs the `claude` CLI and a clone of the repository; otherwise prints the commands)
       codex         skills copied to `~/.agents/skills/` (user) or `<project>/.agents/skills/` (project)
       antigravity   skills copied to `~/.gemini/config/skills/` (user; also `~/.gemini/antigravity/skills/` when that
                     legacy folder exists) or `<project>/.agents/skills/` (project)
       zcode         skills copied to `~/.zcode/skills/` (user) or `<project>/.agents/skills/` (project); ZCode reads
                     skills when a session starts, so open a new session after installing
     Copied skills get `${CLAUDE_PLUGIN_ROOT}` replaced by the absolute plugin path, and a marker file so a
     re-install or `--uninstall` only ever touches folders this installer created.
  4. Runs `deckctl.py doctor` and the quickstart smoke test.

Examples:
  python install.py                                  # environment + plugin copy + codex & antigravity user skills
  python install.py --target claude-code             # also install the Claude Code plugin from this repository
  python install.py --target codex --scope project --project-dir ~/decks/q3-review
  python install.py --deps-only                      # only the Python environment (e.g. after a marketplace install)
  python install.py --uninstall --target all
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Dict, List, Optional

PLUGIN_SRC = Path(__file__).resolve().parent
PLUGIN_NAME = "data-story-slide-deck"
MARKER = ".data-story-slide-deck-managed"
PLACEHOLDER = "${CLAUDE_PLUGIN_ROOT}"
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
TARGETS = ("claude-code", "codex", "antigravity", "zcode")


def log(msg: str) -> None:
    print(msg, flush=True)


def plugin_version() -> str:
    manifest = PLUGIN_SRC / ".claude-plugin" / "plugin.json"
    return json.loads(manifest.read_text(encoding="utf-8")).get("version", "0.0.0")


def venv_python(home: Path) -> Path:
    return home / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd: List[str], dry_run: bool, check: bool = True) -> int:
    log("  $ " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    if dry_run:
        return 0
    rc = subprocess.call(cmd)
    if check and rc != 0:
        raise SystemExit(f"[ERROR] Command failed with exit code {rc}.")
    return rc


# ------------------------------------------------------------------------------
# Python environment and plugin copy
# ------------------------------------------------------------------------------

def setup_environment(home: Path, dry_run: bool) -> None:
    vpy = venv_python(home)
    if not vpy.exists():
        log(f"[1/4] Creating virtual environment at {home / 'venv'}")
        if not dry_run:
            venv.EnvBuilder(with_pip=True, clear=False).create(home / "venv")
    else:
        log(f"[1/4] Reusing virtual environment at {home / 'venv'}")
    run([str(vpy), "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", str(PLUGIN_SRC / "requirements.txt")], dry_run)


def copy_plugin(home: Path, dry_run: bool) -> Path:
    dest = home / "plugin"
    log(f"[2/4] Copying plugin {plugin_version()} to {dest}")
    if not dry_run and dest.resolve() != PLUGIN_SRC:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PLUGIN_SRC, dest, ignore=COPY_IGNORE)
    return dest


# ------------------------------------------------------------------------------
# Skill registration
# ------------------------------------------------------------------------------

def skill_dirs_for(target: str, scope: str, project_dir: Optional[Path], user_home: Path) -> List[Path]:
    if scope == "project":
        if project_dir is None:
            raise SystemExit("[ERROR] --scope project needs --project-dir.")
        return [project_dir / ".agents" / "skills"]
    if target == "codex":
        return [user_home / ".agents" / "skills"]
    if target == "zcode":
        return [user_home / ".zcode" / "skills"]
    if target == "antigravity":
        dirs = [user_home / ".gemini" / "config" / "skills"]
        legacy = user_home / ".gemini" / "antigravity"
        if legacy.exists():
            dirs.append(legacy / "skills")
        return dirs
    return []


def install_skill_copies(plugin_root: Path, skills_root: Path, force: bool, dry_run: bool) -> None:
    root_text = plugin_root.resolve().as_posix()
    for skill in sorted((PLUGIN_SRC / "skills").glob("deck-*/SKILL.md")):
        dest = skills_root / skill.parent.name
        if dest.exists() and not (dest / MARKER).exists() and not force:
            log(f"  ! {dest} exists and was not created by this installer; skipped (use --force to replace)")
            continue
        log(f"  + {dest}")
        if dry_run:
            continue
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text(skill.read_text(encoding="utf-8").replace(PLACEHOLDER, root_text), encoding="utf-8")
        (dest / MARKER).write_text(json.dumps({"plugin": PLUGIN_NAME, "version": plugin_version(), "plugin_root": root_text}) + "\n", encoding="utf-8")


def remove_skill_copies(skills_root: Path, dry_run: bool) -> None:
    for skill in sorted((PLUGIN_SRC / "skills").glob("deck-*")):
        dest = skills_root / skill.name
        if (dest / MARKER).exists():
            log(f"  - {dest}")
            if not dry_run:
                shutil.rmtree(dest)


def claude_code(scope: str, dry_run: bool, uninstall: bool) -> None:
    repo_root = PLUGIN_SRC.parent
    marketplace = repo_root / ".claude-plugin" / "marketplace.json"
    claude = shutil.which("claude")
    plugin_scope = "project" if scope == "project" else "user"
    if uninstall:
        cmds = [["claude", "plugin", "uninstall", f"{PLUGIN_NAME}@{PLUGIN_NAME}"]]
    elif marketplace.exists():
        cmds = [
            ["claude", "plugin", "marketplace", "add", str(repo_root)],
            ["claude", "plugin", "install", f"{PLUGIN_NAME}@{PLUGIN_NAME}", "--scope", plugin_scope],
        ]
    else:
        log("  This copy is not inside the repository clone, so there is no marketplace to add.")
        log("  Install from GitHub instead:  claude plugin marketplace add <owner>/<repo>  then  claude plugin install data-story-slide-deck@data-story-slide-deck")
        raise SystemExit("[ERROR] Claude registration was not completed: repository marketplace is missing.")
    if claude is None:
        log("  `claude` CLI not found. Run these commands yourself:")
        for c in cmds:
            log("    " + " ".join(c))
        raise SystemExit("[ERROR] Claude registration was not completed; install the CLI and retry.")
    for c in cmds:
        run([claude] + c[1:], dry_run)


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Install the Data Story Slide Deck skill suite.")
    parser.add_argument("--target", default="codex,antigravity", help="Comma list of claude-code, codex, antigravity, zcode, all, none (default: codex,antigravity).")
    parser.add_argument("--scope", choices=["user", "project"], default="user")
    parser.add_argument("--project-dir", type=Path, help="Project folder for --scope project.")
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("DATA_STORY_SLIDE_DECK_HOME") or Path.home() / ".data-story-slide-deck"), help="Where the venv and plugin copy live.")
    parser.add_argument("--user-home", type=Path, default=Path.home(), help=argparse.SUPPRESS)  # for testing against a throwaway home
    parser.add_argument("--deps-only", action="store_true", help="Only create/update the Python environment.")
    parser.add_argument("--no-smoke", action="store_true", help="Skip doctor and the smoke test.")
    parser.add_argument("--force", action="store_true", help="Replace same-named skill folders not created by this installer.")
    parser.add_argument("--uninstall", action="store_true", help="Remove installed skills (and the Claude Code plugin with --target claude-code).")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without changing anything.")
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        raise SystemExit(f"[ERROR] Python 3.10+ required (found {sys.version.split()[0]}).")
    targets = [t.strip() for t in args.target.split(",") if t.strip()]
    if "all" in targets:
        targets = list(TARGETS)
    if "none" in targets:
        targets = []
    unknown = [t for t in targets if t not in TARGETS]
    if unknown:
        raise SystemExit(f"[ERROR] Unknown target(s): {unknown}. Choose from {TARGETS}, all, none.")
    home: Path = args.home.expanduser().resolve()
    project_dir = args.project_dir.expanduser().resolve() if args.project_dir else None

    if args.uninstall:
        for t in targets:
            log(f"Uninstalling from {t}")
            if t == "claude-code":
                claude_code(args.scope, args.dry_run, uninstall=True)
            else:
                for d in skill_dirs_for(t, args.scope, project_dir, args.user_home):
                    remove_skill_copies(d, args.dry_run)
        log(f"Done. The environment and plugin copy remain in {home}; delete that folder to remove them.")
        return 0

    setup_environment(home, args.dry_run)
    if args.deps_only:
        log(f"[OK] Python environment ready: {venv_python(home)}")
        return 0
    plugin_root = copy_plugin(home, args.dry_run)

    log(f"[3/4] Registering skills for: {', '.join(targets) or 'none'} ({args.scope} scope)")
    done_dirs: Dict[str, List[str]] = {}
    for t in targets:
        if t == "claude-code":
            claude_code(args.scope, args.dry_run, uninstall=False)
            continue
        for d in skill_dirs_for(t, args.scope, project_dir, args.user_home):
            install_skill_copies(plugin_root, d, args.force, args.dry_run)
            done_dirs.setdefault(t, []).append(str(d))

    if args.no_smoke or args.dry_run:
        log("[4/4] Skipped doctor and smoke test.")
    else:
        log("[4/4] Checking the installation")
        deckctl = str(plugin_root / "scripts" / "deckctl.py")
        env_ok = run([str(venv_python(home)), deckctl, "doctor"], False, check=False) == 0
        smoke_ok = run([str(venv_python(home)), deckctl, "smoke"], False, check=False) == 0
        if not (env_ok and smoke_ok):
            log("[WARN] Installed, but doctor or smoke reported problems (see above).")
            return 1

    log("\n[OK] Data Story Slide Deck installed.")
    log(f"     Plugin root: {plugin_root}")
    for t, dirs in done_dirs.items():
        log(f"     {t}: {', '.join(dirs)}")
    if "zcode" in done_dirs:
        log("     ZCode: open a new session; sessions started before the install do not list the skills.")
    log("     Start a deck by asking your agent to use `deck-orchestrator` on a folder with your report and data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
