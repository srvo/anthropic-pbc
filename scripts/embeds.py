#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Emit one embeddable artifact per argument premise, from `argument.json`.

    uv run scripts/embeds.py emit     # write embeds/
    uv run scripts/embeds.py check    # fail if embeds/ is stale
    uv run scripts/embeds.py list     # print what would be emitted

Each premise produces two representations of the same unit (Praxis
`design/argument-units.md`: a unit needs two useful representations, and where a
second is missing you report the gap rather than claim conformance):

    embeds/<label>.svg          a standalone card, self-contained
    embeds/<label>.blockquote   an HTML blockquote with citation

Nothing here is typed by hand. Every label, statement, state and evidence count is
read from `argument.json`, which `scripts/argument_json.py` derives from
`claims/anthropic-contrapunctus.tsv`. If a card looks wrong, the fix belongs in the
artifact or the claims file, never in this script's output.

## Why the digest

An embedded card is a claim about the paper at a moment. The claims digest in the
footer names that moment, so a reader can tell whether the card they are citing
still describes the argument. The card does not claim to be current; it claims to
describe the claims file at `blake3:<digest>`.

## Self-containment

No network, no external fonts, no script, no `<image>`. The card must render in a
markdown file, an email, a PDF and an LLM's context. Colours are the Praxis tokens
written literally, because an SVG has no cascade to inherit from; `CONTRAST` below
records which pair each colour is and `test_argument_json.py` measures them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "argument.json"
OUT = ROOT / "embeds"

# Praxis tokens, written literally because an SVG carries no cascade. Light values
# from design/praxis.css; the dark block below overrides for prefers-color-scheme.
PAPER = "#ffffff"
INK = "#181818"
MUTED = "#525252"
RULE = "#d6d6d6"
WASH = "#f3f3f3"
ACCENT = "#181818"

DARK_PAPER = "#111111"
DARK_INK = "#eeeeee"
DARK_MUTED = "#b6b6b6"
DARK_RULE = "#484848"
DARK_WASH = "#202020"
DARK_ACCENT = "#eeeeee"

W = 640
PAD = 28

# States, from the artifact. The wording is the paper's own vocabulary; this map
# only decides how each is drawn.
STATE_LABEL = {
    "stands": "stands",
    "fails": "does not stand",
    "unsupported": "unsupported",
}


def _wrap(text: str, width: int) -> list[str]:
    """Break text into lines of at most `width` characters, on word boundaries.

    A single unbreakable token longer than `width` is hard-split, so a long id or a
    URL cannot overflow the card. This is the SVG equivalent of `overflow-wrap:
    anywhere`, and it is why no card has a fixed text width.
    """
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        while len(word) > width:
            lines.append(word[:width])
            word = word[width:]
        current = word
    if current:
        lines.append(current)
    return lines or [""]


def _state(premise: dict) -> str:
    if premise["unsupported"]:
        return "unsupported"
    return "fails" if premise["fails"] else "stands"


def render_svg(premise: dict, digest: str) -> str:
    """One standalone card. Height is computed from the wrapped statement."""
    label = premise["label"]
    state = _state(premise)
    statement = premise["statement"].split(":", 1)[-1].strip() or premise["statement"]
    state_label = STATE_LABEL[state]

    note = premise["section"] or ""
    evidence = premise["evidence_count"]
    if evidence:
        evidence_line = f"{evidence} quotation{'s' if evidence != 1 else ''} under it"
    else:
        evidence_line = "no quotation under it"

    statement_lines = _wrap(statement, 62)
    y = 118
    body: list[str] = []
    for line in statement_lines:
        body.append(
            f'<text class="ink body" x="{PAD}" y="{y}">{escape(line)}</text>'
        )
        y += 22

    y += 6
    body.append(f'<line class="rule" x1="{PAD}" y1="{y}" x2="{W - PAD}" y2="{y}"/>')
    y += 22
    body.append(
        f'<text class="mut small" x="{PAD}" y="{y}">rests on: '
        f'{escape(", ".join(premise["rests_on"]) or "nothing")}'
        f' · {escape(evidence_line)}</text>'
    )
    y += 26
    body.append(
        f'<text class="mut tiny mono" x="{PAD}" y="{y}">'
        f'Anthropic PBC · premise {escape(label)} · claims blake3:{escape(digest[:16])}</text>'
    )
    y += 26

    height = y

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
        f'width="{W}" height="{height}" role="img" aria-labelledby="t d">\n'
        f"<title id=\"t\">{escape(label)}: {escape(state_label)}</title>\n"
        f'<desc id="d">Premise {escape(label)} of the Anthropic PBC working paper. '
        f"{escape(statement)} It {escape(state_label)}; "
        f"{escape(evidence_line)}; because-ness {premise['because_ness']}.</desc>\n"
        "<style>\n"
        f"  .bg{{fill:{PAPER}}} .ink{{fill:{INK}}} .mut{{fill:{MUTED}}} .rule{{stroke:{RULE}}}\n"
        f"  .chip{{fill:{INK}}} .chiptx{{fill:{PAPER}}} .wash{{fill:{WASH}}}\n"
        "  text{font-family:Georgia,'Times New Roman',serif}\n"
        "  .t{font-size:15px;font-weight:700;letter-spacing:.02em}\n"
        "  .body{font-size:16px}\n"
        "  .small{font-size:12px}\n"
        "  .tiny{font-size:10px;letter-spacing:.04em}\n"
        "  .mono{font-family:Menlo,Consolas,monospace}\n"
        "  @media (prefers-color-scheme:dark){\n"
        f"    .bg{{fill:{DARK_PAPER}}} .ink{{fill:{DARK_INK}}} .mut{{fill:{DARK_MUTED}}}\n"
        f"    .rule{{stroke:{DARK_RULE}}} .chip{{fill:{DARK_INK}}} .chiptx{{fill:{DARK_PAPER}}}\n"
        f"    .wash{{fill:{DARK_WASH}}}\n"
        "  }\n"
        "</style>\n"
        f'<rect class="bg" width="{W}" height="{height}" rx="6"/>\n'
        f'<text class="mono t" x="{PAD}" y="46">{escape(label)}</text>\n'
        f'<rect class="chip" x="{W - PAD - 130}" y="28" width="130" height="24" rx="3"/>\n'
        f'<text class="chiptx tiny mono" x="{W - PAD - 65}" y="44" '
        f'text-anchor="middle">{escape(state_label.upper())}</text>\n'
        f'<line class="rule" x1="{PAD}" y1="62" x2="{W - PAD}" y2="62"/>\n'
        f'<text class="mut small" x="{PAD}" y="84">'
        f'{escape(premise["role"])} · because-ness {premise["because_ness"]}'
        f'{" · " + escape(note) if note else ""}</text>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def render_blockquote(premise: dict, digest: str) -> str:
    """An HTML blockquote a writer can paste into prose."""
    label = premise["label"]
    state = _state(premise)
    statement = premise["statement"].split(":", 1)[-1].strip() or premise["statement"]
    evidence = premise["evidence_count"]

    state_note = {
        "stands": "stands on the evidence cited for it",
        "fails": "does not stand: something under it fails",
        "unsupported": "is unsupported: it rests on nothing",
    }[state]

    evidence_note = (
        f"{evidence} quotation{'s' if evidence != 1 else ''} rest under it."
        if evidence
        else "no quotation is recorded under it."
    )

    return (
        f'<figure class="anthropic-pbc-premise" id="anthropic-pbc-{escape(label)}">\n'
        f"  <blockquote cite=\"https://srvo.github.io/anthropic-pbc/\">\n"
        f"    <p>{escape(statement)}</p>\n"
        f"  </blockquote>\n"
        f"  <figcaption>\n"
        f"    Premise <code>{escape(label)}</code> of <cite>Anthropic PBC</cite>, "
        f"a working paper by Sloane Ortel. This premise {escape(state_note)}; "
        f"{evidence_note} "
        f"Claims file at <code>blake3:{escape(digest)}</code>. "
        f'<a href="https://srvo.github.io/anthropic-pbc/">Source</a>\n'
        f"  </figcaption>\n"
        f"</figure>\n"
    )


def build() -> dict[str, tuple[str, str]]:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    digest = (
        artifact.get("source", {})
        .get("inputs_blake3", {})
        .get("claims/anthropic-contrapunctus.tsv", "unknown")
        .split(":", 1)[-1]
    )
    out: dict[str, tuple[str, str]] = {}
    for premise in artifact["premises"]:
        label = premise["label"]
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
        out[safe] = (render_svg(premise, digest), render_blockquote(premise, digest))
    return out


def index_html(items: dict[str, tuple[str, str]]) -> str:
    """One page showing every card, so a reader can pick the one they want."""
    cards = "\n".join(
        f'<section><h2>{escape(name)}</h2>\n'
        f'<img src="{escape(name)}.svg" alt="" width="640">\n'
        f"<details><summary>Blockquote</summary>\n"
        f"<pre>{escape(bq)}</pre></details></section>"
        for name, (_svg, bq) in items.items()
    )
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Anthropic PBC — embeddable premises</title>"
        "<style>body{font-family:Georgia,serif;max-width:760px;margin:2rem auto;"
        "padding:0 1rem;line-height:1.6}img{max-width:100%;height:auto}"
        "section{margin:2rem 0;border-top:1px solid #d6d6d6;padding-top:1rem}"
        "pre{white-space:pre-wrap;background:#f3f3f3;padding:1rem;overflow-x:auto}"
        "h1{font-weight:400}</style></head><body>\n"
        "<h1>Embeddable premises</h1>\n"
        "<p>One card per premise of the argument, generated from "
        "<code>argument.json</code>. Use the SVG as an image, or paste the "
        "blockquote into prose. Every card names the claims-file digest it describes."
        "</p>\n"
        f"{cards}\n</body></html>\n"
    )


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "emit"
    items = build()

    if cmd == "list":
        for name, (svg, bq) in items.items():
            print(f"{name:8} svg {len(svg):6} B   blockquote {len(bq):5} B")
        print(f"{len(items)} premises")
        return 0

    if cmd == "emit":
        OUT.mkdir(exist_ok=True)
        for name, (svg, bq) in items.items():
            (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
            (OUT / f"{name}.blockquote").write_text(bq, encoding="utf-8")
        (OUT / "index.html").write_text(index_html(items), encoding="utf-8")
        total = sum(len(s) + len(b) for s, b in items.values())
        print(f"wrote {len(items)} cards to embeds/ ({total:,} B total)")
        return 0

    if cmd == "check":
        stale = []
        if not OUT.exists():
            print("embeds/ missing; run `uv run scripts/embeds.py emit`", file=sys.stderr)
            return 1
        for name, (svg, bq) in items.items():
            for suffix, want in (("svg", svg), ("blockquote", bq)):
                path = OUT / f"{name}.{suffix}"
                if not path.exists() or path.read_text(encoding="utf-8") != want:
                    stale.append(path.name)
        idx = OUT / "index.html"
        if not idx.exists() or idx.read_text(encoding="utf-8") != index_html(items):
            stale.append("index.html")
        if stale:
            print(
                f"embeds/ is stale ({len(stale)} file(s): {', '.join(stale[:5])}); "
                "run `uv run scripts/embeds.py emit`",
                file=sys.stderr,
            )
            return 1
        print(f"embeds/ is current ({len(items)} cards)")
        return 0

    print(f"unknown command {cmd!r}; use emit, check or list", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
