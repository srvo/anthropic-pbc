#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Render the working paper, on the Praxis brand, as the one version: a PDF and the web page.

    uv run scripts/render_report.py --descartes BIN -o /abs/path/anthropic-pbc.pdf     # PDF only (from-md)
    uv run scripts/render_report.py --descartes BIN --bundle /abs/path/out              # web page + PDF (bundle)

The paper (docs/anthropic-contrapunctus.md) has one source and one version; the PDF and the web page
are two renderings of it. Emitted files are never committed: they are written outside the repository
and attached to a release (Sloane, 2026-11-04).

Every rendering ends with a generated appendix, "Verification chain", so the document carries its own
evidence trail (Sloane, 2026-11-04). It is built when the document is built, never typed:
- the result of running Descartes's article verifier (stage1/article.sh) on this repository now:
  manifest, recipe replay, and `descartes check` on the claims file, with failing claims by cause;
- the steps that produced the claims (claims/anthropic-contrapunctus.steps.tsv);
- the status of the verification-chain audit (the table in docs/audit-2026-11-04-verification-chain.md);
- the Entire trails the repository cites (docs/trails.tsv, refreshed by docs/trails-refresh.sh).
It names the paper's commit, whether the inputs had uncommitted changes, the Descartes checkout's
commit and the binary's SHA-256. Nothing in it reads a clock: the document date is the date of the
paper's last commit.

The paper is ordered by its question, not by the Praxis research standard's eight sections, so it is
rendered with Praxis's --legacy-layout. The front matter is added here, outside the repository, in a
temporary copy; the paper itself carries none.

from-md compiles with Typst's root at praxis/report_writer, and Typst refuses to read any file outside
its root, so this script hands Typst each chart's bytes instead of its path, and passes the image's alt
text to Typst's `alt`. The Praxis web writer leaves local images out for now (caption only), so the web
page links each chart by its path from the repository root. No file in Praxis is changed.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "docs" / "anthropic-contrapunctus.md"
CLAIMS = "claims/anthropic-contrapunctus.tsv"
STEPS = ROOT / "claims" / "anthropic-contrapunctus.steps.tsv"
AUDIT = ROOT / "docs" / "audit-2026-11-04-verification-chain.md"
TRAILS = ROOT / "docs" / "trails.tsv"
INPUTS = ["docs/anthropic-contrapunctus.md", CLAIMS, "claims/anthropic-contrapunctus.steps.tsv",
          "sources/MANIFEST.tsv", "derived/recipes.tsv", "prompts"]
FIGURE = re.compile(r'#figure\(image\("([^"\\]+)"\)')
IMAGE_MD = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", re.M)
CHECK_LINE = re.compile(r"^FAIL\t([^:\t]+\.tsv):(\d+): (.*)$")


def typst_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'


def chart(base: Path, src: str) -> Path:
    path = (base.parent / src).resolve()
    if path.suffix != ".svg" or not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f"image {src!r}: need an SVG inside {ROOT}")
    return path


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def tsv_rows(path: Path) -> list[list[str]]:
    """Data rows of a TSV, comments and the header row dropped."""
    rows = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
    return rows[1:]


def cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def short(s: str) -> str:
    """Shorten every 64-hex digest to 12 characters for the page; full values stay in the records."""
    return re.sub(r"\b([0-9a-f]{12})[0-9a-f]{52}\b", r"\1…", s)


def labels_by_line(path: Path) -> dict[int, str]:
    return {n: line.split("\t", 1)[0] for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if line and not line.startswith("#")}


def verification_appendix(descartes: Path, descartes_root: Path) -> str:
    article = descartes_root / "stage1" / "article.sh"
    if not article.is_file():
        raise SystemExit(f"{article} not found: the appendix needs Descartes's article verifier")
    env = {**os.environ, "DESCARTES": str(descartes)}
    run = subprocess.run(["sh", str(article), str(ROOT), CLAIMS], cwd=ROOT, env=env, capture_output=True, text=True)
    lines = run.stdout.splitlines()
    rederived = [l for l in lines if l.startswith("ok\tre-derived")]
    summary = next((l.split("\t")[2:] for l in lines if l.startswith("summary\t")), ["no summary"])
    manifest = next((l.removeprefix("article: manifest").strip() for l in lines if l.startswith("article: manifest")), "?")
    prompts = next((l.removeprefix("article: prompts").strip() for l in lines if l.startswith("article: prompts")), "none named")
    labels = labels_by_line(ROOT / CLAIMS)
    causes: dict[str, list[str]] = {}
    other: list[str] = []
    for l in lines:
        if not l.startswith("FAIL\t"):
            continue
        m = CHECK_LINE.match(l)
        if m and m.group(1) == CLAIMS:
            msg = m.group(3)
            if msg.endswith("has no surviving evidence"):
                continue  # the consequence of the row failure already listed
            cause = re.sub(r'^(evidence \S+ is not a recipe output).*', r"\1", msg.split(': "')[0])
            causes.setdefault(cause, []).append(labels.get(int(m.group(2)), f"line {m.group(2)}"))
        else:
            other.append(l.removeprefix("FAIL\t"))
    dirty = git("status", "--porcelain", "--", *INPUTS)
    head = git("rev-parse", "--short=12", "HEAD")
    d_head = git("rev-parse", "--short=12", "HEAD", cwd=descartes_root)
    d_dirty = git("status", "--porcelain", "--", "stage1", "src", "tools", cwd=descartes_root)
    sha = hashlib.sha256(descartes.read_bytes()).hexdigest()

    steps = [[r[0], r[1], short(r[3]) if len(r) > 3 else "", short(r[5]) if len(r) > 5 else "", r[6] if len(r) > 6 else ""]
             for r in tsv_rows(STEPS)]
    audit = [l for l in AUDIT.read_text(encoding="utf-8").splitlines() if l.startswith("| ")]
    trails = tsv_rows(TRAILS)

    parts = [
        "### Appendix F. Verification chain (generated at build)",
        "",
        "*Built with the document from the records in the repository; nothing in this appendix is typed by hand. "
        f"Paper commit `{head}`{' with uncommitted changes to its inputs' if dirty else ''}; "
        f"Descartes checkout `{d_head}`{' with uncommitted changes' if d_dirty else ''}; "
        f"Descartes binary SHA-256 `{short(sha)}`. Digests are shortened here; full values are in the records.*",
        "",
        f"**Result: {'PASS' if run.returncode == 0 else 'FAIL'}.** The article verifier ran unsandboxed. "
        f"Manifest: {manifest}. Recipes: {len(rederived)} re-derived, byte-identical to the text the checks use. "
        f"Prompts: {prompts}. Claims: {', '.join(summary)}.",
        "",
    ]
    if causes:
        parts += ["**Failing claims, by cause.** A failure is a finding, never fitted to pass (AGENTS.md).", "",
                  table(["Cause", "Claims"], [[c, ", ".join(ls)] for c, ls in causes.items()]), ""]
    if other:
        parts += ["**Other problems.**", ""] + [f"- {cell(o)}" for o in other] + [""]
    parts += [
        "**Steps that produced the claims** (`claims/anthropic-contrapunctus.steps.tsv`).", "",
        table(["Step", "Kind", "Prompt", "Outputs", "Commit"], steps), "",
        "**Audit of the verification chain** (`docs/audit-2026-11-04-verification-chain.md`).", "",
        *audit, "",
        "**Trails** (Entire project et/ec1c; snapshot `docs/trails.tsv`).", "",
        table(["Trail", "Status", "Intent"], [[f"#{r[0]}", r[1], r[2]] for r in trails]), "",
        "Corrections to this paper are in §9, Errata.", "",
    ]
    return "\n".join(parts)


HTML_BLOCK = re.compile(r"^<(?:!--|/?[A-Za-z])")


def without_html_blocks(lines: list[str]) -> list[str]:
    """Drop raw HTML blocks: as in CommonMark, a line starting with a tag or comment opens one, and the
    next blank line closes it. The Praxis writers print raw HTML as literal text, so web-only markup (the
    paper's figure gallery) stays out of these renderings."""
    out, skipping = [], False
    for line in lines:
        if skipping:
            skipping = line.strip() != ""
            continue
        if HTML_BLOCK.match(line):
            skipping = True
            continue
        out.append(line)
    return out


def compose(paper: Path, appendix: str) -> str:
    text = paper.read_text(encoding="utf-8")
    lines = without_html_blocks(text.splitlines())
    if not lines or not lines[0].startswith("# "):
        raise ValueError("the paper must start with its '# ' title")
    title = lines[0][2:].strip()
    date = git("log", "-1", "--format=%cs", "--", paper.relative_to(ROOT).as_posix())
    front = "\n".join([
        "---", f"title: {typst_str(title)}", 'author: "Sloane Ortel"', f'date: "{date}"',
        'classification: "Working paper"', "template: research", "presentation: praxis", "publisher: praxis",
        "toc_depth: 0", "---", ""])
    return front + "\n".join(lines[1:]) + "\n\n" + appendix + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    out = ap.add_mutually_exclusive_group(required=True)
    out.add_argument("-o", "--output", help="PDF path only (keep it outside the repository)")
    out.add_argument("--bundle", help="directory for the web page + PDF, outside the repository")
    ap.add_argument("--report", default=str(PAPER))
    ap.add_argument("--praxis", default=str(ROOT.parent / "praxis"), help="Praxis checkout (default ../praxis)")
    ap.add_argument("--descartes", required=True, help="descartes binary that checks the claims")
    ap.add_argument("--descartes-root", default=str(ROOT.parent / "descartes"),
                    help="Descartes checkout holding stage1/article.sh (default ../descartes)")
    a = ap.parse_args()
    paper = Path(a.report).resolve()
    sys.path.insert(0, str(Path(a.praxis).resolve() / "report_writer"))
    import cli  # noqa: E402  (Praxis report_writer)
    import praxis_cli  # noqa: E402
    import web_html  # noqa: E402

    text = compose(paper, verification_appendix(Path(a.descartes).resolve(), Path(a.descartes_root).resolve()))
    alts = {src: alt for alt, src in IMAGE_MD.findall(text)}
    generate = cli.generate_typst_doc

    def with_charts(doc, *args, **kw):
        def inline(m: re.Match[str]) -> str:
            src = m.group(1)
            if src not in alts:
                raise ValueError(f"image {src!r}: need a markdown image line")
            path = chart(paper, src)
            return (f"#figure(image(bytes({typst_str(path.read_text(encoding='utf-8'))}), format: \"svg\", "
                    f"alt: {typst_str(alts[src])}, width: 100%)")
        return FIGURE.sub(inline, generate(doc, *args, **kw))

    def web_image(self, block) -> str:
        if block.src.lower().startswith("https://"):
            return web_image.praxis(self, block)
        src = html.escape(chart(paper, block.src).relative_to(ROOT).as_posix(), quote=True)
        alt = html.escape(web_html.plain_text(block.alt), quote=True)
        return (f'<figure><img src="{src}" alt="{alt}">'
                f"<figcaption>{self.inlines(block.alt)}</figcaption></figure>")

    web_image.praxis = web_html.HtmlWriter._image
    cli.generate_typst_doc = with_charts
    web_html.HtmlWriter._image = web_image
    web_html._BLOCK[web_html.Image] = web_image  # the block table holds the method itself
    # The composed copy lives outside the repository, beside nothing (emitted files are never committed).
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / paper.name
        source.write_text(text, encoding="utf-8")
        if a.output:
            return praxis_cli.main(["from-md", str(source), "--template", "research", "--publisher", "praxis",
                                    "--legacy-layout", "-o", str(Path(a.output).resolve())])
        return praxis_cli.main(["bundle", str(source), "--publisher", "praxis", "--force", "--legacy-layout",
                                "-o", str(Path(a.bundle).resolve())])


if __name__ == "__main__":
    sys.exit(main())
