"""Export a public release of this project from Dark into a clone of the public repository.

Dark is the only source (owner direction 2026-11-05). The public GitHub repository
receives releases, never Dark history: this copies the files git tracks under
anthropic-pbc/, minus EXPORT-EXCLUDE, into TARGET (a clone of the public repo),
writes RELEASE.json (each file's SHA-256 and the content hash of the source tree)
and commits there. It never pushes; the push needs the one scoped credential and
is run by the owner.

    python3 scripts/export_public.py TARGET            # sync, write RELEASE.json, commit
    python3 scripts/export_public.py TARGET --dry-run  # list what would change
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # anthropic-pbc/
EXCLUDE_FILE = "EXPORT-EXCLUDE"
EXPECTED_REMOTE = "github.com/srvo/anthropic-pbc"
RELEASE_BRANCH = "main"  # the only public branch; Pages deploys from it


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def patterns(src: Path) -> list[str]:
    f = src / EXCLUDE_FILE
    if not f.exists():
        sys.exit(f"{EXCLUDE_FILE} is missing: refusing to export without an exclusion list")
    return [l.strip() for l in f.read_text().splitlines() if l.strip() and not l.startswith("#")]


def excluded(path: str, pats: list[str]) -> bool:
    for p in pats:
        if p.endswith("/") and (path == p.rstrip("/") or path.startswith(p)):
            return True
        if fnmatch.fnmatch(path, p):
            return True
    return False


def export_set(src: Path) -> list[str]:
    """Tracked files under src, relative to it, minus the exclusions."""
    top = Path(git("rev-parse", "--show-toplevel", cwd=src).strip())
    prefix = src.resolve().relative_to(top.resolve()).as_posix()
    files = git("ls-files", "-z", "--", ".", cwd=src).split("\0")
    pats = patterns(src)
    out = []
    for f in files:
        if not f:
            continue
        rel = f  # ls-files from inside src lists paths relative to src
        if not excluded(rel, pats) and (src / rel).is_file():
            out.append(rel)
    if prefix and not out:
        sys.exit("nothing to export")
    return sorted(out)


def tree_hash(src: Path) -> str:
    """Content hash of the source tree at HEAD (identifies the edition without exposing a Dark commit)."""
    top = Path(git("rev-parse", "--show-toplevel", cwd=src).strip())
    prefix = src.resolve().relative_to(top.resolve()).as_posix()
    return git("rev-parse", f"HEAD:{prefix}" if prefix else "HEAD^{tree}", cwd=top).strip()


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def export(src: Path, target: Path, dry_run: bool = False, check_remote: bool = True) -> dict:
    if not (target / ".git").exists():
        sys.exit(f"{target} is not a git clone of the public repository")
    if check_remote:
        url = git("remote", "get-url", "origin", cwd=target).strip()
        if EXPECTED_REMOTE not in url:
            sys.exit(f"target origin is not {EXPECTED_REMOTE}")
    if git("status", "--porcelain", cwd=target).strip():
        sys.exit("target has uncommitted changes: refusing to overwrite them")
    branch = git("branch", "--show-current", cwd=target).strip()
    if branch != RELEASE_BRANCH:
        sys.exit(f"target is on {branch or 'a detached HEAD'}: releases go to {RELEASE_BRANCH} only")
    if git("status", "--porcelain", "--", ".", cwd=src).strip() and not dry_run:
        sys.exit("source has uncommitted changes: export only committed work")
    files = export_set(src)
    keep = set(files) | {"RELEASE.json"}
    existing = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file() and ".git" not in p.relative_to(target).parts}
    removed = sorted(existing - keep)
    changed = sorted(f for f in files if not (target / f).exists() or sha256(target / f) != sha256(src / f))
    manifest = {"source": "dark:anthropic-pbc", "tree": tree_hash(src), "files": {f: sha256(src / f) for f in files}}
    if dry_run:
        return {"changed": changed, "removed": removed, "files": len(files), "tree": manifest["tree"]}
    for f in removed:
        (target / f).unlink()
    for f in changed:
        (target / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / f, target / f)
    (target / "RELEASE.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    git("add", "-A", cwd=target)
    if git("status", "--porcelain", cwd=target).strip():
        git("commit", "-q", "-m", f"Release from Dark, source tree {manifest['tree'][:12]}\n\n"
            f"{len(changed)} files changed, {len(removed)} removed. RELEASE.json lists every file's SHA-256.", cwd=target)
    return {"changed": changed, "removed": removed, "files": len(files), "tree": manifest["tree"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    r = export(HERE, a.target.expanduser().resolve(), a.dry_run)
    print(f"{'would export' if a.dry_run else 'exported'} {r['files']} files from tree {r['tree'][:12]}: "
          f"{len(r['changed'])} changed, {len(r['removed'])} removed")
    if not a.dry_run:
        print(f"push when ready: git -C {a.target} push origin HEAD")
