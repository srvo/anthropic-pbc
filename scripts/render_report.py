#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Render edition/REPORT.md to PDF with the Praxis report writer, on the Praxis brand.

    uv run scripts/render_report.py -o /abs/path/anthropic-pbc-report.pdf

This runs exactly `./praxis report from-md edition/REPORT.md --template research --publisher praxis -o OUT`
from the Praxis checkout beside this repository (../praxis, as for dag.py), with one addition. from-md
compiles with Typst's root at praxis/report_writer, and Typst refuses to read any file outside its root,
so a markdown image in this repository cannot be found there (from-md fails with "file not found"). This
script hands Typst each chart's bytes instead of its path, and passes the image's alt text binding to
Typst's `alt` as well as to the caption from-md already makes of it. Everything else is the Praxis front
door unchanged: its eight-section check, the publisher lock, the bundled fonts and the design tokens.
No file in Praxis is changed; from-md's own temporary .typ file is written and removed as usual.

Typst writes no clock into the PDF here (the document date is the report's `date:`), so two renders of
the same REPORT.md are byte-identical with the same Typst and Praxis; see docs/report-build.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIGURE = re.compile(r'#figure\(image\("([^"\\]+)"\)')
IMAGE_MD = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", re.M)


def typst_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", required=True, help="PDF path (keep it outside the repository)")
    ap.add_argument("--report", default=str(ROOT / "edition" / "REPORT.md"))
    ap.add_argument("--praxis", default=str(ROOT.parent / "praxis"), help="Praxis checkout (default ../praxis)")
    a = ap.parse_args()
    report = Path(a.report).resolve()
    sys.path.insert(0, str(Path(a.praxis).resolve() / "report_writer"))
    import cli  # noqa: E402  (Praxis report_writer)
    import praxis_cli  # noqa: E402

    alts = {src: alt for alt, src in IMAGE_MD.findall(report.read_text(encoding="utf-8"))}
    generate = cli.generate_typst_doc

    def with_charts(doc, *args, **kw):
        def inline(m: re.Match[str]) -> str:
            src = m.group(1)
            path = (report.parent / src).resolve()
            if src not in alts or path.suffix != ".svg" or not path.is_relative_to(ROOT) or not path.is_file():
                raise ValueError(f"image {src!r}: need a markdown image line with an SVG inside {ROOT}")
            return (f"#figure(image(bytes({typst_str(path.read_text(encoding='utf-8'))}), format: \"svg\", "
                    f"alt: {typst_str(alts[src])}, width: 100%)")
        return FIGURE.sub(inline, generate(doc, *args, **kw))

    cli.generate_typst_doc = with_charts
    return praxis_cli.main(["from-md", str(report), "--template", "research", "--publisher", "praxis",
                            "-o", str(Path(a.output).resolve())])


if __name__ == "__main__":
    sys.exit(main())
