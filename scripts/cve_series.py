#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0", "blake3==1.0.11"]
# ///
"""Monthly CVE time series from the CVE Program's cvelistV5, after Epoch AI's CVE explorer.

Source: CVEProject/cvelistV5, one daily baseline release asset
("<as-of>_all_CVEs_at_midnight.zip.zip": every CVE record as of 00:00Z on the
as-of date), pinned by URL, bytes, SHA-256 and BLAKE3 in corpus/cve/MANIFEST.tsv.
The asset wraps one inner archive, cves.zip, which is pinned the same way.
Bulk bytes live in the gitignored .cvecorpus/.

Method (Epoch AI, https://epoch.ai/data/cve, CC BY; reproduced and checked
cell by cell against the data embedded in Epoch's page, see docs/cve-series.md):
  universe   cveMetadata.state == PUBLISHED (REJECTED records are dropped) and
             CVE id year >= 2020. Epoch's "every published record 2020+" is the
             id year, not the publication year: a CVE-2019-* record published
             in 2021 is outside it. monthly.tsv also reports the any-id-year
             count so the gap is visible.
  month      cveMetadata.datePublished[:7] (UTC), 2020-01 .. the last full month
             before the as-of date.
  severity   first CVSS base score found, searching the CNA container, then each
             ADP container in record order; within a container v4.0, then v3.1,
             then v3.0 (v2 is ignored). Buckets by score: none 0, low 0.1-3.9,
             medium 4-6.9, high 7-8.9, critical 9-10; no score -> unknown.
             (Epoch's published data has no "none": it files 0.0 under low.)
  CNA        cveMetadata.assignerShortName, grouped into Epoch's notable CNAs
             (NOTABLE below) or Other.
  AI         see AI_PRODUCT and AI_CREDIT below; ai-related.tsv lists the matches.

No model, no clock: the as-of date is the recorded pin, outputs are sorted, and
`verify` rebuilds in memory and compares BLAKE3 hashes with the committed files.

    uv run scripts/cve_series.py pin --as-of 2026-11-04   # resolve release asset, download, hash -> MANIFEST.tsv
    uv run scripts/cve_series.py fetch                    # download + check into .cvecorpus/
    uv run scripts/cve_series.py build                    # corpus/cve/*.tsv
    uv run scripts/cve_series.py verify                   # check pins, rebuild in memory, compare hashes
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import blake3

sys.dont_write_bytecode = True                 # importing ec_extract must not leave scripts/__pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ec_extract import TERMS as EC_TERMS  # noqa: E402  (the earnings-call AI term families)
from ec_extract import ANY_RE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "cve"
BULK = ROOT / ".cvecorpus"                     # gitignored: ~650 MB release asset + ~720 MB inner zip
MANIFEST = CORPUS / "MANIFEST.tsv"
REPO = "CVEProject/cvelistV5"
UA = "anthropic-pbc cve series research (github.com/ethicalcapital/anthropic-pbc)"
FIRST_MONTH = "2020-01"
FIRST_ID_YEAR = 2020

# Epoch's notable CNAs -> cvelistV5 assignerShortName values. Every grouping was
# checked against Epoch's per-CNA totals (exact match for all 21 labels).
NOTABLE = {
    "Microsoft": ["microsoft"],
    "Google": ["Chrome", "ChromeOS", "Google", "GoogleCloud", "Google_Devices", "google_android"],
    "Apple": ["apple"],
    "Adobe": ["adobe"],
    "Oracle": ["oracle"],
    "Cisco": ["cisco"],
    "IBM": ["ibm"],
    "Red Hat": ["redhat"],                      # not redhat-cnalr (CNA of last resort for others' code)
    "Intel": ["intel"],
    "AMD": ["AMD"],
    "NVIDIA": ["nvidia"],
    "Qualcomm": ["qualcomm"],
    "Samsung": ["Samsung Mobile", "SamsungMobile", "samsung.tv_appliance"],
    "SAP": ["sap"],
    "AWS": ["AMZN"],
    "VMware": ["vmware"],                       # not brocade (Broadcom's other products)
    "GitHub": ["GitHub_P"],                     # own products; not GitHub_M (maintainer advisories)
    "Linux": ["Linux"],
    "Mozilla": ["mozilla"],
    "Apache": ["apache"],
    "OpenSSL": ["openssl"],
}
CNA_LABEL = {s: lab for lab, ss in NOTABLE.items() for s in ss}
SEVERITIES = ["critical", "high", "medium", "low", "none", "unknown"]

# (a) AI product: ANY_RE from scripts/ec_extract.py over the English description and
# the affected vendor/product/packageName/repo strings, plus these AI-software terms.
AI_PRODUCT = {
    "langchain":   r"(?i:\blangchain)",
    "llamaindex":  r"(?i:\bllama[-_ ]?index\b)",
    "ollama":      r"(?i:\bollama\b)",
    "vllm":        r"(?i:\bvllm\b)",
    "mcp":         r"(?i:model context protocol|\bMCP[-_ ](?:server|client|host|gateway|proxy|inspector|tools?)s?\b)",
    "huggingface": r"(?i:hugging ?face|\bhuggingface)",
    "pytorch":     r"(?i:\bpytorch\b|\btorchserve\b)",
    "tensorflow":  r"(?i:\btensorflow\b|\bkeras\b)",
    "onnx":        r"(?i:\bonnx(?:runtime)?\b)",
    "llama_cpp":   r"(?i:\bllama[.-]cpp\b|\bllama\.cpp\b|\bgguf\b)",
    "open_webui":  r"(?i:\bopen[- ]?webui\b|\btext-generation-webui\b|\blibrechat\b|\blobe-?chat\b|\banythingllm\b|\blollms\b|\blocalai\b)",
    "comfyui":     r"(?i:\bcomfyui\b|\bstable[- ]diffusion\b)",
    "gradio":      r"(?i:\bgradio\b)",
    "mlflow":      r"(?i:\bmlflow\b|\bkubeflow\b|\bbentoml\b)",
    "litellm":     r"(?i:\blitellm\b)",
    "agent_builder": r"(?i:\blangflow\b|\bflowise\b|\bdify\b|\bautogpt\b|\bcrewai\b|\bautogen\b|\bsemantic[- ]kernel\b)",
    "nvidia_ai":   r"(?i:\btriton inference server\b|\btensorrt(?:-llm)?\b|\bdeepspeed\b)|\bNeMo\b",
    "ai_ide":      r"(?i:\bcodeium\b|\bwindsurf\b|\banysphere\b|\bcursor ide\b)",
}
# Field "product" is vendor/product/packageName/repo; "mcp" also matches a bare
# "mcp" token there (package names such as mcp-server-git), never in prose.
MCP_PRODUCT = re.compile(r"(?i)(?:^|[^a-z0-9])mcp(?:$|[^a-z0-9])")

# (b) AI credit: matched against credits[].value only, never the description.
# "Claude" must not be followed by a capitalised surname (a person named Claude).
AI_CREDIT = {
    "claude":     r"\bClaude\b(?!\s+(?!(?:Code|Opus|Sonnet|Haiku|Fable|Mythos|AI|Agents?|Security)\b)[A-Z][a-z])",
    "mythos":     r"\bMythos\b",
    "anthropic":  r"(?i:\banthropic\b)",
    "openai":     r"(?i:\bopenai\b)",
    "gpt":        r"(?i:\bchatgpt\b|\bgpt\b|\bgpt-?\d)",
    "codex":      r"(?i:\bcodex\b)",
    "aardvark":   r"(?i:\baardvark\b)",
    "big_sleep":  r"(?i:\bbig ?sleep\b|\bnaptime\b)",
    "deepmind":   r"(?i:\bdeepmind\b|\bcodemender\b)",
    "gemini":     r"(?i:\bgemini\b)",
    "xbow":       r"(?i:\bxbow\b)",
    "copilot":    r"(?i:\bcopilot\b)",
    "aixcc":      r"(?i:\baixcc\b|\bteam atlanta\b)",
    "zeropath":   r"(?i:\bzeropath\b)",
    "vulnhuntr":  r"(?i:\bvulnhuntr\b)",
}
# A credit with none of the named systems but a generic AI term (ec_extract's
# "ai", "ai_phrase", "ml", "llm", "agentic" families; not "vendor") -> ai_term.
GENERIC = re.compile("|".join(f"(?:{EC_TERMS[k]})" for k in ("ai", "ai_phrase", "ml", "llm", "agentic")))
AI_PRODUCT_RE = {k: re.compile(v) for k, v in AI_PRODUCT.items()}
AI_CREDIT_RE = {k: re.compile(v) for k, v in AI_CREDIT.items()}
EC_RE = {k: re.compile(v) for k, v in EC_TERMS.items()}
CREDIT_COLS = list(AI_CREDIT) + ["ai_term"]
# Credit types that fix rather than find: excluded from n_ai_credited_discovery.
REMEDIATION = {"remediation developer", "remediation reviewer", "remediation verifier"}


def b3_bytes(b: bytes) -> str:
    return blake3.blake3(b).hexdigest()


def hash_file(p: Path) -> tuple[int, str, str]:
    s, b = hashlib.sha256(), blake3.blake3(max_threads=blake3.blake3.AUTO)
    with p.open("rb") as f:
        while chunk := f.read(1 << 24):
            s.update(chunk)
            b.update(chunk)
    return p.stat().st_size, s.hexdigest(), b.hexdigest()


def manifest() -> dict[str, dict[str, str]]:
    with MANIFEST.open(newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f, delimiter="\t")}


def get_json(url: str):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60))


def download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".part")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r, \
            tmp.open("wb") as f:
        while chunk := r.read(1 << 22):
            f.write(chunk)
    tmp.rename(dst)


def extract_inner(outer: Path, name: str) -> Path:
    dst = BULK / name
    if not dst.exists():
        with zipfile.ZipFile(outer) as z, z.open(name) as src, dst.with_name(name + ".part").open("wb") as out:
            while chunk := src.read(1 << 22):
                out.write(chunk)
        dst.with_name(name + ".part").rename(dst)
    return dst


# ---------------------------------------------------------------- pin / fetch
def cmd_pin(as_of: str) -> int:
    asset_name = f"{as_of}_all_CVEs_at_midnight.zip.zip"
    found = []
    for page in range(1, 11):    # releases are hourly; 1,000 covers ~6 weeks
        rels = get_json(f"https://api.github.com/repos/{REPO}/releases?per_page=100&page={page}")
        if not rels:
            break
        for r in rels:
            for a in r["assets"]:
                if a["name"] == asset_name:
                    found.append((r["published_at"], r["tag_name"], a))
        if found and min(x[0] for x in found) > rels[-1]["published_at"]:
            break
    if not found:
        sys.exit(f"no release asset {asset_name} in the last 1,000 releases of {REPO}")
    _, tag, asset = min(found, key=lambda x: x[0])   # earliest release carrying this baseline
    commit = get_json(f"https://api.github.com/repos/{REPO}/git/ref/tags/{tag}")["object"]["sha"]
    url = asset["browser_download_url"]
    outer = BULK / asset_name
    if not outer.exists():
        download(url, outer)
    size, sha, b3 = hash_file(outer)
    if size != asset["size"] or f"sha256:{sha}" != asset.get("digest", f"sha256:{sha}"):
        sys.exit(f"FAIL: {asset_name} size/sha256 differ from GitHub's asset metadata")
    inner = extract_inner(outer, "cves.zip")
    isize, isha, ib3 = hash_file(inner)
    CORPUS.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "role", "pinned", "url", "path", "bytes", "sha256", "blake3", "note"])
        w.writerow(["baseline", "source", as_of, url, asset_name, size, sha, b3,
                    f"{REPO} release {tag} (tag commit {commit}); every CVE record at {as_of}T00:00Z; "
                    "sha256 = GitHub asset digest; CVE Program terms of use"])
        w.writerow(["cves", "source", as_of, f"zip:{asset_name}!cves.zip", "cves.zip", isize, isha, ib3,
                    "the single member of the baseline asset; build reads this"])
    print(f"ok: {asset_name} from {tag} @ {commit[:12]}: {size} bytes; cves.zip {isize} bytes -> "
          f"{MANIFEST.relative_to(ROOT)}")
    return 0


def check_pins() -> list[str]:
    bad = []
    for r in manifest().values():
        p = BULK / r["path"]
        if not p.exists():
            bad.append(f"missing {p.name}")
            continue
        size, sha, b3 = hash_file(p)
        if str(size) != r["bytes"] or sha != r["sha256"] or b3 != r["blake3"]:
            bad.append(f"hash mismatch {p.name}")
    return bad


def cmd_fetch() -> int:
    m = manifest()
    outer = BULK / m["baseline"]["path"]
    if not outer.exists():
        download(m["baseline"]["url"], outer)
    extract_inner(outer, m["cves"]["path"])
    bad = check_pins()
    for b in bad:
        print(f"FAIL: {b}")
    if not bad:
        print(f"ok: {outer.name} and cves.zip match MANIFEST.tsv")
    return 1 if bad else 0


# ---------------------------------------------------------------- classify one record
def severity(d: dict) -> str:
    conts = [d.get("containers", {}).get("cna", {})] + list(d.get("containers", {}).get("adp", []) or [])
    for c in conts:
        for key in ("cvssV4_0", "cvssV3_1", "cvssV3_0"):
            for m in c.get("metrics", []) or []:
                if key in m and m[key].get("baseScore") is not None:
                    s = float(m[key]["baseScore"])
                    return ("none" if s == 0 else "low" if s < 4 else "medium" if s < 7
                            else "high" if s < 9 else "critical")
    return "unknown"


def ai_product(cna: dict) -> list[str]:
    hits = set()
    for a in cna.get("affected", []) or []:
        for f in ("vendor", "product", "packageName", "repo"):
            v = a.get(f)
            if not isinstance(v, str) or not v:
                continue
            hits |= {f"product:{k}" for k, r in EC_RE.items() if r.search(v)}
            hits |= {f"product:{k}" for k, r in AI_PRODUCT_RE.items() if r.search(v)}
            if MCP_PRODUCT.search(v):
                hits.add("product:mcp")
    for desc in cna.get("descriptions", []) or []:
        if not str(desc.get("lang", "")).lower().startswith("en"):
            continue
        v = desc.get("value") or ""
        hits |= {f"description:{k}" for k, r in EC_RE.items() if r.search(v)}
        hits |= {f"description:{k}" for k, r in AI_PRODUCT_RE.items() if r.search(v)}
    return sorted(hits)


def ai_credit(cna: dict) -> tuple[list[str], list[str]]:
    """(systems, "system:type" pairs) over the CNA container's credits array."""
    systems, pairs = set(), set()
    for c in cna.get("credits", []) or []:
        v = c.get("value") or ""
        hit = {k for k, r in AI_CREDIT_RE.items() if r.search(v)}
        if not hit and GENERIC.search(v):
            hit = {"ai_term"}
        systems |= hit
        pairs |= {f"{k}:{c.get('type') or 'unspecified'}" for k in hit}
    return sorted(systems), sorted(pairs)


# ---------------------------------------------------------------- build
def last_full_month(as_of: str) -> str:
    y, m = int(as_of[:4]), int(as_of[5:7])
    y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return f"{y:04d}-{m:02d}"


def month_range(a: str, b: str) -> list[str]:
    out, (y, m) = [], (int(a[:4]), int(a[5:7]))
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def tsv(header: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def compute() -> tuple[dict[str, bytes], dict[str, int]]:
    m = manifest()
    as_of = m["cves"]["pinned"]
    last = last_full_month(as_of)
    months = month_range(FIRST_MONTH, last)
    stats = Counter()
    sev = defaultdict(Counter)
    by_cna = defaultdict(Counter)
    any_year = Counter()
    ai_rows = []
    with zipfile.ZipFile(BULK / m["cves"]["path"]) as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            name = info.filename
            if not (name.endswith(".json") and "/CVE-" in name):
                continue
            d = json.loads(z.read(info))
            md = d.get("cveMetadata", {})
            stats["records"] += 1
            if md.get("state") != "PUBLISHED":
                stats[f"state_{str(md.get('state')).lower()}"] += 1
                continue
            dp = md.get("datePublished") or ""
            month = dp[:7]
            if not dp:
                stats["published_no_date"] += 1
                continue
            if not (FIRST_MONTH <= month <= last):
                stats["published_outside_window"] += 1
                continue
            any_year[month] += 1
            cve_id = md["cveId"]
            if int(cve_id.split("-")[1]) < FIRST_ID_YEAR:
                stats["in_window_id_before_2020"] += 1
                continue
            stats["universe"] += 1
            s = severity(d)
            short = md.get("assignerShortName") or ""
            label = CNA_LABEL.get(short, "Other")
            sev[month][s] += 1
            by_cna[month][label] += 1
            cna = d.get("containers", {}).get("cna", {})
            prod = ai_product(cna)
            systems, types = ai_credit(cna)
            if prod or systems:
                ai_rows.append([cve_id, dp[:10], short, s, ";".join(prod), ";".join(systems), ";".join(types)])
    ai_rows.sort(key=lambda r: (r[1], r[0]))

    monthly = []
    for mo in months:
        n = sum(sev[mo].values())
        notable = sum(v for k, v in by_cna[mo].items() if k != "Other")
        linux = by_cna[mo]["Linux"]
        monthly.append([mo, n] + [sev[mo][s] for s in SEVERITIES] + [notable, linux, n - linux, any_year[mo]])
    labels = list(NOTABLE) + ["Other"]
    per_cna = [[mo] + [by_cna[mo][lab] for lab in labels] for mo in months]

    ai_m = defaultdict(Counter)
    for cve_id, day, _, _, prod, systems, pairs in ai_rows:
        mo = day[:7]
        if prod:
            ai_m[mo]["product"] += 1
            if any(p.startswith("product:") for p in prod.split(";")):
                ai_m[mo]["affected"] += 1
        if systems:
            ai_m[mo]["credited"] += 1
            if any(p.split(":", 1)[1] not in REMEDIATION for p in pairs.split(";")):
                ai_m[mo]["discovery"] += 1
            for sname in systems.split(";"):
                ai_m[mo][sname] += 1
    monthly_ai = [[mo, sum(sev[mo].values()), ai_m[mo]["product"], ai_m[mo]["affected"], ai_m[mo]["credited"],
                   ai_m[mo]["discovery"]] + [ai_m[mo][c] for c in CREDIT_COLS] for mo in months]

    stats["ai_rows"] = len(ai_rows)
    stats["ai_product"] = sum(1 for r in ai_rows if r[4])
    stats["ai_credited"] = sum(1 for r in ai_rows if r[5])
    out = {
        "monthly.tsv": tsv(["month", "n_published"] + SEVERITIES +
                           ["n_notable_cna", "n_linux_cna", "n_excl_linux", "n_published_any_id_year"], monthly),
        "monthly-by-cna.tsv": tsv(["month"] + labels, per_cna),
        "ai-related.tsv": tsv(["cve_id", "date_published", "cna", "severity", "ai_product_rules",
                               "ai_credit_systems", "ai_credit_system_types"], ai_rows),
        "monthly-ai.tsv": tsv(["month", "n_published", "n_ai_product", "n_ai_product_affected", "n_ai_credited",
                                                "n_ai_credited_discovery"] + [f"n_credit_{c}" for c in CREDIT_COLS], monthly_ai),
    }
    return out, dict(stats, as_of=as_of, last_month=last)


def cmd_build() -> int:
    bad = check_pins()
    if bad:
        sys.exit("pins do not match: " + "; ".join(bad) + " (run `fetch`)")
    out, stats = compute()
    for name, data in out.items():
        (CORPUS / name).write_bytes(data)
        print(f"wrote {(CORPUS / name).relative_to(ROOT)}  {len(data)} bytes  blake3 {b3_bytes(data)}")
    print("stats: " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    return 0


def cmd_verify() -> int:
    bad = check_pins()
    out, _ = compute() if not bad else ({}, {})
    for name, data in out.items():
        p = CORPUS / name
        if not p.exists() or b3_bytes(p.read_bytes()) != b3_bytes(data):
            bad.append(f"{name} differs from a rebuild")
    for b in bad:
        print(f"FAIL: {b}")
    print(f"{'ok' if not bad else 'FAIL'}: pins checked, {len(out)} outputs rebuilt and compared by BLAKE3")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["pin", "fetch", "build", "verify"])
    ap.add_argument("--as-of", default="2026-11-04", help="pin: baseline date (YYYY-MM-DD, 00:00Z snapshot)")
    a = ap.parse_args()
    if a.cmd == "pin":
        return cmd_pin(a.as_of)
    return {"fetch": cmd_fetch, "build": cmd_build, "verify": cmd_verify}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
