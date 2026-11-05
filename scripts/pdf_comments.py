# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf==1.26.4"]
# ///
"""Receive reader comments on an emitted PDF (docs/comments-standard.md).

  record PDF --date D --built-from C --to DEST
      Append the emitted file's SHA-256, size and source commit to
      docs/emissions.tsv. Run when a rendering is handed to a reader.
  pull PDF --date D --ledger comments/<doc>.tsv
      Compare PDF byte for byte with its emission record. If the bytes
      are unchanged, say so and stop. If they changed, extract every
      annotation and append the ones not yet in the ledger, verbatim.

No clock enters any output: the date is an argument.
"""
import argparse
import hashlib
import sys
from pathlib import Path

EMISSIONS = Path("docs/emissions.tsv")
EMISSIONS_HEAD = "date\tfile\tsha256\tbytes\tbuilt_from\tto\n"
LEDGER_HEAD = ("id\treceived\tpdf_sha256\temitted_sha256\tbuilt_from\tpage\tkind\t"
               "author\tanchor\tcomment\tstatus\tresolution\n")
MARKUP = ("Highlight", "Underline", "StrikeOut", "Squiggly")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(text: str) -> str:
    return " ".join(text.split()).replace("\t", " ")


def rows(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[1:]
    return [line.split("\t") for line in lines if line and not line.startswith("#")]


def record(args) -> int:
    pdf = Path(args.pdf)
    if not EMISSIONS.exists():
        EMISSIONS.write_text(EMISSIONS_HEAD, encoding="utf-8")
    row = [args.date, pdf.name, sha256(pdf), str(pdf.stat().st_size), args.built_from, args.to]
    with EMISSIONS.open("a", encoding="utf-8") as f:
        f.write("\t".join(row) + "\n")
    print("recorded", pdf.name, row[2][:12])
    return 0


def annotations(pdf: Path):
    import fitz  # pymupdf

    doc = fitz.open(pdf)
    for page in doc:
        for a in page.annots() or []:
            kind = a.type[1]
            if kind in MARKUP:
                v = a.vertices or []
                quads = [fitz.Quad(v[i:i + 4]) for i in range(0, len(v), 4)]
                anchor = " ".join(page.get_textbox(q.rect) for q in quads)
            else:
                r = a.rect
                band = fitz.Rect(0, r.y0 - 40, page.rect.width, r.y1 + 40)
                anchor = page.get_textbox(band)
            info = a.info
            yield (page.number + 1, kind, clean(info.get("title", "")),
                   clean(anchor)[:240], clean(info.get("content", "")))


def pull(args) -> int:
    pdf = Path(args.pdf)
    now = sha256(pdf)
    emitted = [r for r in rows(EMISSIONS) if len(r) >= 5 and r[1] == pdf.name]
    if not emitted:
        print(f"no emission record for {pdf.name}; comparing is impossible", file=sys.stderr)
        return 2
    last = emitted[-1]
    if last[2] == now:
        print(f"{pdf.name}: bytes unchanged since emission ({now[:12]}); no comments")
        return 0
    ledger = Path(args.ledger)
    if not ledger.exists():
        ledger.write_text(LEDGER_HEAD, encoding="utf-8")
    seen = {(r[5], r[6], r[9]) for r in rows(ledger) if len(r) >= 10}
    n = len(rows(ledger))
    added = 0
    with ledger.open("a", encoding="utf-8") as f:
        for page, kind, author, anchor, comment in annotations(pdf):
            if kind in ("Link", "Widget") or (page, kind, comment) in {(int(a), b, c) for a, b, c in seen}:
                continue
            n += 1
            added += 1
            f.write("\t".join([f"C{n}", args.date, now, last[2], last[4], str(page), kind,
                               author, anchor, comment, "open", "-"]) + "\n")
    print(f"{pdf.name}: bytes changed ({last[2][:12]} -> {now[:12]}); {added} new comment(s)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("pdf")
    r.add_argument("--date", required=True)
    r.add_argument("--built-from", required=True)
    r.add_argument("--to", required=True)
    q = sub.add_parser("pull")
    q.add_argument("pdf")
    q.add_argument("--date", required=True)
    q.add_argument("--ledger", required=True)
    args = p.parse_args()
    return record(args) if args.cmd == "record" else pull(args)


if __name__ == "__main__":
    sys.exit(main())
