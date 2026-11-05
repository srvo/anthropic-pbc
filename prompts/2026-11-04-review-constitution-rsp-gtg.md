Atomic review of quotations in a working paper. Read `/Users/srvo/dev/anthropic-pbc/docs/atomic-review.md` first and follow it exactly; also AGENTS.md conventions "Checks are not beaten" and "Always pin, always verify, always breadcrumb". The author is Sloane (she/her).

SCOPE: rows in `/Users/srvo/dev/anthropic-pbc/claims/anthropic-contrapunctus.tsv` whose path is `sources/constitution.html`, `derived/rsp-v3.4.txt` or `derived/anthropic-gtg-1002.txt`.

Inputs (read-only): the claims file; the paper `docs/anthropic-contrapunctus.md` (find where each quote is used and what the paper claims with it); the sources at those paths (constitution.html is raw HTML: words may be split by tags or written as entities; derived/*.txt are pdftotext output with layout line breaks and, in the RSP, zero-width spaces); the unedited check result `docs/quote-check-2026-11-04.md`.

For EVERY row in scope (passing and failing alike):
1. Locate the passage the quotation comes from (account for markup, entities, layout breaks, zero-width spaces and curly quotes when SEARCHING, never when proposing).
2. Copy `context`: the passage around it as a reader sees it, one to three sentences; say in reason what you read through (markup, line breaks, zero-width spaces).
3. Judge question 3 (faithful): does the paper's use keep the source's meaning? The paper uses Claude's Constitution as a rubric against Anthropic; check especially that a clause about Claude's conduct is not presented as a rule for Anthropic's corporate conduct beyond what the text says, and that the RSP's conditions are not stripped.
4. Verdict per docs/atomic-review.md: verified / requote / unquote / context / not-in-source.
5. `proposed`: for requote, the source's exact words carrying the paper's point, chosen to occur once and stand alone; say in reason if the words are split by markup/layout in the pinned bytes (a finding for the author, not something to work around). For unquote, the paper's wording without quotation marks. For context, a one-line note of what the paper must change. Else `-`.
6. `reason`: one or two plain sentences.

Output: write ONLY to `/private/tmp/claude-501/-Users-srvo-dev-anthropic-pbc/c1e11076-829e-4b02-9641-6b48b095d475/scratchpad/review-const-rsp.tsv`, tab-separated, no header, columns: `label verdict source context proposed reason reviewer status` with reviewer `llm:claude (atomic review 2026-11-04)` and status `proposed`. Escape tab/newline as `\t`/`\n`. Do not edit any repository file; no scripts that transform sources; reading and grep only. Stop by ~40 turns.

Report back: counts per verdict; how many failures are caused only by layout/markup; the 5 most serious context problems in one line each.