#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["blake3==1.0.11"]
# ///
"""The report's claim registry, edition/claims.tsv (stable ids), and its excerpts, edition/excerpts.tsv.

    edition/claims.tsv     id, key, kind, statement_ref, status, aliases, upstream, review, address, content_id
    edition/excerpts.tsv   key, commit, path, start, end, blake3, highlight_start, highlight_end, highlight_blake3

    uv run scripts/edition_claims.py locate COMMIT PATH "quoted text" "highlighted part"   # print an excerpt row
    uv run scripts/edition_claims.py paper COMMIT   # append the paper's claims at COMMIT (new ones only)

`paper` parses the committed paper (git show COMMIT:docs/anthropic-contrapunctus.md, never the working
tree): Appendix C (kind inference, status = its Verdict cell), the section 7 GOV table (recommendation)
and the falsifiers of sections 6 and 8 (falsifier). The GOV table and the falsifier lists carry no status,
so their status is NO_STATUS. The highlight is mechanical: the Report's quoted words in an Appendix C
claim, the mechanism's bold name in a GOV row, the whole falsifier.

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
    if (ha, hb) == (a, b):   # nothing singled out yet: shown plain
        return norm(whole), norm(whole), errs
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


# ------------------------------------------------------------ the paper's own claims
PAPER = "docs/anthropic-contrapunctus.md"
NO_STATUS = "none stated"   # the paper gives this kind of row no status


def _section(raw: str, heading: str) -> tuple[int, int]:
    m = re.search(r"^" + re.escape(heading), raw, re.M)
    if not m:
        raise ValueError(f"paper has no section {heading!r}")
    n = re.search(r"^## ", raw[m.end():], re.M)
    return m.start(), m.end() + n.start() if n else len(raw)


def _rows(raw: str, a: int, b: int):
    """(cells, header?) per markdown table row in raw[a:b]; each cell is (start, end) of its stripped text."""
    pos, first = a, True
    for line in raw[a:b].splitlines(keepends=True):
        at, pos = pos, pos + len(line)
        if not line.startswith("|"):
            first = True
            continue
        if re.fullmatch(r"\|[-| :]+\|\s*", line):
            continue
        pipes = [i for i, c in enumerate(line) if c == "|"]
        cells = []
        for x, y in zip(pipes, pipes[1:]):
            t = line[x + 1:y]
            lead = len(t) - len(t.lstrip())
            cells.append((at + x + 1 + lead, at + x + 1 + len(t.rstrip())))
        yield cells, first
        first = False


def parse_paper(raw: str) -> list[dict]:
    """The paper's claims: alias, key, kind, status and the excerpt span (start, end, highlight)."""
    out = []
    def add(alias, key, kind, status, a, b, ha=None, hb=None):
        out.append({"alias": alias, "key": key, "kind": kind, "status": status, "start": a, "end": b,
                    "hs": a if ha is None else ha, "he": b if hb is None else hb})
    a, b = _section(raw, "## Appendix C.")
    n = 0
    for cells, header in _rows(raw, a, b):
        if header:
            continue
        n += 1
        (x, y), (sx, sy) = cells[0], cells[1]
        q = re.search(r'"([^"]+)"', raw[x:y])
        add(f"v0:AppC-{n}", f"appc_{n}", "inference", raw[sx:sy], x, y,
            *((x + q.start(1), x + q.end(1)) if q else ()))
    a, b = _section(raw, "## 7. ")
    for cells, header in _rows(raw, a, b):
        g = re.fullmatch(r"GOV-(\d+)", raw[cells[0][0]:cells[0][1]])
        if header or not g:
            continue
        x, y = cells[1]
        bold = re.match(r"\*\*(.+?)\*\*", raw[x:y])
        add(f"GOV-{g.group(1)}", f"gov_{g.group(1)}", "recommendation", NO_STATUS, x, y,
            *((x + bold.start(1), x + bold.end(1)) if bold else ()))
    for m in re.finditer(r"^### 6\.(\d) .*$", raw, re.M):
        f = re.compile(r"\*\*What would falsify our critique\.\*\* ").search(raw, m.end())
        end = raw.index("\n\n", f.end())
        add(f"v0:Pillar-{m.group(1)}-falsifier", f"pillar_{m.group(1)}", "falsifier", NO_STATUS, f.end(), end)
    a, b = _section(raw, "## 8. ")
    f = re.compile(r"\*\*Falsifiers\.\*\*").search(raw, a, b)
    para = raw.index("\n\n", f.end())
    for m in re.finditer(r"\((\d)\)\s+", raw[f.end():para]):
        x = f.end() + m.end()
        y = x + re.search(r"[;.](\s|$)", raw[x:para + 1]).start()
        add(f"v0:Falsifier-{m.group(1)}", f"falsifier_{m.group(1)}", "falsifier", NO_STATUS, x, y)
    return out


def append_paper(root: Path, commit: str) -> int:
    """Append claims.tsv and excerpts.tsv rows for paper claims not yet registered (by alias)."""
    raw = git_show(commit, PAPER, str(root))
    claims_text = (root / CLAIMS_TSV).read_text()
    ex_text = (root / EXCERPTS_TSV).read_text()
    rows, errs = load_claims(claims_text)
    if errs:
        raise SystemExit("\n".join(errs))
    have = {a for r in rows for a in r["aliases"].split(",")}
    new_c, new_x = [], []
    for c in parse_paper(raw):
        if c["alias"] in have:
            continue
        cid = f"C{len(rows) + len(new_c) + 1:04d}"
        xkey = f"x_{c['key']}"
        new_c.append("\t".join([cid, f"paper_{c['key']}", c["kind"], f"excerpt:{xkey}", c["status"], c["alias"], "-",
                                "pending", address(cid), content_id(norm(raw[c["start"]:c["end"]]))]))
        new_x.append(excerpt_row(xkey, commit, PAPER, raw, c["start"], c["end"], c["hs"], c["he"]))
    (root / CLAIMS_TSV).write_text(claims_text + "".join(l + "\n" for l in new_c))
    (root / EXCERPTS_TSV).write_text(ex_text + "".join(l + "\n" for l in new_x))
    print(f"appended {len(new_c)} paper claims from {commit[:12]}")
    return 0


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
    if len(argv) == 3 and argv[1] == "paper":
        root = Path(__file__).resolve().parent.parent
        commit = subprocess.run(["git", "rev-parse", argv[2]], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        return append_paper(root, commit)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
