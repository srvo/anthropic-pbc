Atomic review of quotations in a working paper. Read `/Users/srvo/dev/anthropic-pbc/docs/atomic-review.md` first and follow it exactly; also AGENTS.md conventions "Checks are not beaten" and "Always pin, always verify, always breadcrumb". The author is Sloane (she/her).

SCOPE: rows in `/Users/srvo/dev/anthropic-pbc/claims/anthropic-contrapunctus.tsv` whose path is `sources/s1a1.htm`, `sources/dgcl-c001-sc15.html`, `sources/anthropic-misuse-aug-2025.html` or `sources/anthropic-productivity-gains.html`.

Inputs (read-only): the claims file; the paper `docs/anthropic-contrapunctus.md` (find where each quote is used and what the paper claims with it); the pinned HTML sources at those paths (raw HTML: words may be split by tags or written as entities such as &#8217;; grep with care; the S-1 is 14 MB, so grep, do not read whole); the unedited check result `docs/quote-check-2026-11-04.md`.

For EVERY row in scope (passing and failing alike):
1. Locate the passage in the source the quotation comes from (search key words; account for markup, entities and curly quotes when SEARCHING, but never when proposing).
2. Copy `context`: the source passage around it as a reader sees it (tags removed by you reading, entities read as characters), one to three sentences; say in reason that markup was read through.
3. Judge question 3 (faithful): does the paper's use keep the source's meaning? Watch for: paraphrase in quotation marks, joined fragments, cut qualifiers/conditions/negations, hedges made facts, plans made results, one example as the general case.
4. Verdict per docs/atomic-review.md: verified / requote / unquote / context / not-in-source.
5. `proposed`: for requote, the source's exact words that carry the paper's point, chosen to occur once in the source and to stand alone; note in reason if the words are split by markup in the raw HTML (that is a finding for the author: an HTML source may need a recorded text derivation, which is her decision, not yours). For unquote, the paper's wording without quotation marks. For context, a one-line note of what the paper must change. Else `-`.
6. `reason`: one or two plain sentences.

Output: write ONLY to `/private/tmp/claude-501/-Users-srvo-dev-anthropic-pbc/c1e11076-829e-4b02-9641-6b48b095d475/scratchpad/review-s1.tsv`, tab-separated, no header, columns: `label verdict source context proposed reason reviewer status` with reviewer `llm:claude (atomic review 2026-11-04)` and status `proposed`. Escape any tab/newline in a field as `\t`/`\n`. Do not edit any repository file; do not write scripts that transform sources; reading and grep only. Stop by ~40 turns.

Report back: counts per verdict; how many failures are caused only by markup/entities splitting the words; and the 5 most serious context problems in one line each.