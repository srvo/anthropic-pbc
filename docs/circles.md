# Circles of assumption

A derivation such as PDF → text is never simply "faithful" or "unfaithful".
Each part of the content gets a colour: the highest circle at which that part
is verified, together with the measured gap.

| Circle | What is assumed or checked | Instrument |
|---|---|---|
| 0 | The source bytes, identified by digest. This is the only thing assumed. | none |
| 1 | Conservation laws measured with one instrument: every word kept, every inked pixel accounted for | poppler (`pdftotext -bbox`, `pdftoppm`) |
| 2 | The same measurement confirmed by an independent instrument | tesseract OCR of the raster, which never sees poppler's text layer |
| 3 | An untrusted proposal (LLM) that passes circles 1–2 | an LLM witness, checked by `descartes` |
| 4 | Human discernment: what no mechanical check can settle | a person |

Rasters, text layers and OCR output are not ground truth. They are
derivations from circle 0, re-run on every check and kept only as digests in
`artifacts/fidelity/<name>.instruments.tsv`. If a re-run gives a different
digest, the instruments are not reproducible and the check fails. Because
everything can be regenerated from the source, only the source is assumed.

## First measurement: the Gemini transcript (2026-11-02)

`sh stage1/fidelity.sh` produced
`artifacts/fidelity/Secure-Alternatives-to-Iroh-P2P.tsv`:

| Component | Circle | Measured |
|---|---|---|
| source bytes | 0 | reproducible from the digest |
| text (words) | 1 | 10,898 / 10,910 (99.89%) of text-layer words are present in `pdftotext` output |
| text (words) | 2 | 10,619 / 10,910 (97.33%) confirmed by OCR at the same position |
| text position | 0 | not captured: the plain-text derivation has no coordinates |
| non-text ink | 0 | 2.41% of inked pixels lie outside every word box, in 17 regions: table grids and section rules |
| tables | 0 | not captured: row/column pairings are unverified |
| reading order | 4 | open |

The largest unaccounted region on page 3 (42.5,143 → 570,307.5 pt) is
exactly the "Comparison Across Your Requirements" table grid. The ink check
found the table without being told to look for one. Any claim that depends
on which cell sits in which row therefore rests on circle 0 until a table
proposal passes a geometric check.

The 2.67% of words OCR does not confirm are mostly code (monospace
punctuation, `::`, `->`) and the box-drawing characters in diagrams. These
are differences between instruments, and they stay visible in the per-page
rows rather than being averaged away.

## Parameters (recorded in every report)

| Parameter | Value | Why |
|---|---|---|
| Scale | 2 px/pt (144 dpi) | Enough resolution for OCR. Coordinates are exact multiples of points. |
| Ink threshold | < 250 of 255 | Chrome draws table rules in light grey. A mid-grey threshold (128) missed every one of them, which the first run showed: 0 regions. |
| Mask margin | 1 pt | Glyph ink extends slightly past the font's box. |
| Minimum region | 40 px | Anti-aliasing specks are counted in the totals but not listed as regions. |

These are assumptions too, so they are printed at the top of every report.

## Next, in order

1. **Table proposals (circle 3).** An LLM proposes cells as page + box +
   text. The check: the glyphs inside each box spell the cell's text, the
   cells tile the table without overlap, the row and column bands are
   consistent, and the table's box covers the residual-ink region it
   explains. A table that passes moves its pairings from circle 0 to circle 3.
2. **Name the lost words.** Report the 12 words the plain-text derivation
   dropped.
3. **Second text-layer instrument.** A content-stream reader, so circle 2
   for text does not rest on OCR alone.

## Notes on the pasted "concentric circles" draft

That draft and this design share the structure. They differ in these places:

- It puts the 300 dpi raster in circle 0. A raster is the output of a
  renderer, which is an instrument and therefore an assumption. Here circle
  0 is the bytes alone, as Sloane specified.
- It says poppler's 42 text blocks can be checked by counting 42 `BT…ET`
  operators. They cannot. Poppler's blocks are a layout heuristic, while
  `BT/ET` is however the producer (here Skia) chose to emit text, and the two
  counts have no reason to match.
- It calls for the `image` crate. Binary PGM is a 4-field header followed by
  raw bytes, and `src/fidelity.rs` reads it with no dependency.
- It says "a mathematically verified geometric fact". A table that passes
  the geometric check proves that its cells are consistent with the page.
  It does not prove the author meant them as a table, so it is circle 3, not
  circle 1.
