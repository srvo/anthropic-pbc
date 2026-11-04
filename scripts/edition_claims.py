#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["blake3==1.0.11"]
# ///
"""The report's claim registry, edition/claims.tsv (stable ids), and its excerpts, edition/excerpts.tsv.

    edition/claims.tsv     id, key, kind, statement_ref, status, aliases, upstream, review, address, content_id
    edition/excerpts.tsv   key, commit, path, start, end, blake3, highlight_start, highlight_end, highlight_blake3

    uv run scripts/edition_claims.py locate COMMIT PATH "quoted text" "highlighted part"   # print an excerpt row

Ids are assigned once, in file order (C0001, C0002, ...), and never reused or renumbered: a claim that
is dropped keeps its row. The build checks the file and every committed version of it, so an id that
is reused for another key, or rows that are reordered, fail. `address` is the claim's global address
across Praxis-governed repositories, `praxis:claim/<namespace>/<id>`; `content_id` is the BLAKE3 of
its canonical statement, so the same claim stated in two repositories can be matched later. Neither is
ever reused.

An excerpt is a slice of a file at a commit, read with `git show` (never the working tree): character
offsets [start, end) into the file's text and the BLAKE3 of the slice's UTF-8 bytes, plus a highlighted
sub-span (the most relevant part) with its own offsets and BLAKE3. The build re-slices and re-hashes
both, so a moved or edited slice fails. It is shown with markdown emphasis and line breaks removed and
the highlight in bold; every numeral in it is the source's own figure, never recomputed.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import blake3

NAMESPACE = "anthropic-pbc"   # this repository's namespace in the Praxis claim address space
CLAIMS_TSV = "edition/claims.tsv"
EXCERPTS_TSV = "edition/excerpts.tsv"
EXCERPT_COLS = ("key", "commit", "path", "start", "end", "blake3", "highlight_start", "highlight_end", "highlight_blake3")
CLAIM_COLS = ("id", "key", "kind", "statement_ref", "status", "aliases", "upstream", "review", "address", "content_id")
KINDS = ("observation", "inference", "recommendation", "falsifier", "open question")   # Praxis kinds, kept intact


def b3(s: str) -> str:
    return blake3.blake3(s.encode()).hexdigest()


def content_id(statement: str) -> str:
    return "blake3:" + b3(statement)


def address(cid: str) -> str:
    return f"praxis:claim/{NAMESPACE}/{cid}"


def read_tsv(text: str, cols: tuple[str, ...], where: str) -> tuple[list[dict], list[str]]:
    lines = [l for l in text.splitlines() if l and not l.startswith("#")]
    rows = list(csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE))
    if not lines or tuple(lines[0].split("\t")) != cols:
        return [], [f"{where}: columns must be {list(cols)}"]
    return rows, [f"{where}: row {i} has {len(r)} cells" for i, r in enumerate(rows, 2) if None in r or None in r.values()]


def load_claims(text: str, where: str = CLAIMS_TSV) -> tuple[list[dict], list[str]]:
    """Rows of claims.tsv and every structural error: ids in file order from C0001 with no gap, unique
    keys and addresses, a Praxis kind, and the address derived from the id."""
    rows, errs = read_tsv(text, CLAIM_COLS, where)
    seen_key: dict[str, str] = {}
    seen_addr: dict[str, str] = {}
    for i, r in enumerate(rows, 1):
        want = f"C{i:04d}"
        if r["id"] != want:
            errs.append(f"{where}: row {i} has id {r['id']}, want {want} (ids are assigned in file order, append-only)")
        if r["key"] in seen_key:
            errs.append(f"{where}: key {r['key']} has two ids, {seen_key[r['key']]} and {r['id']}")
        seen_key.setdefault(r["key"], r["id"])
        if r["kind"] not in KINDS:
            errs.append(f"{where}: {r['id']} kind {r['kind']!r} is not one of {list(KINDS)}")
        if r["address"] in seen_addr:
            errs.append(f"{where}: {r['id']} and {seen_addr[r['address']]} share the address {r['address']}")
        seen_addr.setdefault(r["address"], r["id"])
        if r["address"] != address(r["id"]):
            errs.append(f"{where}: {r['id']} address {r['address']!r}, want {address(r['id'])!r}")
        if not re.fullmatch(r"blake3:[0-9a-f]{64}", r["content_id"]):
            errs.append(f"{where}: {r['id']} content_id must be blake3:<64 hex>")
    return rows, errs


def history_errs(rows: list[dict], versions: list[tuple[str, str]]) -> list[str]:
    """Every committed version of claims.tsv (commit, text) must survive in the current rows: the same id
    for the same key at the same address. Catches an id reused for another claim and renumbered rows."""
    now = {r["id"]: r for r in rows}
    errs = []
    for commit, text in versions:
        old, _ = read_tsv(text, CLAIM_COLS, f"{CLAIMS_TSV}@{commit[:12]}")
        for r in old:
            cur = now.get(r["id"])
            if cur is None:
                errs.append(f"{CLAIMS_TSV}: {r['id']} ({r['key']}) existed at {commit[:12]} and was removed; ids are never dropped")
            elif (cur["key"], cur["address"]) != (r["key"], r["address"]):
                errs.append(f"{CLAIMS_TSV}: {r['id']} was {r['key']} at {commit[:12]}, now {cur['key']}; ids are never reused")
    return errs


# ------------------------------------------------------------ excerpts
def norm(s: str) -> str:
    """Display text of a slice: markdown emphasis and line breaks removed."""
    return re.sub(r"\s+", " ", s.replace("*", ""))


@lru_cache(maxsize=None)
def git_show(commit: str, path: str, root: str) -> str:
    return subprocess.run(["git", "show", f"{commit}:{path}"], cwd=root, capture_output=True, text=True, check=True).stdout


def newer_revisions(commit: str, path: str, root: str) -> list[str]:
    """Commits after `commit` (on HEAD's history) that change `path`: the pin is no longer the latest."""
    return subprocess.run(["git", "log", "--format=%H", f"{commit}..HEAD", "--", path], cwd=root,
                          capture_output=True, text=True, check=True).stdout.split()


def load_excerpts(text: str, where: str = EXCERPTS_TSV) -> tuple[dict[str, dict], list[str]]:
    rows, errs = read_tsv(text, EXCERPT_COLS, where)
    out: dict[str, dict] = {}
    for r in rows:
        if r["key"] in out:
            errs.append(f"{where}: excerpt {r['key']} listed twice")
        if not re.fullmatch(r"[0-9a-f]{40}", r["commit"] or ""):
            errs.append(f"{where}: excerpt {r['key']}: commit must be a full 40-hex commit id")
        if not all(re.fullmatch(r"\d+", r[c] or "") for c in ("start", "end", "highlight_start", "highlight_end")):
            errs.append(f"{where}: excerpt {r['key']}: offsets must be integers")
            continue
        out[r["key"]] = r
    return out, errs


def verify_excerpt(r: dict, raw: str) -> tuple[str, str, list[str]]:
    """(shown, plain, errors) for one excerpt row against the file text at its commit. shown has the
    highlight in bold; plain is the display text without it."""
    k = r["key"]
    a, b, ha, hb = (int(r[c]) for c in ("start", "end", "highlight_start", "highlight_end"))
    if not 0 <= a < b <= len(raw):
        return "", "", [f"excerpt {k}: span {a}..{b} outside {r['path']}@{r['commit'][:12]}"]
    whole = raw[a:b]
    errs = []
    if b3(whole) != r["blake3"]:
        errs.append(f"excerpt {k}: slice {a}..{b} of {r['path']}@{r['commit'][:12]} does not hash to its blake3 "
                    f"(moved or edited): {norm(whole)[:60]!r}")
    if whole != whole.strip():
        errs.append(f"excerpt {k}: slice starts or ends with whitespace")
    if not a <= ha < hb <= b:
        return "", "", errs + [f"excerpt {k}: highlight {ha}..{hb} outside its excerpt {a}..{b}"]
    if b3(raw[ha:hb]) != r["highlight_blake3"]:
        errs.append(f"excerpt {k}: highlight {ha}..{hb} does not hash to its highlight_blake3 (moved or edited)")
    pre, hl, post = norm(raw[a:ha]), norm(raw[ha:hb]), norm(raw[hb:b])
    if pre + hl + post != norm(whole) or hl != hl.strip() or not hl:
        errs.append(f"excerpt {k}: highlight must start and end on text, not inside emphasis or whitespace")
    return pre + "**" + hl + "**" + post, norm(whole), errs


def locate(raw: str, text: str) -> tuple[int, int]:
    """Raw offsets of the one place whose display text (norm) is `text`."""
    keep = [(c if not c.isspace() else " ", i) for i, c in enumerate(raw) if c != "*"]
    flat, idx = [], []
    for c, i in keep:
        if c == " " and flat and flat[-1] == " ":
            continue
        flat.append(c)
        idx.append(i)
    s = "".join(flat)
    hits = [m.start() for m in re.finditer(re.escape(text), s)]
    if len(hits) != 1:
        raise ValueError(f"{text[:60]!r} occurs {len(hits)} times")
    return idx[hits[0]], idx[hits[0] + len(text) - 1] + 1


def table_cell(raw: str, at: int, col: int) -> str:
    """Cell `col` (1 = first) of the markdown table row holding offset `at`; '' when that line is no table row."""
    line = raw[raw.rfind("\n", 0, at) + 1:raw.find("\n", at)]
    cells = line.split("|")
    return cells[col].strip() if line.startswith("|") and len(cells) > col + 1 else ""


def excerpt_row(key: str, commit: str, path: str, raw: str, start: int, end: int, hs: int, he: int) -> str:
    return "\t".join([key, commit, path, str(start), str(end), b3(raw[start:end]), str(hs), str(he), b3(raw[hs:he])])


def main(argv: list[str]) -> int:
    if len(argv) == 6 and argv[1] == "locate":
        _, _, commit, path, text, hl = argv
        root = str(Path(__file__).resolve().parent.parent)
        commit = subprocess.run(["git", "rev-parse", commit], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        raw = git_show(commit, path, root)
        a, b = locate(raw, text)
        ha, hb = locate(raw[a:b], hl)
        print(excerpt_row("KEY", commit, path, raw, a, b, a + ha, a + hb))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
