# Hacker News corpus: method

### What practitioners say about Anthropic and AI security, read by the same witnesses

**Status: corpus HELD as ids and hashes; model output is WITNESS ONLY.** Every
score in `proposals/hacker-news/` is a proposal under
[`bert-enrichment-spec.md`](bert-enrichment-spec.md) §5, not a finding.

Version: v0.1 · 2026-11-04. Companion to
[`earnings-call-ai-corpus.md`](earnings-call-ai-corpus.md), whose unit, witnesses
and codebook it reuses so the sources can be set side by side.

## 1. Source and coverage

- `open-index/hacker-news` on Hugging Face, dataset commit `c54ced59`, ODC-BY.
  The 68 monthly files for 2021-01 to 2026-08 are pinned by SHA-256 in
  `corpus/hacker-news/MANIFEST.tsv`. 2021 is when Anthropic was founded.
- The archive's last comment is in August 2026 (`months.tsv`,
  `last_comment_utc`). September to November 2026 is not covered. It would have
  to come from the HN API by id range and be pinned the same way.
- Deleted and dead comments are excluded from every count.

## 2. Why ids only

HN commenters are mostly private individuals. The earnings-call corpus
republishes executives and analysts on the record; this one republishes nobody.
The repository holds item ids, character offsets and BLAKE3 hashes, and the text
is rebuilt locally from the pin. `verify` re-normalises, re-slices and re-hashes
every window, so the method stays checkable.

## 3. Sets and unit

Both sets are published regexes in `scripts/hn_extract.py`.

- **anthropic:** "Anthropic", excluding the anthropic principle, reasoning,
  argument, bias and selection. Also "Claude" from 2023-03-01 (the model's
  release), excluding common first-name collocations (Shannon, Monet, Debussy...).
- **ai_security:** a security term in a window that also holds an AI term
  (the earnings-call regex). Security terms include CVE, breach, exfiltration,
  vulnerability, exploit, malware, zero-day, RCE, backdoor, jailbreak, and leaked
  weights, keys or prompts. "Prompt injection" counts on its own. "Jailbreak"
  needs the AI term, because phones and Kindles are jailbroken too. "Hacked" is
  excluded, because of "hacked together".

The unit is the earnings-call window: the match sentence ±1, merged and clipped
at 1,500 characters. It is cut from a normalised comment: `<p>` becomes a blank
line, other tags are dropped, and HTML entities are unescaped. A comment can be
in both sets.

## 4. Witnesses

The same two NLI cross-encoders and the same `codebook-v0.1.tsv` as the calls
(§5 there), on Modal L40S with bfloat16, written to `proposals/hacker-news/<set>/`.
A proposed positive needs both witnesses ≥ 0.5. A comment carries a label if
any of its windows does.

## 5. What this corpus does not answer

- **HN is not the public.** It is a self-selected, English-language audience of
  developers and practitioners, many of whom build on or compete with these
  products. It is a third voice beside executives and analysts. It does not
  fill the gap of workers, users and data-center neighbours (spec §9).
- **The codebook was written for company speech.** Several hypotheses say
  "the company". On comments that is ambiguous, so `governance` and
  `disruption` read differently here than on calls.
- **Informal text is harder for zero-shot NLI.** Sarcasm, quotation and
  argument are common. κ is reported per set, and no rate is cited before a
  hand-coded sample checks it.
- **Mention is volume, not salience.** A month with a product launch has more
  Anthropic comments; rates are reported against all comments that month.

## 6. Rebuild

    uv run scripts/hn_extract.py pin && uv run scripts/hn_extract.py fetch
    uv run scripts/hn_extract.py build
    for s in anthropic ai_security; do for m in deberta modernbert; do
      uvx --with duckdb==2.0.0 --with blake3 modal run scripts/ec_classify_modal.py --model $m \
          --units .hncorpus/units-$s.parquet --out proposals/hacker-news/$s
    done; done
    uv run scripts/hn_report.py
