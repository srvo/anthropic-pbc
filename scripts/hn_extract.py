#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0", "blake3==1.0.11"]
# ///
"""Hacker News focused AI corpus: Anthropic, and AI security incidents. IDs only.

Source: open-index/hacker-news on Hugging Face (ODC-BY), monthly parquet files
pinned to one dataset commit in corpus/hacker-news/MANIFEST.tsv (path, bytes,
SHA-256 = the LFS oid Hugging Face publishes). Bulk bytes and comment text live
in the gitignored .hncorpus/ and are never committed: HN commenters are mostly
private individuals, so the repository holds item ids, character offsets and
BLAKE3 hashes, and anyone can rebuild the text from the pinned source.

Two focused sets, each a published regex (no model):
  anthropic    "Anthropic" (not the anthropic principle / reasoning / argument),
               and "Claude" from 2023-03-01 (the model's release), minus common
               first-name collocations.
  ai_security  a security term (CVE, breach, exfiltration, vulnerability, exploit,
               malware, zero-day, RCE, backdoor, jailbreak, leaked weights/keys/prompt,
               ...) in a window that also holds an AI term, or "prompt injection"
               on its own. ("jailbreak" needs the AI term: phones and Kindles are
               jailbroken too; "hacked" is excluded: "hacked together".)

Unit: the earnings-call window (match sentence +/- 1, merged, clipped at 1,500
chars) over the comment's normalised text. Normalisation: <p> -> blank line,
other tags dropped, HTML entities unescaped. Comments that are deleted or dead
are excluded from numerator and denominator alike.

    uv run scripts/hn_extract.py pin      # write MANIFEST.tsv from the pinned HF revision
    uv run scripts/hn_extract.py fetch    # download + SHA-256 check into .hncorpus/
    uv run scripts/hn_extract.py build    # months.tsv, windows.parquet (+ local text)
    uv run scripts/hn_extract.py verify   # re-normalise, re-slice, re-hash every window
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import blake3
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ec_extract import ANY_RE as AI_RE  # noqa: E402  (the earnings-call AI term regex)

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "hacker-news"
BULK = ROOT / ".hncorpus"                      # gitignored: source parquet + local text
MANIFEST = CORPUS / "MANIFEST.tsv"
REPO = "open-index/hacker-news"
REVISION = "c54ced5973b95d80cd934b8921f44ec8d87c3cd1"
FIRST_MONTH, LAST_MONTH = "2021-01", "2026-08"   # Anthropic founded 2021; archive ends Aug 2026
CLAUDE_FROM = "2023-03-01"
UA = "anthropic-pbc hacker-news corpus research (github.com/ethicalcapital/anthropic-pbc)"

ANTHROPIC = re.compile(
    r"(?i:\banthropic(?:'s)?\b)(?!\s+(?i:principle|reasoning|argument|bias|selection|shadow|explanation))")
CLAUDE = re.compile(
    r"\bClaude\b(?!\s+(?:Shannon|Monet|Debussy|L[eé]vi|Van\b|Elwood|Bernard|Chabrol|Rains|Lorrain|Cahun|Makelele|Steele|Frollo))")
SECURITY = re.compile(
    r"\bCVE-\d{4}-\d{4,}|\bCVEs?\b|\bRCE\b|\b0-?days?\b"
    r"|(?i:\bdata breach(?:es)?\b|\bbreach(?:ed|es)?\b|\bexfiltrat\w*|\bvulnerabilit(?:y|ies)\b"
    r"|\bexploit(?:s|ed|able|ing)?\b|\bmalware\b|\bsupply[- ]chain attacks?\b|\bzero[- ]days?\b"
    r"|\bbackdoor(?:s|ed)?\b|\bsecurity (?:incident|breach|hole|flaw)s?\b|\bjailbr(?:eak|eaks|eaking|eaked|oken)\b"
    r"|\bdata leaks?\b|\bleak(?:s|ed)? (?:the |its |their )?(?:system prompt|weights|model weights|source code|api keys?|keys|credentials|secrets|user data|training data)\b)")
AI_ATTACK = re.compile(r"(?i:\bprompt[- ]injections?\b)")
SENT_END = re.compile(r"(?<=[.!?])\s+")
MAX_WINDOW, CLIP_PAD = 1500, 600
PRE_FILTER = (r"(?i)anthropic|claude|cve|rce|0-?day|breach|exfiltrat|vulnerab|exploit|malware"
              r"|supply.chain|zero.day|backdoor|security|leak|prompt.injection|jailbr")


def connect() -> duckdb.DuckDBPyConnection:
    """DuckDB pinned to UTC: the source `time` column carries a zone, and strftime
    otherwise formats in the build host's zone, which would make output host-dependent."""
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    return con


def b3(s: str) -> str:
    return blake3.blake3(s.encode("utf-8")).hexdigest()


TAG = re.compile(r"<[^>]*>")


def normalise(raw: str) -> str:
    return html.unescape(TAG.sub("", raw.replace("<p>", "\n\n")))


def months() -> list[dict[str, str]]:
    with MANIFEST.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# ---------------------------------------------------------------- pin / fetch
def cmd_pin() -> int:
    url = f"https://huggingface.co/api/datasets/{REPO}/tree/{REVISION}/data?recursive=true"
    tree = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60))
    rows = []
    for x in tree:
        m = re.fullmatch(r"data/\d{4}/(\d{4}-\d{2})\.parquet", x["path"])
        if x["type"] == "file" and m and FIRST_MONTH <= m.group(1) <= LAST_MONTH:
            rows.append((m.group(1), x["path"], f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{x['path']}",
                         str(x["lfs"]["size"]), x["lfs"]["oid"]))
    rows.sort()
    CORPUS.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["month", "path", "url", "bytes", "sha256"])
        w.writerows(rows)
    print(f"ok: {len(rows)} monthly files pinned at {REPO}@{REVISION[:8]} -> {MANIFEST.relative_to(ROOT)}")
    return 0


def _fetch_one(r: dict[str, str]) -> str:
    dst = BULK / r["path"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        tmp = dst.with_suffix(".part")
        with urllib.request.urlopen(urllib.request.Request(r["url"], headers={"User-Agent": UA}), timeout=120) as s, \
                tmp.open("wb") as f:
            while chunk := s.read(1 << 22):
                f.write(chunk)
        tmp.rename(dst)
    h = hashlib.sha256()
    with dst.open("rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    ok = str(dst.stat().st_size) == r["bytes"] and h.hexdigest() == r["sha256"]
    return f"{'ok' if ok else 'FAIL'}: {r['month']}"


def cmd_fetch() -> int:
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(_fetch_one, months()))
    bad = [x for x in res if x.startswith("FAIL")]
    print(f"{len(res) - len(bad)} ok, {len(bad)} failed" + ("".join("\n  " + b for b in bad)))
    return 1 if bad else 0


# ---------------------------------------------------------------- windows
def spans(content: str, hit_re: re.Pattern) -> list[tuple[int, int]]:
    """Merged sentence windows (match sentence +/- 1) around hit_re, clipped like ec_extract."""
    bounds, pos = [], 0
    for m in SENT_END.finditer(content):
        bounds.append((pos, m.start()))
        pos = m.end()
    bounds.append((pos, len(content)))
    hits = sorted({i for i, (s, e) in enumerate(bounds) if hit_re.search(content, s, e)})
    merged: list[list[int]] = []
    for i in hits:
        lo, hi = max(i - 1, 0), min(i + 1, len(bounds) - 1)
        if merged and lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    out = []
    for lo, hi in merged:
        s, e = bounds[lo][0], bounds[hi][1]
        if e - s <= MAX_WINDOW:
            out.append((s, e))
            continue
        pieces: list[list[int]] = []
        for m in hit_re.finditer(content, s, e):
            a, b = max(m.start() - CLIP_PAD, s), min(m.end() + CLIP_PAD, e)
            if pieces and a <= pieces[-1][1]:
                pieces[-1][1] = b
            else:
                pieces.append([a, b])
        for a, b in pieces:
            if a > s:
                a = content.find(" ", a, b) + 1 or a
            if b < e and content.rfind(" ", a, b) > a:
                b = content.rfind(" ", a, b)
            out.append((a, b))
    return out


def windows_for(text: str, day: str) -> list[tuple[str, int, int, str]]:
    """(set, start, end, families) for one normalised comment."""
    res = []
    anth = ANTHROPIC if day < CLAUDE_FROM else re.compile(f"{ANTHROPIC.pattern}|{CLAUDE.pattern}")
    for s, e in spans(text, anth):
        seg = text[s:e]
        fam = [k for k, r in (("anthropic", ANTHROPIC), ("claude", CLAUDE)) if r.search(seg)
               and (k == "anthropic" or day >= CLAUDE_FROM)]
        if fam:
            res.append(("anthropic", s, e, ";".join(fam)))
    sec = re.compile(f"{SECURITY.pattern}|{AI_ATTACK.pattern}")
    for s, e in spans(text, sec):
        seg = text[s:e]
        fam = ["ai_attack"] if AI_ATTACK.search(seg) else []
        if SECURITY.search(seg) and AI_RE.search(seg):
            fam.append("security_ai")
        if fam:
            res.append(("ai_security", s, e, ";".join(fam)))
    return res


def scan(con: duckdb.DuckDBPyConnection, path: Path):
    return con.execute(
        f"""SELECT id, strftime(time, '%Y-%m-%d') AS day, text FROM '{path}'
            WHERE type = 2 AND coalesce(deleted, 0) = 0 AND coalesce(dead, 0) = 0
              AND text IS NOT NULL AND regexp_matches(text, ?) ORDER BY id""", [PRE_FILTER]).fetchall()


def cmd_build() -> int:
    con = connect()
    mrows, wrows, trows = [], [], []
    for r in months():
        path = BULK / r["path"]
        n_all = con.execute(f"""SELECT count(*) FROM '{path}' WHERE type = 2
            AND coalesce(deleted, 0) = 0 AND coalesce(dead, 0) = 0 AND text IS NOT NULL""").fetchone()[0]
        last = con.execute(f"SELECT strftime(max(time), '%Y-%m-%d %H:%M:%S') FROM '{path}' WHERE type = 2").fetchone()[0]
        per = {"anthropic": set(), "ai_security": set()}
        for item_id, day, raw in scan(con, path):
            text = normalise(raw)
            ws = windows_for(text, day)
            if not ws:
                continue
            tb = b3(text)
            trows.append((item_id, text))
            for st, s, e, fam in ws:
                per[st].add(item_id)
                wid = b3(f"{item_id}:{st}:{s}:{e}")[:16]
                wrows.append((wid, st, item_id, day, s, e, e - s, fam, b3(text[s:e]), tb))
        mrows.append((r["month"], n_all, len(per["anthropic"]), len(per["ai_security"]), last))
        print(f"{r['month']}: {n_all:>7} comments  anthropic {len(per['anthropic']):>6}  ai_security {len(per['ai_security']):>5}",
              flush=True)
    with (CORPUS / "months.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["month", "n_comments", "n_anthropic_comments", "n_ai_security_comments", "last_comment_utc"])
        w.writerows(mrows)
    con.execute("""CREATE TABLE w (window_id VARCHAR, "set" VARCHAR, item_id UBIGINT, day DATE,
        start_char INTEGER, end_char INTEGER, n_chars INTEGER, families VARCHAR, window_blake3 VARCHAR,
        comment_blake3 VARCHAR)""")
    con.executemany("INSERT INTO w VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", wrows)
    con.execute(f"""COPY (SELECT * FROM w ORDER BY "set", item_id, start_char)
        TO '{CORPUS / "windows.parquet"}' (FORMAT parquet, COMPRESSION zstd)""")
    # local only (gitignored): comment text, and the classifier input per set
    con.execute("CREATE TABLE t (item_id UBIGINT, text VARCHAR)")
    con.executemany("INSERT INTO t VALUES (?, ?)", sorted(set(trows)))
    con.execute(f"COPY (SELECT * FROM t ORDER BY item_id) TO '{BULK / 'comments-text.parquet'}' (FORMAT parquet)")
    for st in ("anthropic", "ai_security"):
        con.execute(f"""COPY (SELECT w.window_id, substr(t.text, w.start_char + 1, w.n_chars) AS text
            FROM w JOIN t USING (item_id) WHERE w."set" = '{st}' ORDER BY w.window_id)
            TO '{BULK / f"units-{st}.parquet"}' (FORMAT parquet)""")
    print(f"ok: {len(wrows)} windows on {len(set(trows))} comments -> {(CORPUS / 'windows.parquet').relative_to(ROOT)}")
    return cmd_verify()


def cmd_verify() -> int:
    need = [(BULK / r["path"], "uv run scripts/hn_extract.py fetch") for r in months()]
    need.append((BULK / "comments-text.parquet", "uv run scripts/hn_extract.py build"))
    for p, fix in need:
        if not p.exists():
            print(f"FAIL: missing {p.relative_to(ROOT)}; run {fix}")
            return 1
    con = connect()
    text = dict(con.execute(f"SELECT item_id, text FROM '{BULK / 'comments-text.parquet'}'").fetchall())
    raw = {}
    for r in months():
        raw.update(con.execute(f"""SELECT id, text FROM '{BULK / r['path']}' WHERE id IN
            (SELECT item_id FROM '{CORPUS / 'windows.parquet'}')""").fetchall())
    bad = 0
    for item_id, s, e, wb, cb in con.execute(f"""SELECT item_id, start_char, end_char, window_blake3, comment_blake3
            FROM '{CORPUS / 'windows.parquet'}'""").fetchall():
        t = normalise(raw[item_id])
        if t != text[item_id] or b3(t) != cb or b3(t[s:e]) != wb:
            bad += 1
    print(f"verify: {bad} mismatches")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["pin", "fetch", "build", "verify"])
    a = ap.parse_args()
    return {"pin": cmd_pin, "fetch": cmd_fetch, "build": cmd_build, "verify": cmd_verify}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
