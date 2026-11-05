# Bug: quotes from HTML sources cannot be checked as published

**For:** Descartes (file in Forgejo, `EthicalCapital/monocloud` tracker, when a
Forgejo tool is available). **Found:** 2026-11-04, quote check of
`docs/anthropic-contrapunctus.md` (`docs/quote-check-2026-11-04.md`).
**Reported by:** Sloane Ortel (via Claude). **Tracked:** Entire trail #25 (HTML recipe; descartes c8c8fa7 fixed static HTML) and trail #26 (PDF line breaks in the recipe).

## What happens

`descartes check` looks for a quotation in the pinned bytes. For a PDF there is
a recorded recipe (`pdftotext -enc UTF-8 -nopgbrk`), so the check runs against
the text. For HTML there is none, so the check runs against raw markup, and a
quotation that a reader sees as one sentence fails:

- **Markup splits sentences.** The SEC's S-1 HTML puts each printed line in its
  own positioned `<div>`, so any sentence longer than a line is split by tags.
  Correct, faithful quotations fail (review rows Q012, Q014, Q016, Q017).
- **Entities.** Curly apostrophes and dashes are written as `&#8217;` and the
  like, so the published characters are not the bytes.
- **Embedded duplicates.** Anthropic's web pages (Next.js) carry the body text
  twice, once rendered and once in an embedded JSON payload, so every sentence
  "occurs more than once" (Q048, Q084). The Constitution page had the same
  defect; it was fixed by pinning its PDF instead (`70a8866`), which is not
  available for every page.

### Same defect in PDF-derived text (added after the re-run, merge e36f74e)

The PDF recipe (`pdftotext -enc UTF-8 -nopgbrk`) keeps the printed line
breaks, so a quotation that runs across a printed line fails, although its
words are the source's: 18 claims (Constitution 11, Public Benefit Report 6,
RSP 1). The RSP's text also carries a zero-width space (U+200B) at each line
edge (982 in `derived/rsp-v3.4.txt`). A reader sees one sentence; the check
sees a newline. Whether a layout line break or a zero-width space matches a
space is a general rule for Descartes to decide once, for every source, not
something to settle quote by quote.

## What should happen

A quotation should be checked against what was published, as a reader saw it
on the date it was pinned. Requirement (Sloane): match what is published at
the time it is published.

## Proposed fix

A recorded, general recipe for HTML, in Descartes, exactly like `pdftotext` for
PDF: one standard HTML-to-text tool, the same arguments for every HTML source,
recorded with `descartes derive` and re-run by the loop byte-identically. It
must render only the visible document (not scripts or embedded data) and decode
entities. It must not be tuned to any source or quotation (AGENTS.md, "Checks
are not beaten"). Candidate tools to evaluate: `pandoc -t plain`, `w3m -dump`,
`lynx -dump`; choose by determinism across versions and by handling of
positioned blocks.

Until it is fixed, quotations from HTML sources stay `requote` or fail the
check, and that failure is reported, not worked around.
