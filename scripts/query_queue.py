"""Query queue: every explored point -> web searches -> normalized leads.

    python3 scripts/query_queue.py plan        # argument/points.tsv -> research/queries.tsv
    bws run -- python3 scripts/query_queue.py run [--limit N] [--workers 4]
    python3 scripts/query_queue.py normalize   # .leadscorpus/*.json -> research/leads.tsv
    python3 scripts/query_queue.py status

Stages, each recorded in research/queries.tsv `state`:
    queued -> searched (raw response pinned) | failed (HTTP status kept) -> normalized

Raw responses are kept byte for byte in the gitignored .leadscorpus/ and pinned in
research/MANIFEST.tsv (sha256, bytes, retrieved_at), the same way corpus/ pins bulk
bytes. research/leads.tsv is committed. A lead is not evidence: it becomes evidence
only when its source is pinned under docs/data-intake-checklist.md and a quote from
it passes the Descartes byte check.

The API key is read from TINYFISH_API_KEY inside this process and never printed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POINTS = ROOT / "argument/points.tsv"  # plus argument/open-lines.tsv
RES = ROOT / "research"
QUERIES = RES / "queries.tsv"
MANIFEST = RES / "MANIFEST.tsv"
LEADS = RES / "leads.tsv"
RAW = ROOT / ".leadscorpus"

# TinyFish is reached through its MCP server, as Claude Code reaches it (~/.claude.json): X-API-Key header.
SEARCH_URL = os.environ.get("TINYFISH_MCP_URL", "https://agent.tinyfish.ai/mcp")
AUTH_HEADER = "X-API-Key"

Q_COLS = ["query_id", "point_id", "query", "state", "detail"]
M_COLS = ["query_id", "retrieved_at", "bytes", "sha256", "path"]
L_COLS = ["query_id", "point_id", "rank", "url", "domain", "source_class", "title", "snippet",
          "published", "url_sha256"]

# Domain -> source class. A primary source is what a lead must reach before it can be pinned.
CLASSES = [
    ("filing", ("sec.gov", "edgar")),
    ("statute", ("delcode.delaware.gov", "law.cornell.edu", "legislature", "congress.gov", "govinfo.gov", "legislation.gov")),
    ("court", ("courtlistener.com", "courts.delaware.gov", "uscourts.gov", "justia.com", "casetext.com", "supremecourt.gov")),
    ("agency", (".gov", "iea.org", "ipcc.ch", "unfccc.int", "europa.eu", "oecd.org", "who.int", "worldbank.org", "un.org")),
    ("subject", ("anthropic.com", "claude.com", "woodcache.org", "puro.earth")),
    ("commentary", ("morrisnichols.com", "cooley.com", "cooleygo.com", "rlf.com", "reedsmith.com", "gibsondunn.com", "mintz.com",
                    "mintzedge.com", "btlaw.com", "wolterskluwer.com", "thecorporatecounsel.net", "nonprofitlawblog.com", "delawareinc.com",
                    "upcounsel.com", "harvard.edu/corpgov", "corpgov.law.harvard.edu", "lexology.com", "jdsupra.com", "law360.com",
                    "skadden.com", "wsgr.com", "lw.com", "sullcrom.com", "davispolk.com", "theshareholdercommons.com", "aals.org")),
    ("paper", ("doi.org", "arxiv.org", "nature.com", "science.org", "sciencedirect.com", "springer.com", "wiley.com",
               "pnas.org", "ssrn.com", "hal.science", "sup.org", "opencasebook.org", "jstor.org", "researchgate.net", ".edu", "ecologyandsociety.org", "stockholmresilience.org")),
    ("data", ("epoch.ai", "ourworldindata.org", "github.com", "huggingface.co", "kaggle.com")),
    ("social", ("linkedin.com", "facebook.com", "reddit.com", "youtube.com", "x.com", "twitter.com", "medium.com", "substack.com", "quora.com")),
    ("market", ("finance.yahoo.com", "stockopedia.com", "indmoney.com", "microventures.com", "seekingalpha.com", "fool.com", "marketwatch.com",
                "investing.com", "morningstar.com", "forgeglobal.com", "sec-api.io")),
    ("news", ("reuters.com", "bloomberg.com", "ft.com", "wsj.com", "nytimes.com", "theverge.com", "techcrunch.com",
              "apnews.com", "cnbc.com", "theguardian.com", "axios.com", "wired.com", "washingtonpost.com")),
]


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return list(csv.DictReader((l for l in path.open() if not l.startswith("#")), delimiter="\t"))


def write(path: Path, cols: list[str], rows: list[dict], header: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        f.write(header)
        w = csv.DictWriter(f, cols, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: str(r.get(k, "")).replace("\t", " ").replace("\n", " ") for k in cols})


def qid(point: str, query: str) -> str:
    return hashlib.sha256(f"{point}\x00{query.strip().lower()}".encode()).hexdigest()[:12]


def plan(_: argparse.Namespace) -> None:
    old = {r["query_id"]: r for r in read(QUERIES)}
    rows, seen = [], set()
    sources = [(p["id"], p.get("queries", "")) for p in read(POINTS)]
    sources += [(l["id"], l.get("queries", "")) for l in read(ROOT / "argument/open-lines.tsv")]
    for pid, qs in sources:
        p = {"id": pid, "queries": qs}
        for q in (x.strip() for x in p.get("queries", "").split("||")):
            if not q:
                continue
            k = qid(p["id"], q)
            if k in seen:
                continue
            seen.add(k)
            rows.append(old.get(k) or {"query_id": k, "point_id": p["id"], "query": q, "state": "queued", "detail": ""})
    write(QUERIES, Q_COLS, rows, "# Query queue, planned from argument/points.tsv by scripts/query_queue.py plan.\n")
    print(f"planned {len(rows)} queries from {len(read(POINTS))} points ({len(rows) - len([r for r in rows if r['query_id'] in old])} new)")


class MCP:
    """Minimal MCP (streamable HTTP, JSON-RPC) client for TinyFish's `search` tool."""

    def __init__(self, url: str, key: str):
        self.url, self.key, self.sid, self.n, self.lock = url, key, None, 0, threading.Lock()

    def _post(self, msg: dict) -> tuple[int, dict | None]:
        h = {AUTH_HEADER: self.key, "Content-Type": "application/json",
             "Accept": "application/json, text/event-stream", "User-Agent": "anthropic-pbc-query-queue/1"}
        if self.sid:
            h["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.url, data=json.dumps(msg).encode(), headers=h, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                self.sid = r.headers.get("Mcp-Session-Id") or self.sid
                body = r.read().decode("utf-8", "replace")
                status = r.status
        except urllib.error.HTTPError as e:  # the body may echo the request; keep the status only
            return e.code, None
        except (urllib.error.URLError, TimeoutError):
            return 0, None
        if not body.strip():
            return status, None
        if body.lstrip().startswith("{"):
            return status, json.loads(body)
        for line in body.splitlines():  # server-sent events: the JSON-RPC reply is a data: line
            if line.startswith("data:") and '"id"' in line:
                return status, json.loads(line[5:])
        return status, None

    def call(self, method: str, params: dict | None = None, notify: bool = False) -> tuple[int, dict | None]:
        msg = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notify:
            with self.lock:
                self.n += 1
                msg["id"] = self.n
        return self._post(msg)

    def open(self) -> int:
        st, _ = self.call("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                         "clientInfo": {"name": "anthropic-pbc-query-queue", "version": "1"}})
        if st == 200:
            self.call("notifications/initialized", notify=True)
        return st


def search(mcp: MCP, query: str) -> tuple[int, bytes]:
    st, reply = mcp.call("tools/call", {"name": "search", "arguments": {"query": query}})
    if st != 200 or not reply or "result" not in reply:
        return st or 0, b""
    res = reply["result"]
    if res.get("isError"):  # a tool error carries no secret; keep its first words to diagnose
        msg = " ".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        return 502, ("tool error: " + msg[:160]).encode()
    # Prefer structured content; else the first text block, which TinyFish returns as JSON text.
    doc = res.get("structuredContent")
    if doc is None:
        texts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
        try:
            doc = json.loads(texts[0]) if texts else None
        except json.JSONDecodeError:
            doc = {"text": texts[0]}
    return 200, json.dumps({"query": query, "response": doc}, sort_keys=True, ensure_ascii=False).encode()


def run(a: argparse.Namespace) -> None:
    key = os.environ.get("TINYFISH_API_KEY", "")
    if not key:
        sys.exit("TINYFISH_API_KEY is not set (run under `bws run --`)")
    rows = read(QUERIES)
    todo = [r for r in rows if r["state"] in ("queued", "failed")][: a.limit or None]
    man = {m["query_id"]: m for m in read(MANIFEST)}
    RAW.mkdir(exist_ok=True)
    mcp = MCP(SEARCH_URL, key)
    st = mcp.open()
    if st != 200:
        sys.exit(f"MCP initialize failed: http {st}")

    def one(r: dict) -> None:
        for attempt in range(4):  # back off on rate limits
            status, body = search(mcp, r["query"])
            if status == 200 or attempt == 3:
                break
            time.sleep(2 ** attempt * 3)
        if status != 200 or not body:
            r["state"], r["detail"] = "failed", f"http {status} {body.decode(errors='replace')}".strip()
            return
        path = RAW / f"{r['query_id']}.json"
        path.write_bytes(body)
        man[r["query_id"]] = {"query_id": r["query_id"], "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                              "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "path": f".leadscorpus/{path.name}"}
        r["state"], r["detail"] = "searched", ""

    done_n, lock = [0], threading.Lock()

    def save() -> None:
        write(QUERIES, Q_COLS, rows, "# Query queue, planned from argument/points.tsv by scripts/query_queue.py plan.\n")
        write(MANIFEST, M_COLS, sorted(man.values(), key=lambda m: m["query_id"]),
              "# Raw TinyFish search responses, pinned by hash. Bytes live in the gitignored .leadscorpus/.\n")

    def step(r: dict) -> None:
        one(r)
        with lock:
            done_n[0] += 1
            if done_n[0] % 25 == 0:  # checkpoint, so an interrupted run keeps its work
                save()
                print(f"  {done_n[0]}/{len(todo)}", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(step, todo))
    write(QUERIES, Q_COLS, rows, "# Query queue, planned from argument/points.tsv by scripts/query_queue.py plan.\n")
    write(MANIFEST, M_COLS, sorted(man.values(), key=lambda m: m["query_id"]),
          "# Raw TinyFish search responses, pinned by hash. Bytes live in the gitignored .leadscorpus/.\n")
    done = sum(r["state"] == "searched" for r in todo)
    print(f"ran {len(todo)}: {done} searched, {len(todo) - done} failed")


def classify(domain: str) -> str:
    for cls, pats in CLASSES:
        if any(domain == p or domain.endswith("." + p.lstrip(".")) or ("." not in p and p in domain) for p in pats):
            return cls
    return "other"


def results_of(doc: object) -> list[dict]:
    """Find the list of result objects in a search response, whatever its envelope."""
    if isinstance(doc, list):
        return [x for x in doc if isinstance(x, dict)]
    if isinstance(doc, dict):
        for k in ("response", "results", "data", "items", "organic", "web"):
            if k in doc:
                return results_of(doc[k])
    return []


def normalize(_: argparse.Namespace) -> None:
    rows = read(QUERIES)
    leads, seen = [], set()
    for r in rows:
        f = RAW / f"{r['query_id']}.json"
        if r["state"] not in ("searched", "normalized") or not f.exists():
            continue
        for i, x in enumerate(results_of(json.loads(f.read_bytes())), 1):
            url = x.get("url") or x.get("link") or ""
            if not url or (r["point_id"], url) in seen:
                continue
            seen.add((r["point_id"], url))
            dom = urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.")
            leads.append({"query_id": r["query_id"], "point_id": r["point_id"], "rank": x.get("position") or i,
                          "url": url, "domain": dom, "source_class": classify(dom), "title": x.get("title", ""),
                          "snippet": (x.get("snippet") or x.get("description") or x.get("content") or "")[:400],
                          "published": x.get("published_date") or x.get("date") or x.get("published") or "",
                          "url_sha256": hashlib.sha256(url.encode()).hexdigest()[:16]})
        r["state"] = "normalized"
    write(LEADS, L_COLS, leads, "# Leads, not evidence: see docs/data-intake-checklist.md. Built by scripts/query_queue.py normalize.\n")
    write(QUERIES, Q_COLS, rows, "# Query queue, planned from argument/points.tsv by scripts/query_queue.py plan.\n")
    by = {}
    for l in leads:
        by[l["source_class"]] = by.get(l["source_class"], 0) + 1
    print(f"{len(leads)} leads; by class {dict(sorted(by.items(), key=lambda kv: -kv[1]))}")


def status(_: argparse.Namespace) -> None:
    rows = read(QUERIES)
    st = {}
    for r in rows:
        st[r["state"]] = st.get(r["state"], 0) + 1
    print(f"points {len(read(POINTS))} · queries {len(rows)} {st} · leads {len(read(LEADS))}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(required=True)
    sub.add_parser("plan").set_defaults(f=plan)
    r = sub.add_parser("run")
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--workers", type=int, default=4)
    r.set_defaults(f=run)
    sub.add_parser("normalize").set_defaults(f=normalize)
    sub.add_parser("status").set_defaults(f=status)
    a = ap.parse_args()
    a.f(a)
