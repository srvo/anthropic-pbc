#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["blake3>=1.0"]
# ///
"""Stage 0b: derive plain text from pinned sources and segment clauses.

Derivation is lossy and says so: PDF via poppler `pdftotext` (circle 1
instrument, docs/circles.md), HTML via the same dependency-free stripper
as scripts/rf_extract.py. Derived text is a new artifact with its own
BLAKE3; clause byte offsets anchor into the DERIVED artifact, never into
source bytes. Layout loss (multi-column order, tables, hyphenation) is
unmeasured in v0.1 and every downstream rate inherits that caveat.

    uv run scripts/enrich_derive.py          # derive + segment
    uv run scripts/enrich_derive.py verify   # re-slice every unit, re-hash

Outputs (gitignored bulk, rebuildable): enrich-out/derived/<id>.txt,
enrich-out/units.tsv, enrich-out/derived-MANIFEST.tsv.
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

import blake3

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sources"
OUT = ROOT / "enrich-out"
DER = OUT / "derived"


def strip_html(raw: str) -> str:
    """Identical logic to scripts/rf_extract.py strip_html (kept in sync
    by inspection; a parser that repairs markup would hide drift)."""
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    s = re.sub(r"(?is)<!--.*?-->", " ", s)
    s = re.sub(r"(?i)<(br|/p|/div|/tr|/h[1-6]|/li|hr)\b[^>]*>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ").replace("\u200b", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def derive() -> list[tuple[str, str, str, Path]]:
    rows = []
    manifest = (SRC / "MANIFEST.tsv").read_text(encoding="utf-8").strip().splitlines()[1:]
    DER.mkdir(parents=True, exist_ok=True)
    for line in manifest:
        doc_id, role, _f, _u, path, _b, src_hash = line.split("\t")
        src = SRC / path
        if blake3.blake3(src.read_bytes()).hexdigest() != src_hash:
            raise SystemExit(f"source hash mismatch: {doc_id} (run enrich_fetch verify)")
        if path.endswith(".pdf"):
            out = DER / f"{doc_id}.txt"
            subprocess.run(["pdftotext", str(src), str(out)], check=True)
            tool = "pdftotext(poppler)"
        else:
            out = DER / f"{doc_id}.txt"
            out.write_text(strip_html(src.read_text(encoding="utf-8", errors="replace")),
                           encoding="utf-8")
            tool = "strip_html-rf"
        rows.append((doc_id, role, tool, out))
    return rows


SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"“])")
CLAUSE_SPLIT = re.compile(
    r";\s+|,\s+(?=(?:and|but|while|whereas)\s+(?:we|the company|anthropic|it|they)\b)", re.I)


def section_guess(doc_id: str, window: str) -> str:
    w = window.lower()
    if "risk factor" in w: return "risk"
    if "cybersecurity" in w and ("item 106" in w or "risk management and strategy" in w): return "cyber-106"
    if "pillar" in w or "public benefit" in w: return "pillar-benefit"
    if "corporate governance" in w or "long-term benefit trust" in w or "certificate of incorporation" in w: return "governance"
    if "capitalization" in w or "description of capital stock" in w: return "capital"
    if "consolidated statements" in w or "management's discussion" in w or "managements discussion" in w: return "financial"
    return "other"


def segment(doc_id: str, role: str, text: str) -> list[list[str]]:
    """Clauses with char offsets into `text`. Offsets are character
    offsets into the derived UTF-8 text; slice_blake3 is over the UTF-8
    bytes of the clause, so re-slicing verifies regardless of offset kind."""
    units = []
    # Paragraphs first (context), then sentences, then clauses.
    cursor = 0
    for para in text.split("\n\n"):
        p_start = text.find(para, cursor)
        cursor = p_start + len(para)
        local = 0
        flat = " ".join(para.split())
        for sent in SENT_END.split(flat):
            s_idx = flat.find(sent, local); local = s_idx + len(sent)
            c_local = 0
            for clause in CLAUSE_SPLIT.split(sent):
                clause = clause.strip()
                if len(clause) < 25 or not re.search(r"[A-Za-z]{3,}", clause):
                    continue
                if not re.search(r"\b(is|are|was|were|will|shall|may|can|could|must|has|have|had|intend|plan|aim|expect|believe|seek|hope|would)\b", clause, re.I):
                    continue  # no finite/modal verb proxy: not a clause under codebook §1
                frag = clause[:40]
                s_pos = sent.find(frag, c_local); c_local = max(c_local, s_pos + len(clause))
                units.append([doc_id, role, section_guess(doc_id, flat[max(0, s_idx-200):s_idx+200]),
                              sent.replace("\t", " "), clause.replace("\t", " ")])
    return units


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        # Re-slice every unit quote from its derived artifact (existence +
        # exactly-once is checked in enrich_stage2; here: hash integrity).
        bad = 0
        lines = (OUT / "derived-MANIFEST.tsv").read_text(encoding="utf-8").strip().splitlines()[1:]
        for line in lines:
            doc_id, _r, _t, path, digest = line.split("\t")
            data = (ROOT / path).read_bytes()
            if blake3.blake3(data).hexdigest() != digest:
                print(f"MISMATCH {doc_id}"); bad += 1
        print(f"verified {len(lines)} derived artifacts; {bad} bad")
        return 1 if bad else 0

    rows = derive()
    man = ["id\trole\ttool\tpath\tblake3"]
    all_units = []
    for (doc_id, role, tool, out) in rows:
        text = out.read_text(encoding="utf-8", errors="replace")
        digest = blake3.blake3(out.read_bytes()).hexdigest()
        man.append(f"{doc_id}\t{role}\t{tool}\t{out.relative_to(ROOT)}\t{digest}")
        units = segment(doc_id, role, text)
        for i, u in enumerate(units):
            ch = blake3.blake3(u[4].encode("utf-8")).hexdigest()
            all_units.append([f"{doc_id}:{i:06d}", u[0], u[1], u[2], ch, u[3], u[4]])
        print(f"{doc_id}: {len(text.split()):,} words -> {len(units):,} clauses")
    (OUT / "derived-MANIFEST.tsv").write_text("\n".join(man) + "\n", encoding="utf-8")
    hdr = "unit_id\tdoc_id\trole\tsection_guess\tclause_blake3\tsentence\tclause"
    body = [hdr] + ["\t".join(u) for u in all_units]
    (OUT / "units.tsv").write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"wrote {OUT/'units.tsv'} ({len(all_units):,} units); manifests in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
