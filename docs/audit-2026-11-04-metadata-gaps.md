# Metadata we have but don't record, 2026-11-04

Question (Sloane): which accessible metadata are we omitting? "Accessible"
means it is already in the pinned bytes, the tools' own output, git, or the
build environment. An LLM agent ran read-only commands to find each gap;
three were rechecked by hand (MANIFEST columns, the PDF Info dictionary,
the `pdftotext` version). Rule at stake: AGENTS.md, "Every step emits its
metadata", and precision about where in a source a quote sits.

| Record | Omitted | Where it is accessible |
|---|---|---|
| `sources/MANIFEST.tsv` | SHA-256 (AGENTS.md requires it) | `.descartes/objects` artifact records already hold it |
| `sources/MANIFEST.tsv` | EDGAR accession, CIK, form/exhibit type, registration no., filing date | URL path, SGML header, first line of `derived/s1a1.txt` |
| `sources/MANIFEST.tsv` | PDF title, producer, creation date, page count | `pdfinfo` (e.g. Report 20 pp., created 2026-10-21) |
| `sources/MANIFEST.tsv` | fetch time, HTTP headers; pinning tool version | file mtimes; `curl --version` 8.7.1 |
| `derived/recipes.tsv` | tool version | `pdftotext -v`: 26.10.0 |
| `derived/recipes.tsv` | digest of each derived text | `.descartes/objects` only (gitignored) |
| `derived/*.txt` | page boundaries (dropped by `-nopgbrk`) | without the flag, the output differs only by form feeds |
| `claims/*.tsv` | page, source section and offset of each quote | computable: PDF form feeds; S-1 "N Table of Contents" footers (all 21 S-1 claims located uniquely) |
| `claims/*.tsv` | digest of the text the quote was checked against | Descartes computes it |
| `claims/*.steps.tsv` | commit hashes where rows say "see … history" | `git log` |
| `claims/*.review.tsv` | page of the reviewed passage | free prose only |
| `docs/emissions.tsv` | Descartes, Praxis and Typst versions, page count, dirty flag | the render's own inputs |
| `comments/*.tsv` | annotation time and position | pymupdf `modDate`, `rect` |
| emitted PDF | front-page version and commit (comment C5) | the render knows them |
| emitted PDF | Info title is "Anthropic PBC"; no Subject/Keywords/commit; CreationDate is midnight UTC, which reads as the day before in Utah | `pdfinfo -isodates` |
| emitted PDF | one of two Figure structure elements has no alt text (unverified which) | PDF structure tree |

Already right: the PDF is tagged, its language is `en`, and fonts are
embedded.

## Close first

1. Page and offset for every claim: keep page breaks in the recipe, or emit a
   page map, and use the S-1 footers.
2. SHA-256 in the manifest, plus the derived-text digest on each claim row.
3. Tool versions in the recipes and derivation records.
4. EDGAR identity (accession, form or exhibit, filing date) as manifest
   columns.
5. A full build stamp on the front page, in the PDF metadata and in
   `docs/emissions.tsv`, with a true creation time.

Items 1–3 change what Descartes records, so they belong in Descartes and
trail #26. Items 4–5 belong to this repository's records and its render.
