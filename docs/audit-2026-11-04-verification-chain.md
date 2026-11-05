# Adversarial audit of the verification chain, 2026-11-04

Question (Sloane: "really lock this down"): how can a wrong or unverifiable
record pass the checks on this paper without any check failing? An LLM agent
audited the chain read-only and reproduced its cases on scratch copies. Each
finding is listed with what was done. Fixes are on the Descartes branch
`witness-prompt-digest` (commits 1a44f60, 8ef1b42, d828de8, e7b3cb6), **not
merged**: see "Decisions open".

State when audited: all 15 sources matched their BLAKE3 in
`sources/MANIFEST.tsv`, and all 7 `derived/*.txt` rebuilt byte-identical from
their recipes. Nothing had drifted; the gaps were that nothing would catch it.

| # | Finding (reproduced unless marked) | Status |
|---|---|---|
| 1 | No gate runs `descartes check`: the hooks and CI run only `scripts/seal.py check`, so "passed" means an `ok` line read from a doc, not an exit code. | **Open.** The hook and workflow files belong to another session's uncommitted work. |
| 2 | The check trusts whatever bytes are on disk: an edited `derived/*.txt` or raw source passed; `descartes derive` records without running the tool; three rows quote raw HTML. | **Closed for articles** by `stage1/article.sh`: manifest bytes and BLAKE3, recipes replayed byte for byte, every derived file has a recipe, evidence must be a recipe output. Binding this inside `descartes check` itself is Entire trail #26. |
| 3 | A quote can pass without saying what the source says: no word boundary, no length floor, spans across headings and page numbers; a match inside an HTML comment passed. Live case Q022b dropped "necessarily". | **Partly closed.** Quotes match whole words only (d828de8). Q022b requoted (ceb603f). Raw HTML refused as evidence. **Open:** a minimum quote length, refusing spans across paragraph breaks, and storing context with the evidence. |
| 4 | The witness rule was easy to get past: `LLM:`, a leading space, `llm-x`, a second `prompt=`, and any file on disk under `prompts/`. | **Closed.** Witness kinds are a closed set (`human`, `llm`, `org`, `doi`, `arxiv`); exactly one `prompt=`; the digest must name a file committed at HEAD. **Open:** tying each row to the step that produced it. |
| 5 | Nothing checks the review or steps files: 24 claim labels have no review row and 20 review labels have no claim (split and renamed labels); review `context` is not verbatim in most rows. | **Open.** Needs a mechanical review check and a data fix of the review file. |
| 6 | A claim with one good and one fabricated evidence row printed `ok`. | **Closed.** Any failed row fails its claim (d828de8). |
| 7 | (Plausible) a claim with no evidence of its own passes on its parents alone. | **Open**, minor. |

Also found while fixing: `verify` does not check witness format on claim nodes
already in a store (only claims files are checked); a pdftotext footnote marker
glued to a word ("profiles92") makes a faithful quote fail the word-boundary
rule, a false failure kept on purpose (correctness first).

## Effect on this paper
`descartes check` (d828de8, binary sha256 `7cac773c…`, reproducible): 74 claims
ok, unchanged by the new rules. `stage1/article.sh`: inputs clean; Q007, Q048
and Q084 refused for citing raw HTML; both prompt digests match files at HEAD.

## Effect on Descartes's own claims
72 rows fail the prompt rule (interactive sessions and pasted transcripts, all
honest about having no prompt file), 8 fail as witness kind `model:`, and 1
faithful quote fails the word-boundary rule on a footnote marker.

## Decisions open (Sloane)
- Merge the branch, which requires migrating those Descartes rows and its loop's
  expected results (the Descartes owner).
- Run `descartes check` / `article.sh` as a gate in pre-commit and CI.
- A minimum quote length, and whether a quote may cross a paragraph break.
