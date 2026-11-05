#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0", "blake3==1.0.11", "mwparserfromhell==0.7.2"]
# ///
"""Wikipedia AI-risk corpus: pinned revisions, deterministic plain-Markdown text.

A reference corpus of what English Wikipedia files under AI risk, so that call,
analyst and practitioner language can later be placed against it. Discovery is a
published seed list (the CATEGORIES and SEED_ARTICLES constants below); each
article is pinned to its last revision at or before --as-of. The candidate
dimension list is read from Wikipedia's own headings (HUBS), never written or
judged by a person or a model.

Design constraints, per docs/descartes-spec.md and docs/earnings-call-ai-corpus.md:
  - P3 determinism: no clock, host, user or random id in any output. The as-of
    time is a recorded argument. Rows are sorted; parquet is written by a
    pinned DuckDB on one thread.
  - Verbatim and anchored: every paragraph is a [md_start, md_end) slice of the
    article's converted Markdown, every window a [start_char, end_char) slice of
    a paragraph, each with BLAKE3. `verify` re-converts, re-slices, re-hashes,
    and rebuilds every output into a scratch directory to compare hashes.
  - No model, no labels. Conversion and dimension rules are published here.

    uv run scripts/wp_extract.py pin --as-of 2026-11-04   # discover, pin revisions -> MANIFEST.tsv, seeds.tsv
    uv run scripts/wp_extract.py fetch                    # download pinned wikitext to .wpcorpus/, check BLAKE3
    uv run scripts/wp_extract.py build                    # articles.parquet, sections.tsv, windows.parquet, dimensions-candidate.tsv
    uv run scripts/wp_extract.py verify                   # re-convert, re-slice, re-hash, rebuild and compare
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import blake3
import duckdb
import mwparserfromhell as mw

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "wikipedia-ai-risk"
BULK = ROOT / ".wpcorpus"                     # gitignored: pinned wikitext, re-fetchable from MANIFEST
MANIFEST = CORPUS / "MANIFEST.tsv"
SEEDS_TSV = CORPUS / "seeds.tsv"
CODEBOOK = ROOT / "corpus" / "earnings-calls" / "codebook-v0.1.tsv"
API = "https://en.wikipedia.org/w/api.php"
UA = "anthropic-pbc wikipedia ai-risk corpus research (github.com/ethicalcapital/anthropic-pbc)"

# ---------------------------------------------------------------- published seed
# Categories checked to exist on 2026-11-04. Non-existent candidates that were
# tried and dropped: "Category:Existential risk from artificial general
# intelligence", "Category:Artificial intelligence safety",
# "Category:Artificial intelligence risks".
CATEGORIES = [
    "Category:AI safety",
    "Category:Ethics of artificial intelligence",
    "Category:Existential risk from artificial intelligence",
    "Category:Regulation of artificial intelligence",
]
# Depth 1: the article (namespace 0) members of each category above. Their
# subcategories are recorded in seeds.tsv but not entered; on 2026-11-04 the only
# subcategories are person categories (AI safety advocates, AI safety
# scientists, AI legal scholars), which hold biographies, not risks.
SEED_ARTICLES = [
    "AI alignment",
    "AI capability control",
    "AI safety",
    "AI takeover",
    "AI-assisted targeting",
    "Algorithmic bias",
    "Artificial intelligence",
    "Deepfake",
    "Environmental impact of artificial intelligence",
    "Ethics of artificial intelligence",
    "Existential risk from artificial intelligence",
    "Hallucination (artificial intelligence)",
    "Instrumental convergence",
    "Lethal autonomous weapon",
    "Misinformation",
    "Prompt injection",
    "Regulation of artificial intelligence",
    "Technological unemployment",
]

# Hub articles whose headings become candidate dimensions. "" = every kept
# heading of the article; otherwise only the subtree under that heading path.
HUBS = {
    "AI safety": "",
    "Artificial intelligence": "Ethics > Risks and harm",
    "Ethics of artificial intelligence": "",
    "Existential risk from artificial intelligence": "",
}

# ---------------------------------------------------------------- conversion rules
# Standard end-matter sections (MOS:LAYOUT); dropped with their subsections.
APPENDIX = {
    "references", "notes", "further reading", "external links", "see also",
    "bibliography", "sources", "citations", "footnotes", "notes and references",
    "references and notes", "works cited", "cited sources", "general sources",
    "general and cited sources", "general bibliography", "explanatory notes",
}
DROP_TAGS = {
    "ref", "references", "table", "gallery", "math", "chem", "ce", "score",
    "timeline", "graph", "mapframe", "maplink", "syntaxhighlight", "source",
    "templatestyles", "imagemap", "hiero", "categorytree", "inputbox",
}
DROP_LINK_NS = {"file", "image", "media", "category"}
INTERWIKI = {"wikt", "wiktionary", "commons", "c", "s", "wikisource", "q", "wikiquote",
             "d", "wikidata", "m", "meta", "mw", "n", "wikinews", "b", "wikibooks",
             "v", "wikiversity", "voy", "species", "wikispecies", "w", "wikipedia",
             "wp", "special", "help", "template", "portal", "user", "talk", "draft",
             "module", "mediawiki"}
# Inline templates whose words are prose; every other template is dropped.
KEEP_TEMPLATES = {"nowrap": 1, "nobr": 1, "lang": 2, "transliteration": 2, "keypress": 1,
                  "abbr": 1, "em": 1, "strong": 1, "small": 1, "smaller": 1, "var": 1,
                  "math": 1, "mvar": 1, "tooltip": 1, "nobold": 1, "noitalic": 1}
# Hatnote templates whose targets are the section's "main" articles (dimensions only).
MAIN_TEMPLATES = {"main", "further", "further information", "details", "see also", "main article"}
MAX_WINDOW = 1500   # chars; same ceiling as the earnings-call windows
MIN_WINDOW = 80     # chars; shorter paragraphs (stub list items) get no window
SPLIT = re.compile(r"(?<=[.!?])[ \t]+|\n")


def b3(s: str) -> str:
    return blake3.blake3(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- http
def api(**params) -> dict:
    params.update(format="json", formatversion="2", maxlag="5")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
            if d.get("error", {}).get("code") == "maxlag":
                raise urllib.error.HTTPError(url, 503, "maxlag", {}, None)
            if "error" in d:
                sys.exit(f"API error: {d['error']}")
            time.sleep(0.5)       # politeness; not recorded anywhere
            return d
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == 7:
                raise
            time.sleep(2 ** attempt * 2)
    raise RuntimeError("unreachable")


def norm_title(t: str) -> str:
    t = t.replace("_", " ").strip().lstrip(":").split("#", 1)[0].strip()
    t = re.sub(r"\s+", " ", t)
    return t[:1].upper() + t[1:]


# ---------------------------------------------------------------- pin
def as_of_ts(s: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s + "T00:00:00Z"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", s):
        return s
    sys.exit("--as-of must be YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ (UTC)")


def cmd_pin(as_of: str) -> int:
    ts = as_of_ts(as_of)
    seeds, sources = [], {}          # seeds.tsv rows; title -> set(via)
    for c in CATEGORIES:
        info = api(action="query", titles=c, prop="categoryinfo")["query"]["pages"][0]
        if info.get("missing"):
            seeds.append(("category", c, "", "missing", 0, ""))
            continue
        members, subcats, cont = [], [], {}
        while True:
            d = api(action="query", list="categorymembers", cmtitle=c, cmlimit="max",
                    cmtype="page|subcat", cmprop="title|ns", **cont)
            for m in d["query"]["categorymembers"]:
                (subcats if m["ns"] == 14 else members if m["ns"] == 0 else []).append(m["title"])
            if "continue" not in d:
                break
            cont = d["continue"]
        for t in members:
            sources.setdefault(t, set()).add(c)
        seeds.append(("category", c, c, "ok", len(members), "; ".join(sorted(subcats))))
    for t in SEED_ARTICLES:
        sources.setdefault(t, set()).add("seed")

    rows, pinned = [], {}
    for t in sorted(sources):
        d = api(action="query", titles=t, redirects=1, prop="revisions", rvlimit=1,
                rvstart=ts, rvdir="older", rvslots="main",
                rvprop="ids|timestamp|sha1|size|content")["query"]
        page = d["pages"][0]
        resolved = page.get("title", t)
        if page.get("missing") or "revisions" not in page:
            status = "missing" if page.get("missing") else "no revision at or before as-of"
            if "seed" in sources[t]:
                seeds.append(("article", t, "", status, 0, ""))
            print(f"dropped: {t} ({status})")
            continue
        if page["ns"] != 0:
            print(f"dropped: {t} (namespace {page['ns']})")
            continue
        rev = page["revisions"][0]
        text = rev["slots"]["main"]["content"]
        if "seed" in sources[t]:
            seeds.append(("article", t, resolved, "redirect" if resolved != t else "ok", 1, ""))
        rec = pinned.setdefault(page["pageid"], {
            "title": resolved, "pageid": page["pageid"], "revid": rev["revid"],
            "timestamp": rev["timestamp"], "bytes": len(text.encode("utf-8")),
            "sha1": rev["sha1"], "blake3": b3(text), "via": set()})
        rec["via"] |= sources[t]
        BULK.mkdir(exist_ok=True)
        (BULK / f"{rev['revid']}.wikitext").write_text(text, encoding="utf-8", newline="")

    CORPUS.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["title", "pageid", "revid", "timestamp", "as_of", "bytes", "sha1", "blake3", "via", "url"])
        for r in sorted(pinned.values(), key=lambda r: r["title"]):
            w.writerow([r["title"], r["pageid"], r["revid"], r["timestamp"], ts, r["bytes"], r["sha1"],
                        r["blake3"], "; ".join(sorted(r["via"])), revision_url(r["revid"])])
    with SEEDS_TSV.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["kind", "seed", "resolved", "status", "n_articles", "subcategories_not_entered"])
        w.writerows(sorted(seeds))
    print(f"ok: {len(pinned)} articles pinned at or before {ts} -> {MANIFEST.relative_to(ROOT)}")
    return 0


def revision_url(revid) -> str:
    return (f"{API}?action=query&prop=revisions&revids={revid}"
            "&rvprop=ids|content&rvslots=main&format=json&formatversion=2")


# ---------------------------------------------------------------- fetch
def manifest() -> list[dict[str, str]]:
    with MANIFEST.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def cmd_fetch() -> int:
    BULK.mkdir(exist_ok=True)
    bad = 0
    for m in manifest():
        dst = BULK / f"{m['revid']}.wikitext"
        if not dst.exists():
            page = api(action="query", prop="revisions", revids=m["revid"],
                       rvprop="ids|content", rvslots="main")["query"]["pages"][0]
            dst.write_text(page["revisions"][0]["slots"]["main"]["content"], encoding="utf-8", newline="")
        if b3(dst.read_text(encoding="utf-8")) != m["blake3"]:
            bad += 1
            print(f"FAIL: {m['title']} revid {m['revid']} blake3 mismatch")
    print(f"{'ok' if not bad else 'FAIL'}: {len(manifest())} revisions in {BULK.name}/, {bad} bad")
    return 1 if bad else 0


# ---------------------------------------------------------------- convert
def is_dropped_link(title: str) -> bool:
    t = title.strip().lstrip(":")
    if ":" in t:
        raw = t.split(":", 1)[0].strip()
        pre = raw.lower()
        # interlanguage links are written lower-case ("fr:"); article titles start upper-case
        return pre in DROP_LINK_NS or pre in INTERWIKI or re.fullmatch(r"[a-z]{2,3}(-[a-z]+)?", raw) is not None
    return False


def render(nodes, links: list[str] | None = None, mains: list[str] | None = None) -> str:
    """Wikitext nodes -> plain text. Links reduced to label; templates/refs/tables/files dropped."""
    out = []
    for n in nodes:
        k = type(n).__name__
        if k == "Text":
            out.append(str(n.value))
        elif k == "Wikilink":
            title = str(n.title)
            if is_dropped_link(title):
                continue
            if links is not None and not title.strip().startswith("#"):
                links.append(norm_title(title))
            out.append(render(n.text.nodes, links, mains) if n.text is not None
                       else title.strip().lstrip(":"))
        elif k == "ExternalLink":
            if n.title is not None:              # bare and unlabelled URLs are dropped
                out.append(render(n.title.nodes, links, mains))
        elif k == "Template":
            name = str(n.name).strip().lower().replace("_", " ")
            if mains is not None and name in MAIN_TEMPLATES:
                for p in n.params:          # "{{!}}" is a pipe: keep the target, drop the label
                    v = str(p.value).replace("{{!}}", "|").split("|", 1)[0]
                    if not p.showkey and v.strip():
                        mains.append(norm_title(v))
            if name in KEEP_TEMPLATES:
                pos = [p for p in n.params if not p.showkey]
                i = KEEP_TEMPLATES[name]
                if len(pos) >= i:
                    out.append(render(pos[i - 1].value.nodes, links, mains))
        elif k == "Tag":
            tag = str(n.tag).strip().lower()
            if tag in DROP_TAGS:
                continue
            if tag == "li":
                out.append("\x01")          # list-item marker, resolved per line
            elif tag in ("dd", "dt", "hr"):
                out.append("")
            elif tag == "br":
                out.append(" ")
            elif n.contents is not None:
                out.append(render(n.contents.nodes, links, mains))
        elif k == "HTMLEntity":
            out.append(n.normalize())
        elif k == "Heading":
            out.append(render(n.title.nodes, links, mains))
        # Comment, Argument, anything else: dropped
    return "".join(out)


def clean_line(s: str) -> str:
    depth = 0
    s = s.strip()
    while s.startswith("\x01"):
        depth += 1
        s = s[1:].lstrip()
    s = s.replace("\x01", "").replace("\xa0", " ").replace("​", "")
    s = re.sub(r"__[A-Z]+__", "", s)
    s = re.sub(r"'{2,}", "", s)                    # bold/italic quotes the parser left unbalanced
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\( *[,;]? *\)", "", s)           # parentheses emptied by dropped templates
    s = re.sub(r" +([.,;:!?)])", r"\1", s)
    s = re.sub(r"\( +", "(", s)
    s = re.sub(r"[ \t]+", " ", s).strip()
    if depth and s:
        s = "  " * (depth - 1) + "- " + s
    return s


def blocks_of(text: str) -> list[str]:
    out, cur = [], []
    for line in text.split("\n"):
        line = clean_line(line)
        if line:
            cur.append(line)
        elif cur:
            out.append("\n".join(cur))
            cur = []
    if cur:
        out.append("\n".join(cur))
    return [b for b in out if re.search(r"\w", b)]


def convert(title: str, wikitext: str) -> dict:
    """-> {markdown, sections:[{level, path, kept, blocks:[(start, end, text)], links, mains}]}."""
    code = mw.parse(wikitext)
    raw = [{"level": 1, "heading": "(lead)", "nodes": []}]
    for n in code.nodes:
        if type(n).__name__ == "Heading":
            raw.append({"level": n.level, "heading": clean_line(render(n.title.nodes)), "nodes": []})
        else:
            raw[-1]["nodes"].append(n)
    md, secs, stack = [f"# {title}"], [], []      # stack: (level, heading, kept)
    for r in raw:
        if r["heading"] == "(lead)":
            path, kept = "(lead)", True
        else:
            while stack and stack[-1][0] >= r["level"]:
                stack.pop()
            kept = r["heading"].lower() not in APPENDIX and all(s[2] for s in stack)
            stack.append((r["level"], r["heading"], kept))
            path = " > ".join(s[1] for s in stack)
        links, mains = [], []
        text = render(r["nodes"], links, mains)
        sec = {"level": r["level"], "path": path, "heading": r["heading"], "kept": kept,
               "links": links, "mains": mains, "blocks": []}
        if kept:
            if r["heading"] != "(lead)":
                md.append("#" * r["level"] + " " + r["heading"])
            for b in blocks_of(text):
                md.append(b)
                sec["blocks"].append(b)
        secs.append(sec)
    markdown = "\n\n".join(md) + "\n"
    # anchor each block in the markdown, scanning forward (blocks never overlap)
    pos = 0
    for sec in secs:
        anchored = []
        for b in sec["blocks"]:
            s = markdown.index(b, pos)
            anchored.append((s, s + len(b), b))
            pos = s + len(b)
        sec["blocks"] = anchored
    return {"markdown": markdown, "sections": secs}


def windows_for(p: str) -> list[tuple[int, int]]:
    """Paragraph-sized windows: the whole paragraph, or sentence-packed chunks <= MAX_WINDOW."""
    if len(p) < MIN_WINDOW:
        return []
    if len(p) <= MAX_WINDOW:
        return [(0, len(p))]
    units, pos = [], 0
    for m in SPLIT.finditer(p):
        units.append((pos, m.start()))
        pos = m.end()
    units.append((pos, len(p)))
    pieces = []
    for s, e in units:                       # hard-split any single over-long sentence at a space
        while e - s > MAX_WINDOW:
            cut = p.rfind(" ", s, s + MAX_WINDOW)
            cut = cut if cut > s else s + MAX_WINDOW
            pieces.append((s, cut))
            s = cut + 1 if p[cut:cut + 1] == " " else cut
        if e > s:
            pieces.append((s, e))
    out: list[list[int]] = []
    for s, e in pieces:
        if out and e - out[-1][0] <= MAX_WINDOW:
            out[-1][1] = e
        else:
            out.append([s, e])
    return [(s, e) for s, e in out]


# ---------------------------------------------------------------- build
def codebook_ids() -> list[str]:
    with CODEBOOK.open(newline="") as f:
        return [r["id"] for r in csv.DictReader(f, delimiter="\t")]


def literal_match(heading: str, ids: list[str]) -> str:
    """Codebook ids whose own text (underscores as spaces) appears as a whole word in the heading."""
    h = heading.lower()
    return ",".join(i for i in ids if re.search(r"\b" + re.escape(i.replace("_", " ")) + r"\b", h))


def build_to(out: Path) -> dict:
    rows = manifest()
    in_corpus = {r["title"] for r in rows}
    ids = codebook_ids()
    paras, wins, sects, dims = [], [], [], []
    for m in rows:
        src = BULK / f"{m['revid']}.wikitext"
        if not src.exists():
            sys.exit(f"missing {src.name}: run `fetch` first")
        wt = src.read_text(encoding="utf-8")
        if b3(wt) != m["blake3"]:
            sys.exit(f"{m['title']} revid {m['revid']}: wikitext blake3 mismatch")
        title, pageid, revid = m["title"], int(m["pageid"]), int(m["revid"])
        conv = convert(title, wt)
        mdh = b3(conv["markdown"])
        pn = 0
        hub = HUBS.get(title)
        for si, sec in enumerate(conv["sections"]):
            n_chars = sum(e - s for s, e, _ in sec["blocks"])
            sects.append((title, revid, si, sec["level"], sec["path"], int(sec["kept"]),
                          len(sec["blocks"]), n_chars))
            for s, e, text in sec["blocks"]:
                pn += 1
                ph = b3(text)
                kind = "list" if text.lstrip().startswith("- ") else "prose"
                paras.append((title, pageid, revid, sec["path"], sec["level"], pn, kind,
                              s, e, mdh, ph, text))
                for ws, we in windows_for(text):
                    seg = text[ws:we]
                    wid = b3(f"{title}|{revid}|{pn}|{ws}|{we}|{ph}")[:16]
                    wins.append((wid, title, pageid, revid, sec["path"], pn, ph, ws, we, b3(seg), seg))
            if (hub is not None and sec["kept"] and sec["path"] != "(lead)"
                    and (hub == "" or sec["path"].startswith(hub + " > "))):
                links = list(dict.fromkeys(sec["links"]))
                mains = list(dict.fromkeys(sec["mains"]))
                dims.append((title, revid, sec["level"], sec["path"], sec["heading"],
                             " | ".join(mains), " | ".join(links),
                             sum(1 for t in dict.fromkeys(mains + links) if t in in_corpus),
                             literal_match(sec["heading"], ids), "candidate: not reviewed"))

    con = duckdb.connect()
    con.execute("SET threads=1")
    con.execute("""CREATE TABLE p (title VARCHAR, pageid BIGINT, revid BIGINT, section_path VARCHAR,
                   heading_level INT, paragraph_number INT, kind VARCHAR, md_start INT, md_end INT,
                   markdown_blake3 VARCHAR, paragraph_blake3 VARCHAR, text VARCHAR)""")
    con.executemany("INSERT INTO p VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", paras)
    con.execute("""CREATE TABLE w (window_id VARCHAR, title VARCHAR, pageid BIGINT, revid BIGINT,
                   section_path VARCHAR, paragraph_number INT, paragraph_blake3 VARCHAR,
                   start_char INT, end_char INT, window_blake3 VARCHAR, text VARCHAR)""")
    con.executemany("INSERT INTO w VALUES (?,?,?,?,?,?,?,?,?,?,?)", wins)
    if con.execute("SELECT count(*) - count(DISTINCT window_id) FROM w").fetchone()[0]:
        sys.exit("window_id collision")
    opts = "(FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 8192)"
    con.execute(f"COPY (SELECT * FROM p ORDER BY title, paragraph_number) TO '{out / 'articles.parquet'}' {opts}")
    con.execute(f"COPY (SELECT * FROM w ORDER BY title, paragraph_number, start_char) "
                f"TO '{out / 'windows.parquet'}' {opts}")
    with (out / "sections.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["title", "revid", "section_index", "heading_level", "heading_path", "kept",
                    "n_paragraphs", "n_chars"])
        w.writerows(sorted(sects, key=lambda r: (r[0], r[2])))
    with (out / "dimensions-candidate.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["source_title", "revid", "heading_level", "heading_path", "heading",
                    "main_articles", "linked_articles", "n_linked_in_corpus",
                    "codebook_v0_1_literal_match", "status"])
        w.writerows(dims)                     # document order within each hub; hubs sorted by title
    return {"articles": len(rows), "paragraphs": len(paras), "windows": len(wins),
            "sections": len(sects), "dimensions": len(dims)}


OUTPUTS = ["articles.parquet", "windows.parquet", "sections.tsv", "dimensions-candidate.tsv"]


def cmd_build() -> int:
    n = build_to(CORPUS)
    print(f"ok: {n['articles']} articles, {n['sections']} sections, {n['paragraphs']} paragraphs, "
          f"{n['windows']} windows, {n['dimensions']} candidate dimensions")
    for f in OUTPUTS:
        print(f"  {f} blake3 {b3file(CORPUS / f)}")
    return cmd_verify()


def b3file(p: Path) -> str:
    return blake3.blake3(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------- verify
def cmd_verify() -> int:
    for m in manifest():
        p = BULK / f"{m['revid']}.wikitext"
        if not p.exists():
            print(f"FAIL: missing {p.relative_to(ROOT)}; run uv run scripts/wp_extract.py fetch")
            return 1
    bad = 0
    con = duckdb.connect()
    paras = con.execute(f"SELECT title, revid, paragraph_number, md_start, md_end, markdown_blake3, "
                        f"paragraph_blake3, text FROM '{CORPUS / 'articles.parquet'}'").fetchall()
    md = {}
    for m in manifest():
        wt = (BULK / f"{m['revid']}.wikitext").read_text(encoding="utf-8")
        if b3(wt) != m["blake3"]:
            bad += 1
            print(f"FAIL wikitext {m['title']}")
        md[(m["title"], int(m["revid"]))] = convert(m["title"], wt)["markdown"]
    pmap = {}
    for title, revid, pn, s, e, mdh, ph, text in paras:
        doc = md.get((title, revid))
        if doc is None or b3(doc) != mdh or doc[s:e] != text or b3(text) != ph:
            bad += 1
            print(f"FAIL paragraph {title} #{pn}")
        pmap[(title, revid, pn)] = (ph, text)
    n = 0
    for wid, title, revid, pn, ph, s, e, wh, text in con.execute(
            f"SELECT window_id, title, revid, paragraph_number, paragraph_blake3, start_char, end_char, "
            f"window_blake3, text FROM '{CORPUS / 'windows.parquet'}'").fetchall():
        n += 1
        p = pmap.get((title, revid, pn))
        if p is None or p[0] != ph or p[1][s:e] != text or b3(text) != wh:
            bad += 1
            print(f"FAIL window {wid}")
    with tempfile.TemporaryDirectory() as td:     # rebuild from scratch and compare bytes
        build_to(Path(td))
        for f in OUTPUTS:
            a, b = b3file(CORPUS / f), b3file(Path(td) / f)
            if a != b:
                bad += 1
                print(f"FAIL rebuild {f}: committed {a} != rebuilt {b}")
    print(f"{'ok' if not bad else 'FAIL'}: {len(md)} articles re-converted, {len(paras)} paragraphs, "
          f"{n} windows re-sliced and re-hashed, {len(OUTPUTS)} outputs rebuilt and compared, {bad} bad")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["pin", "fetch", "build", "verify"])
    ap.add_argument("--as-of", help="pin: UTC date YYYY-MM-DD (= 00:00:00Z) or YYYY-MM-DDTHH:MM:SSZ")
    a = ap.parse_args()
    if a.cmd == "pin":
        if not a.as_of:
            sys.exit("pin requires --as-of")
        return cmd_pin(a.as_of)
    return {"fetch": cmd_fetch, "build": cmd_build, "verify": cmd_verify}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
