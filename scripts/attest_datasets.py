#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["blake3==1.0.11"]
# ///
"""Signing records for each dataset, and SSH signatures over them.

The paper has its own attestation protocol (docs/contrapunctus-attest.md). This
is the same mechanism for the corpora: OpenSSH Ed25519 signatures
(`ssh-keygen -Y`), in a separate namespace, `anthropic-pbc-dataset`, so a
dataset signature can never be replayed as an endorsement of the paper.

A record lists, for one dataset in corpus/datasets.tsv:
  - the BLAKE3 of every committed file in its corpus folder;
  - the BLAKE3 of every script its refresh command runs;
  - what a signature over the record attests.
It holds no clock and no commit id, so it is a pure function of the files. When
any file changes, the record changes, and an old signature stops verifying: the
dataset shows as stale until someone re-signs.

    uv run scripts/attest_datasets.py record                 # write attestations/datasets/<id>.txt
    uv run scripts/attest_datasets.py sign --key ~/.ssh/KEY --signer "NAME"   # run by the signer
    uv run scripts/attest_datasets.py verify                 # exit 1 on a bad or stale signature
    uv run scripts/attest_datasets.py status                 # signed / unsigned / stale per dataset

`sign` runs `verify` for each dataset's own build first (`<script> verify`),
when the script has one, and refuses to sign a record that is not current.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

import blake3

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "corpus" / "datasets.tsv"
DIR = ROOT / "attestations" / "datasets"
ALLOWED = ROOT / "attestations" / "allowed_signers"
NAMESPACE = "anthropic-pbc-dataset"
STATEMENT = (
    "By signing this record, the signer attests that, when they signed: the files listed\n"
    "had exactly these BLAKE3 hashes; the dataset's own verify step (where it has one)\n"
    "passed; and, where scripts are listed, the files are the output of those scripts\n"
    "run on the sources pinned in the dataset's MANIFEST.tsv. It does not attest that\n"
    "any finding drawn from the dataset is true, and it says nothing about model\n"
    "output in proposals/.\n")


def b3(p: Path) -> str:
    return blake3.blake3(p.read_bytes()).hexdigest()


def registry() -> list[dict[str, str]]:
    return [r for r in csv.DictReader(REGISTRY.open(), delimiter="\t") if r["corpus_dir"] != "—"]


def scripts_of(r: dict[str, str]) -> list[str]:
    return sorted(set(re.findall(r"scripts/[\w./-]+\.py", r["refresh"])))


def tracked(folder: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z", "--", folder], cwd=ROOT, capture_output=True, check=True).stdout
    return sorted(p for p in out.decode().split("\0") if p)


def render(r: dict[str, str]) -> str:
    lines = [f"namespace: {NAMESPACE}", f"dataset: {r['id']}", f"title: {r['title']}",
             f"pinned_as_of: {r['pinned_as_of']}", f"registry: corpus/datasets.tsv", "",
             STATEMENT, "files (BLAKE3, path):"]
    for p in tracked(r["corpus_dir"]):
        lines.append(f"{b3(ROOT / p)}  {p}")
    lines += ["", "scripts (BLAKE3, path):"]
    for p in scripts_of(r):
        lines.append(f"{b3(ROOT / p)}  {p}")
    return "\n".join(lines) + "\n"


def cmd_record(_a) -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    for r in registry():
        (DIR / f"{r['id']}.txt").write_text(render(r))
    print(f"wrote {len(registry())} records to {DIR.relative_to(ROOT)}/")
    return 0


def status() -> list[tuple[str, str]]:
    """(dataset, signed | unsigned | stale | bad-signature)."""
    res = []
    for r in registry():
        rec, sig = DIR / f"{r['id']}.txt", DIR / f"{r['id']}.txt.sig"
        current = rec.exists() and rec.read_text() == render(r)
        if not sig.exists():
            res.append((r["id"], "unsigned" if current else "unsigned, record stale"))
            continue
        if not current:
            res.append((r["id"], "stale (files changed since signing)"))
            continue
        signer = sig.with_suffix(".signer").read_text().strip() if sig.with_suffix(".signer").exists() else ""
        ok = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", str(ALLOWED), "-I", signer, "-n", NAMESPACE,
                             "-s", str(sig)], input=rec.read_bytes(), capture_output=True).returncode == 0
        res.append((r["id"], f"signed by {signer}" if ok else "bad signature"))
    return res


def cmd_status(_a) -> int:
    for d, s in status():
        print(f"{d:20} {s}")
    return 0


def cmd_verify(_a) -> int:
    bad = [(d, s) for d, s in status() if s.startswith(("stale", "bad"))]
    for d, s in bad:
        print(f"FAIL {d}: {s}")
    print("ok" if not bad else f"{len(bad)} dataset(s) failed")
    return 1 if bad else 0


def cmd_sign(a) -> int:
    if "\n" in a.signer or '"' in a.signer:
        sys.exit("signer name must be one line without quotes")
    key = Path(a.key).expanduser()
    pub = key.with_suffix(key.suffix + ".pub") if not key.name.endswith(".pub") else key
    if not pub.exists():
        sys.exit(f"no public key at {pub}")
    ids = [x for x in a.datasets] or [r["id"] for r in registry()]
    for r in registry():
        if r["id"] not in ids:
            continue
        rec = DIR / f"{r['id']}.txt"
        if not rec.exists() or rec.read_text() != render(r):
            sys.exit(f"{r['id']}: record is missing or stale; run `record` and commit it first")
        for s in scripts_of(r):
            src = (ROOT / s).read_text()
            if '"verify"' in src or "'verify'" in src:
                print(f"{r['id']}: {s} verify ...", flush=True)
                if subprocess.run(["uv", "run", s, "verify"], cwd=ROOT).returncode != 0:
                    sys.exit(f"{r['id']}: {s} verify failed; not signing")
        sig = rec.with_suffix(".txt.sig")
        sig.unlink(missing_ok=True)
        # ssh-keygen reads the private key itself (or the agent); no key material passes through here.
        if subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(key), "-n", NAMESPACE, str(rec)]).returncode != 0:
            sys.exit(f"{r['id']}: ssh-keygen sign failed")
        rec.with_suffix(".txt.signer").write_text(a.signer + "\n")
    # add the signer to allowed_signers once
    line = f'"{a.signer}" namespaces="{NAMESPACE}" ' + " ".join(pub.read_text().split()[:2])
    have = ALLOWED.read_text().splitlines() if ALLOWED.exists() else []
    if line not in have:
        ALLOWED.parent.mkdir(parents=True, exist_ok=True)
        ALLOWED.write_text("\n".join(have + [line]) + "\n")
    return cmd_status(a)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("record")
    sub.add_parser("status")
    sub.add_parser("verify")
    s = sub.add_parser("sign")
    s.add_argument("--key", required=True, help="path to your SSH private key (ssh-keygen reads it; agent keys work)")
    s.add_argument("--signer", required=True, help='name recorded in allowed_signers, e.g. "Sloane Ortel"')
    s.add_argument("datasets", nargs="*", help="dataset ids (default: all)")
    a = ap.parse_args()
    return {"record": cmd_record, "status": cmd_status, "verify": cmd_verify, "sign": cmd_sign}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
