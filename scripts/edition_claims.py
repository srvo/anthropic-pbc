"""The report's claim registry: edition/claims.tsv (stable ids).

    edition/claims.tsv   id, key, kind, statement_ref, status, aliases, upstream, review, address, content_id

Ids are assigned once, in file order (C0001, C0002, ...), and never reused or renumbered: a claim that
is dropped keeps its row. The build checks the file and every committed version of it, so an id that
is reused for another key, or rows that are reordered, fail. `address` is the claim's global address
across Praxis-governed repositories, `praxis:claim/<namespace>/<id>`; `content_id` is the BLAKE3 of
its canonical statement, so the same claim stated in two repositories can be matched later. Neither is
ever reused. The build imports this module; it has no command line of its own.
"""

from __future__ import annotations

import csv
import re

import blake3

NAMESPACE = "anthropic-pbc"   # this repository's namespace in the Praxis claim address space
CLAIMS_TSV = "edition/claims.tsv"
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
