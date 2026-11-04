#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Render edition/REPORT.md, on the Praxis brand, as the one version: a PDF and the web page.

    uv run scripts/render_report.py -o /abs/path/anthropic-pbc-report.pdf      # PDF only (from-md)
    uv run scripts/render_report.py --bundle /abs/path/out [--publish]           # web page + PDF (bundle)

The report has one source (edition/REPORT.md) and one version; the PDF and the web page are two
renderings of it. `--bundle DIR` runs `./praxis report bundle` (Praxis refuses to write a bundle inside
a repository, so DIR is outside it); `--publish` then copies every file the bundle's manifest lists, and
the manifest, into this repository's root, replacing index.html: the page, its PDF, styles and assets. The Praxis web writer leaves local images out for now (caption only), so this
script links each chart by its path from the repository root (edition/*.svg), with its alt text: the
published page shows the committed SVGs themselves, and nothing is copied (Praxis PRINCIPLES.md P1).
The staging bundle outside the repository therefore shows captions without charts; only the published
copy resolves them.

The PDF runs exactly `./praxis report from-md edition/REPORT.md --template research --publisher praxis -o OUT`
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
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIGURE = re.compile(r'#figure\(image\("([^"\\]+)"\)')
IMAGE_MD = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", re.M)


def typst_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'


def chart(report: Path, src: str) -> Path:
    path = (report.parent / src).resolve()
    if path.suffix != ".svg" or not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f"image {src!r}: need an SVG inside {ROOT}")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    out = ap.add_mutually_exclusive_group(required=True)
    out.add_argument("-o", "--output", help="PDF path only (keep it outside the repository)")
    out.add_argument("--bundle", help="directory for the web page + PDF, outside the repository")
    ap.add_argument("--publish", action="store_true", help="with --bundle: copy the web files into the repository root")
    ap.add_argument("--report", default=str(ROOT / "edition" / "REPORT.md"))
    ap.add_argument("--praxis", default=str(ROOT.parent / "praxis"), help="Praxis checkout (default ../praxis)")
    a = ap.parse_args()
    if a.publish and not a.bundle:
        ap.error("--publish needs --bundle")
    report = Path(a.report).resolve()
    sys.path.insert(0, str(Path(a.praxis).resolve() / "report_writer"))
    import cli  # noqa: E402  (Praxis report_writer)
    import praxis_cli  # noqa: E402
    import web_html  # noqa: E402

    alts = {src: alt for alt, src in IMAGE_MD.findall(report.read_text(encoding="utf-8"))}
    generate = cli.generate_typst_doc

    def with_charts(doc, *args, **kw):
        def inline(m: re.Match[str]) -> str:
            src = m.group(1)
            if src not in alts:
                raise ValueError(f"image {src!r}: need a markdown image line")
            path = chart(report, src)
            return (f"#figure(image(bytes({typst_str(path.read_text(encoding='utf-8'))}), format: \"svg\", "
                    f"alt: {typst_str(alts[src])}, width: 100%)")
        return FIGURE.sub(inline, generate(doc, *args, **kw))

    def web_image(self, block) -> str:
        if block.src.lower().startswith("https://"):
            return web_image.praxis(self, block)
        src = html.escape(chart(report, block.src).relative_to(ROOT).as_posix(), quote=True)
        alt = html.escape(web_html.plain_text(block.alt), quote=True)
        return (f'<figure><img src="{src}" alt="{alt}">'
                f"<figcaption>{self.inlines(block.alt)}</figcaption></figure>")

    web_image.praxis = web_html.HtmlWriter._image
    cli.generate_typst_doc = with_charts
    web_html.HtmlWriter._image = web_image
    web_html._BLOCK[web_html.Image] = web_image  # the block table holds the method itself
    if a.output:
        return praxis_cli.main(["from-md", str(report), "--template", "research", "--publisher", "praxis",
                                "-o", str(Path(a.output).resolve())])
    bundle = Path(a.bundle).resolve()
    rc = praxis_cli.main(["bundle", str(report), "--publisher", "praxis", "--force", "-o", str(bundle)])
    if rc or not a.publish:
        return rc
    # Publish every file the bundle's manifest lists, and the manifest: the page links them all
    # (report.pdf, archive.html, sustainability.html, carbon.txt).
    names = [f["path"] for f in json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))["files"]]
    for name in [*names, "manifest.json"]:
        (ROOT / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(bundle / name, ROOT / name)
    print(f"published {len(names) + 1} files to {ROOT}; review `git diff`, then commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
