"""Tests for scripts/export_public.py: exclusions hold, the manifest matches, stale files go, nothing pushes."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_public as ex  # noqa: E402


def sh(*a: str, cwd: Path) -> str:
    return subprocess.run(list(a), cwd=cwd, check=True, capture_output=True, text=True).stdout


def repo(path: Path) -> Path:
    path.mkdir(parents=True)
    sh("git", "init", "-q", "-b", "main", cwd=path)
    sh("git", "config", "user.email", "test@example.invalid", cwd=path)
    sh("git", "config", "user.name", "test", cwd=path)
    return path


def write(root: Path, rel: str, text: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text)


def main() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        dark = repo(t / "dark")
        src = dark / "anthropic-pbc"
        write(dark, "secret-plan.md", "dark only")  # outside the project: never exported
        write(src, "README.md", "public")
        write(src, "argument/cards.tsv", "A001\tclaim\n")
        write(src, "private/pricing.md", "privileged")
        write(src, "research/survey/instrument.md", "draft")
        write(src, "notes.privileged.md", "privileged")
        write(src, "EXPORT-EXCLUDE", "private/\nresearch/survey/\n*.privileged.*\nEXPORT-EXCLUDE\n")
        sh("git", "add", "-A", cwd=dark)
        sh("git", "commit", "-q", "-m", "dark history message that must not leave", cwd=dark)

        pub = repo(t / "public")
        write(pub, "stale.txt", "removed upstream")
        sh("git", "add", "-A", cwd=pub)
        sh("git", "commit", "-q", "-m", "old release", cwd=pub)

        r = ex.export(src, pub, check_remote=False)
        files = {p.relative_to(pub).as_posix() for p in pub.rglob("*") if p.is_file() and ".git" not in p.relative_to(pub).parts}

        def check(ok: bool, what: str) -> None:
            nonlocal fails
            print(("ok    " if ok else "FAIL  ") + what)
            fails += not ok

        check(files == {"README.md", "argument/cards.tsv", "RELEASE.json"}, f"only public files exported: {sorted(files)}")
        check("secret-plan.md" not in files, "files outside the project never leave")
        check(not any(f.startswith(("private/", "research/survey/")) for f in files), "excluded folders stay in Dark")
        man = json.loads((pub / "RELEASE.json").read_text())
        check(all(hashlib.sha256((pub / f).read_bytes()).hexdigest() == h for f, h in man["files"].items()), "RELEASE.json hashes match the files")
        log = sh("git", "log", "--format=%B", cwd=pub)
        check("dark history" not in log, "no Dark commit message reaches the public history")
        check(r["removed"] == ["stale.txt"], "stale public files are removed")
        check(sh("git", "remote", cwd=pub).strip() == "", "export does not add or use a remote (never pushes)")

        write(pub, "dirty.txt", "uncommitted")
        try:
            ex.export(src, pub, check_remote=False)
            check(False, "refuses a target with uncommitted changes")
        except SystemExit:
            check(True, "refuses a target with uncommitted changes")
        sh("git", "checkout", "-q", "-b", "cards/side", cwd=pub)
        (pub / "dirty.txt").unlink()
        try:
            ex.export(src, pub, check_remote=False)
            check(False, "refuses any branch but main")
        except SystemExit:
            check(True, "refuses any branch but main")
    print(f"\n{fails} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
