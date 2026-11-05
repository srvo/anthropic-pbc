Draft a Descartes claims file listing every quotation in one working paper, for its author (Sloane, she/her) to confirm. This is editorial inventory work, not a check: do not run descartes, do not write scripts that transform sources, do not alter any quotation.

## Inputs
- The paper: `docs/anthropic-contrapunctus.md` (branch ec-ai-corpus).
- The pinned sources: `sources/MANIFEST.tsv` (columns id, role, fetched, url, path, bytes, blake3). Paths there are relative to `sources/`. The source files themselves are gitignored and absent from your worktree; you only need the manifest.
- The format: Descartes claims files, six tab-separated columns `label rests_on witness statement path quote` (see `docs/descartes-spec.md` §8). `rests_on` is `-`. Lines starting `#` are comments. In `quote`, a literal tab/newline/backslash must be written `\t`, `\n`, `\\`.
- Read `AGENTS.md`, convention "Checks are not beaten": quotes go in exactly as the paper prints them; never trim, lengthen or normalise a quote to make it more likely to match. A failing check later is a finding.

## Task
Write `claims/anthropic-contrapunctus.tsv`:
1. Find every quotation the paper attributes to an outside source: text in quotation marks (straight or curly) or *italic quotes* or blockquotes presented as a source's words. Skip the paper's own epigraphs/slogans and its quotations of itself.
2. One row per quotation. `label` Q001, Q002… in paper order. `witness` = `llm:claude-opus-5-5 proposed; confirm=human:sloane`. `statement` = one short plain sentence of what the quote shows, in the paper's terms, including the paper section (e.g. "§4.1: the charter purpose names the long-term benefit of humanity"). `quote` = the quoted words exactly as printed in the paper, without the surrounding quotation marks, ellipses kept as printed.
3. `path`: the pinned source the paper attributes it to, as `sources/<path from MANIFEST>` (Report → `sources/pbc-report-2026.pdf`, S-1 → `sources/s1a1.htm`, Claude's Constitution → `sources/constitution.html`, RSP → `sources/rsp-v3.4.pdf`, Lemonade 10-K, CoreWeave S-1 as listed). Do NOT invent derived-text paths; materialisation is a later step.
4. A quotation whose source is not pinned in the manifest (court opinions, news, people's spoken remarks, the DGCL, academic studies, etc.): write it as a comment row `# UNPINNED Q0nn<TAB>statement<TAB>attributed source as the paper names it<TAB>quote` so nothing is lost, and count it.
5. A quotation whose attribution is ambiguous: comment row `# AMBIGUOUS …` with the candidate sources.
6. Header comments: what the file is, that it is a draft for Sloane to confirm, that paths point at pinned sources not yet materialised, and that no check has been run.

## Rules
- Touch only `claims/anthropic-contrapunctus.tsv`. Commit it once, message ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never sign.
- No Python or other scripts that transform text; reading the paper and writing the TSV by hand (or with plain editor tooling) is fine. Use `grep` to find quotation marks if helpful.
- Stop by ~40 turns; commit what is complete and say what is not.

## Report (concise)
Commit hash; counts: pinned rows per source, UNPINNED, AMBIGUOUS, total; the five quotes you think most likely to fail an exact match and why (curly vs straight quotes, ellipses, compressions the paper itself flags, line-broken PDF text) — as findings, not fixes; anything you could not classify.