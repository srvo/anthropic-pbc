#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["blake3==1.0.11"]
# ///
"""Pinned snapshot of Epoch AI's public datasets (https://epoch.ai/data), for later joins.

Source: every download listed under "Download our data" on https://epoch.ai/data
(except Cyber vulnerabilities, rebuilt separately in corpus/cve/), plus the
standalone files a dataset page offers that its bundle does not contain
(EXTRAS below). Epoch AI data is CC BY 4.0; credit strings are in
corpus/epoch/CITATIONS.tsv, taken verbatim from each dataset page.

Epoch's URLs are not versioned and the bundles are regenerated (zip member
timestamps change with each regeneration), so the URL is not the pin: the saved
bytes are. `pin` downloads every file once into the gitignored .epochcorpus/
and records bytes, SHA-256 and BLAKE3 in corpus/epoch/MANIFEST.tsv, with the
"Updated" date Epoch shows for the file. A later download of the same URL will
usually not match; re-pinning moves the snapshot.

`build` unpacks each pinned file (zip members, gz payload, plain CSV) and writes
corpus/epoch/inventory.tsv, one row per member: rows, columns, column names,
BLAKE3 of the member bytes, and the count of rows with "anthropic" (any case)
in any cell. CSV members under COMMIT_LIMIT bytes are also copied verbatim to
corpus/epoch/<dataset>/, except third-party benchmark tables (*_external.csv,
which keep their original licences). The ChatGPT-usage dataset is excluded
entirely (SKIP_LABELS): YouGov's notice forbids AI ingestion. No clock: the as-of date is the recorded argument, outputs are
sorted, and `verify` rebuilds in memory and compares BLAKE3 hashes.

    uv run scripts/epoch_data.py pin --as-of 2026-11-04   # download + hash -> MANIFEST.tsv, CITATIONS.tsv
    uv run scripts/epoch_data.py build                    # inventory.tsv + verbatim small tables
    uv run scripts/epoch_data.py verify                   # re-hash pins, rebuild in memory, compare
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import io
import json
import re
import shutil
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import blake3

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "epoch"
BULK = ROOT / ".epochcorpus"                   # gitignored: every pinned download, byte for byte
MANIFEST = CORPUS / "MANIFEST.tsv"
CITATIONS = CORPUS / "CITATIONS.tsv"
INVENTORY = CORPUS / "inventory.tsv"
BASE = "https://epoch.ai"
UA = "anthropic-pbc epoch-data snapshot research (github.com/ethicalcapital/anthropic-pbc)"
PAUSE = 2.0                                    # seconds between requests to epoch.ai
COMMIT_LIMIT = 5_000_000                       # CSV tables at or above this many bytes stay in .epochcorpus/
ANTHROPIC = re.compile(r"(?i)anthropic")

# (dataset id = Epoch page slug, label on /data, page holding the citation, bundle path on /data)
DATASETS = [
    ("ai-chip-components",        "AI chip components",          "/data/ai-chip-components",        "/data/ai_chip_components.zip"),
    ("ai-chip-imports",           "AI chip imports",             "/data/ai-chip-imports",           "/data/ai_chip_trade/ai_chip_trade.zip"),
    ("ai-chip-owners",            "AI chip owners",              "/data/ai-chip-owners",            "/data/ai_chip_owners.zip"),
    ("ai-chip-sales",             "AI chip sales",               "/data/ai-chip-sales",             "/data/ai_chip_sales.zip"),
    ("ai-chip-users",             "AI chip users",               "/data/ai-chip-users",             "/data/ai_chip_users.zip"),
    ("ai-companies",              "AI companies",                "/data/ai-companies",              "/data/ai_companies.zip"),
    ("ai-data-centers",           "AI data centers",             "/data/ai-data-centers",           "/data/data_centers/data_centers.zip"),
    ("ai-models",                 "AI models",                   "/data/ai-models",                 "/data/ai_models.zip"),
    ("arxiv",                     "AI use in math research",     "/data/arxiv",                     "/data/math_acknowledgment_trends_monthly.csv.gz"),
    ("ai-research-use",           "AI use in research",          "/data/ai-research-use",           "/data/ai_research_use_monthly.csv"),
    ("benchmarks",                "Capabilities & benchmarking", "/benchmarks/use-this-data",       "/data/benchmark_data.zip"),
    ("frontier-lab-hiring",       "Frontier Lab Hiring",         "/data/frontier-lab-hiring",       "/data/frontier_lab_hiring.zip"),
    ("gpu-clusters",              "GPU clusters",                "/data/gpu-clusters",              "/data/gpu_clusters.csv"),
    ("machine-learning-hardware", "Machine learning hardware",   "/data/machine-learning-hardware", "/data/ml_hardware.zip"),
    ("polling",                   "Polling on AI usage",         "/data/polling",                   "/data/polling/polling_on_ai_usage_jul_2026.csv"),
]
SKIP_LABELS = {
    "Cyber vulnerabilities",   # corpus/cve/ rebuilds it from cvelistV5
    "ChatGPT usage",           # its workbook reads "AI not authorized by YouGov is not authorized
}                              # to ingest or scrape this data." Not downloaded, not pinned.

# Files a dataset page lists under Downloads that its /data bundle does not contain.
# (Per-table CSVs that duplicate a bundle member are not pinned twice. The
# ChatGPT-usage CSVs duplicate the workbook's sheets and carry the same notice.)
EXTRAS = {
    "ai-research-use": ["/data/ai_research_use_cases_monthly.csv", "/data/ai_research_tools_monthly.csv"],
    "polling": ["/data/polling/polling_on_ai_usage_jul_2026_microdata.csv"],
}

NOT_PARSED: dict[str, str] = {}

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun",
                                      "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
LINK_RE = re.compile(r"\[LINK ([^\]]+)\]\s*([^\[]*?)\s+(ZIP|CSV|GZ|XLSX)\s*,\s*Updated\s+([A-Z][a-z]{2})[a-z]*\.?\s+(\d{1,2}),\s+(\d{4})")


# ---------------------------------------------------------------- helpers
def b3_bytes(b: bytes) -> str:
    return blake3.blake3(b).hexdigest()


def hash_file(p: Path) -> tuple[int, str, str]:
    s, b = hashlib.sha256(), blake3.blake3()
    with p.open("rb") as f:
        while chunk := f.read(1 << 22):
            s.update(chunk)
            b.update(chunk)
    return p.stat().st_size, s.hexdigest(), b.hexdigest()


def tsv(header: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def read_tsv(p: Path) -> list[dict[str, str]]:
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def get(url: str) -> bytes:
    time.sleep(PAUSE)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
        return r.read()


def page_text(raw: bytes) -> str:
    """Visible text with each download link marked as [LINK href]."""
    s = raw.decode("utf-8")
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    s = re.sub(r'<a [^>]*href="([^"]*\.(?:zip|csv|gz|xlsx))"[^>]*>', r" [LINK \1] ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(re.sub(r"\s+", " ", s))


def download_links(text: str) -> dict[str, tuple[str, str]]:
    """href -> (label, ISO updated date) for every 'label TYPE , Updated Mon. D, YYYY' link."""
    out = {}
    for href, label, _, mon, day, year in LINK_RE.findall(text):
        out.setdefault(href, (label.strip(), f"{year}-{MONTHS[mon.lower()]:02d}-{int(day):02d}"))
    return out


def local_path(slug: str, href: str) -> str:
    return f"{slug}/{href.rsplit('/', 1)[1]}"


# ---------------------------------------------------------------- pin
def cmd_pin(as_of: str) -> int:
    pages = BULK / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    index = get(BASE + "/data")
    (pages / "data.html").write_bytes(index)
    listed = download_links(page_text(index))
    by_label = {lab: (href, upd) for href, (lab, upd) in listed.items()}
    expected = {d[1] for d in DATASETS}
    unknown = sorted(set(by_label) - expected - SKIP_LABELS)
    if unknown:
        sys.exit(f"FAIL: /data lists downloads not in DATASETS: {unknown}")
    man_rows, cite_rows, problems = [], [], []
    for slug, label, page, bundle in DATASETS:
        if label not in by_label or by_label[label][0] != bundle:
            problems.append(f"{label}: /data no longer links {bundle} (found {by_label.get(label)})")
            continue
        raw = get(BASE + page)
        (pages / f"{slug}.html").write_bytes(raw)
        text = page_text(raw)
        m = re.search(r"Citation (.+? \[online resource\]\. Accessed [^.]+\.)", text)
        if not m:
            problems.append(f"{label}: no citation on {page}")
        else:
            cite = m.group(1).strip()
            if not cite.endswith(f"Accessed {int(as_of[8:])} {list(MONTHS)[int(as_of[5:7]) - 1].title()} {as_of[:4]}."):
                problems.append(f"{label}: page access date in citation differs from --as-of ({cite[-24:]})")
            cite_rows.append([slug, label, BASE + page, cite])
        on_page = download_links(text)
        files = [(bundle, "bundle", by_label[label][1])]
        for href in EXTRAS.get(slug, []):
            if href not in on_page:
                problems.append(f"{label}: {page} no longer links {href}")
                continue
            files.append((href, "page-file", on_page[href][1]))
        for href, role, updated in files:
            dst = BULK / local_path(slug, href)
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                data = get(BASE + href)
            except Exception as e:                      # noqa: BLE001  record and continue
                problems.append(f"{label}: download failed {href}: {e}")
                continue
            dst.write_bytes(data)
            size, sha, b3 = hash_file(dst)
            man_rows.append([slug, role, BASE + href, local_path(slug, href), size, sha, b3, as_of, updated])
            print(f"pinned {local_path(slug, href)}  {size} bytes  updated {updated}")
    CORPUS.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_bytes(tsv(["dataset", "role", "url", "path", "bytes", "sha256", "blake3", "as_of", "updated"],
                             sorted(man_rows, key=lambda r: r[3])))
    CITATIONS.write_bytes(tsv(["dataset", "name", "page", "citation"], sorted(cite_rows)))
    for p in problems:
        print(f"FAIL: {p}")
    print(f"{'ok' if not problems else 'FAIL'}: {len(man_rows)} files pinned -> {MANIFEST.relative_to(ROOT)}")
    return 1 if problems else 0


def check_pins() -> list[str]:
    bad = []
    for r in read_tsv(MANIFEST):
        p = BULK / r["path"]
        if not p.exists():
            bad.append(f"missing {r['path']}")
            continue
        size, sha, b3 = hash_file(p)
        if str(size) != r["bytes"] or sha != r["sha256"] or b3 != r["blake3"]:
            bad.append(f"hash mismatch {r['path']}")
    return bad


# ---------------------------------------------------------------- build
def members(p: Path):
    """(member name, bytes) for every file inside a pinned download, in name order."""
    if p.suffix == ".zip":
        with zipfile.ZipFile(p) as z:
            for name in sorted(i.filename for i in z.infolist() if not i.is_dir()):
                yield name, z.read(name)
    elif p.suffix == ".gz":
        yield p.name[:-3], gzip.decompress(p.read_bytes())
    else:
        yield p.name, p.read_bytes()


def table_stats(data: bytes) -> tuple[int, list[str], int]:
    """(data rows, header, rows with 'anthropic' in any cell). Leading '#' comment lines are skipped."""
    text = data.decode("utf-8-sig")
    lines = text.splitlines(keepends=True)
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    reader = csv.reader(io.StringIO("".join(lines)), strict=True)
    header = next(reader, [])
    n = hits = 0
    for row in reader:
        if not row:
            continue
        n += 1
        if any(ANTHROPIC.search(c) for c in row):
            hits += 1
    return n, header, hits


def committable(name: str, kind: str, size: int) -> bool:
    return kind == "csv" and size < COMMIT_LIMIT and not name.endswith("_external.csv")


def compute() -> dict[str, bytes]:
    """Relative output path under corpus/epoch/ -> bytes (inventory.tsv plus verbatim tables)."""
    csv.field_size_limit(sys.maxsize)
    out, rows = {}, []
    for r in read_tsv(MANIFEST):
        slug, src = r["dataset"], r["path"].split("/", 1)[1]
        if slug in NOT_PARSED:
            rows.append([slug, src, "", "xlsx", r["bytes"], "", "", "", r["blake3"], "", "", NOT_PARSED[slug]])
            continue
        for name, data in members(BULK / r["path"]):
            kind = name.rsplit(".", 1)[-1].lower()
            nrows = ncols = cols = hits = ""
            if kind == "csv":
                n, header, h = table_stats(data)
                nrows, ncols, cols, hits = n, len(header), json.dumps(header, ensure_ascii=False), h
            committed, note = "", ""
            if committable(name, kind, len(data)):
                committed = f"{slug}/{name}"
                out[committed] = data
            elif kind == "csv":
                note = ("third-party benchmark data, original licence; local only" if name.endswith("_external.csv")
                        else f">= {COMMIT_LIMIT} bytes; local only")
            rows.append([slug, src, name if name != src else "", kind, len(data), nrows, ncols, cols,
                         b3_bytes(data), hits, committed, note])
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    out["inventory.tsv"] = tsv(["dataset", "file", "member", "kind", "bytes", "rows", "columns", "column_names",
                                "blake3", "anthropic_rows", "committed", "note"], rows)
    return out


def table_dirs() -> list[Path]:
    return [CORPUS / d[0] for d in DATASETS]


def stray_files(out: dict[str, bytes]) -> list[Path]:
    return sorted(p for d in table_dirs() if d.exists() for p in d.rglob("*")
                  if p.is_file() and p.relative_to(CORPUS).as_posix() not in out)


def cmd_build() -> int:
    bad = check_pins()
    if bad:
        sys.exit("pins do not match: " + "; ".join(bad) + " (re-run `pin` to move the snapshot)")
    out = compute()
    for p in stray_files(out):
        p.unlink()
    for d in table_dirs():
        if d.exists() and not any(d.rglob("*.csv")):
            shutil.rmtree(d)
    for rel, data in sorted(out.items()):
        p = CORPUS / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    committed = {k: v for k, v in out.items() if k != "inventory.tsv"}
    print(f"wrote {len(committed)} verbatim tables ({sum(map(len, committed.values()))} bytes)")
    print(f"wrote {INVENTORY.relative_to(ROOT)}  {len(out['inventory.tsv'])} bytes  "
          f"blake3 {b3_bytes(out['inventory.tsv'])}")
    return 0


def cmd_verify() -> int:
    bad = check_pins()
    out = compute() if not bad else {}
    for rel, data in sorted(out.items()):
        p = CORPUS / rel
        if not p.exists() or b3_bytes(p.read_bytes()) != b3_bytes(data):
            bad.append(f"{rel} differs from a rebuild")
    bad += [f"stray file {p.relative_to(CORPUS)}" for p in stray_files(out)] if out else []
    for b in bad:
        print(f"FAIL: {b}")
    if out:
        print(f"inventory.tsv blake3 {b3_bytes(out['inventory.tsv'])}")
    print(f"{'ok' if not bad else 'FAIL'}: pins checked, {len(out)} outputs rebuilt and compared by BLAKE3")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["pin", "build", "verify"])
    ap.add_argument("--as-of", default="2026-11-04", help="pin: the snapshot date recorded in MANIFEST.tsv")
    a = ap.parse_args()
    if a.cmd == "pin":
        return cmd_pin(a.as_of)
    return {"build": cmd_build, "verify": cmd_verify}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
