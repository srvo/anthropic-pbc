# Earnings-call AI corpus: method

### What S&P 500 companies say about AI on their calls, and how the repository reads it

**Status: corpus HELD as verbatim text; model output is WITNESS ONLY.** The
corpus files are deterministic extractions that `verify` re-checks byte for
byte. Every model score in `proposals/` is a proposal under
[`bert-enrichment-spec.md`](bert-enrichment-spec.md) §5. It is not a verdict
or a finding, and it is not evidence that any risk materialised.

Version: v0.1 · 2026-11-04. Companion to
[`anthropic-contrapunctus.md`](anthropic-contrapunctus.md) Appendix E and
[`risk-factor-corpus.md`](risk-factor-corpus.md). This file does not edit the
paper or its hash.

## 1. Source and universe

- **Transcripts.** `defeatbeta/yahoo-finance-data`, table
  `stock_earning_call_transcripts`, pinned to dataset commit `31ee0261`. The file
  is 2,294,997,554 bytes. Its BLAKE3 is in `corpus/earnings-calls/MANIFEST.tsv`.
  Its SHA-256 equals the Git LFS object id Hugging Face publishes for the file.
  The full table holds 240,536 calls across 6,592 tickers, fiscal 2005–2027. It
  is ODC-BY 1.0, attribution in `corpus/earnings-calls/README.md`.
- **Universe.** The constituents table of Wikipedia's "List of S&P 500
  companies", revision 1382178819 (2026-10-27): 503 tickers, all with CIK.
  This is **today's** index, applied backwards. A firm that left the index
  before 2026-10-27 is absent, so the panel has survivorship bias. A
  point-in-time membership history is not built.
- **Coverage.** 499 of 503 tickers have transcripts. BRK-B, ED, EXPD and NVR
  have none in the source, and their absence is not a finding about them. There
  are 33,978 S&P 500 calls in total.
  - 203 are second listings of one call under another share class: GOOGL→GOOG,
    NWSA→NWS, FOXA→FOX, plus one COR call identical to an AMT call, which is a
    source mis-filing.
  - 153 calls are stubs of two paragraphs or fewer.
  - All rates use the remaining unique, non-stub calls as the denominator
    (`calls.tsv`).

## 2. Unit

A **window** is the sentence containing an AI term, plus one sentence either
side. Overlapping windows in the same paragraph are merged. A window longer
than 1,500 characters (a run-on transcript "sentence") is clipped to 600
characters around each match and snapped to spaces. Each window is stored as
`[start_char, end_char)` of its paragraph, with BLAKE3 of both. `verify`
re-slices every window and re-hashes it.

The source paragraph is the wrong unit. Its median is about 900 characters,
but its 90th percentile is about 8,700 and its maximum about 56,000, because
whole prepared remarks are stored as one paragraph.

## 3. Term match

Published in `scripts/ec_extract.py` as six families:

- `AI`, `A.I.`, `GenAI` and `AGI` (case-sensitive)
- artificial intelligence and generative AI/models
- machine/deep learning and neural nets
- LLM and large language model
- named vendors and assistants: ChatGPT, OpenAI, Anthropic, Claude, Gemini, Copilot
- agentic and AI agents

The match is a recall filter, not a classifier. False positives are expected,
for example "Gemini" the exchange, "Claude" as a first name, or a product
called Copilot. The `about_ai` hypothesis below exists to catch them.

Result: 28,602 paragraphs and 38,600 windows.

## 4. Speaker role (heuristic)

The source gives a speaker name, not a role. A name heard on the calls of at
least three different issuers across the full 6,592-ticker table is tagged
`analyst_heuristic`, because sell-side analysts cover many firms. Other names
are `issuer_heuristic`, and "Operator" is `operator`. Common names collide and
executives move between firms, so the tag is reported with its name and never
as fact.

## 5. Witnesses

Two zero-shot NLI cross-encoders of different architecture, run independently:

| Witness | Model @ revision | License |
|---|---|---|
| DeBERTa | `MoritzLaurer/deberta-v3-large-zeroshot-v2.0` @ `cf44676c` | MIT |
| ModernBERT | `MoritzLaurer/ModernBERT-large-zeroshot-v2.0` @ `a51e07b5` | Apache-2.0 |

Each window is scored against all 16 hypotheses in `codebook-v0.1.tsv`:

- `about_ai`
- stance: `ai_risk` and `ai_opportunity`
- 12 AI risk types
- `governance`, which marks a described control mechanism and is the hook
  into the Risk–Governance Index

score = P(entailment). Nothing is trained, and no label comes from an LLM.

- **Precision and hardware.** bfloat16 on Modal L40S GPUs (§9). On a
  200-window check against float32 (on MPS), the mean absolute difference was 0.0013, the maximum
  0.036, and 5 of 3,200 scores (0.16%) crossed 0.5.
- **What is recorded.** `run-<model>.json` pins every input hash, model
  revision and library version.
- **What is not claimed.** Reproducibility across hardware (spec §5, Route B).

A **proposed positive** requires both witnesses to score ≥ 0.5. Each witness's
own count and Cohen's κ between them are reported beside it
(`report/agreement.tsv`), so disagreement stays visible.

## 6. Exploratory topic map

`scripts/ec_topics.py` runs BERTopic: all-mpnet-base-v2 embeddings at a
pinned revision, UMAP with seed 42, and HDBSCAN with a minimum cluster size of
60. It is a reading aid for choosing what to hand-code next. Spec §9 bars
clusters and embeddings as evidence, so no topic is cited as a finding. Every
topic lists window ids that resolve to verbatim text.

## 7. What this corpus does not answer

- **A mention is not an exposure, and an exposure is not a loss.** Calls are
  promotional and forward-looking. Whether a risk said on a call was
  *governed* is the Appendix E join: call language against 10-K Item 1A,
  Item 106 and the 0–5 mechanism test. Whether it *materialised* needs the
  8-K and enforcement joins.
- **Silence on a call is not absence of risk.** It is silence, and must be
  counted as such against the denominator.
- **Only citable voices are heard.** Executives and the analysts who cover
  them speak on a call. Workers, users and data-center neighbours do not, so
  their side is scored as unmeasured, never as no harm (spec §9).
- **Gate not yet passed.** No human gold set exists yet for this codebook,
  so witness precision is unknown. Before any rate is cited, a stratified
  hand-coded sample must report precision and recall per hypothesis (spec
  §7, go criterion a).

## 8. Rebuild

    uv run scripts/ec_extract.py fetch && uv run scripts/ec_extract.py constituents
    uv run scripts/ec_extract.py build            # verifies on completion
    # witnesses: Modal GPUs (default), or locally with scripts/ec_classify.py
    uvx --with duckdb==2.0.0 --with blake3 modal run scripts/ec_classify_modal.py --model deberta
    uvx --with duckdb==2.0.0 --with blake3 modal run scripts/ec_classify_modal.py --model modernbert
    uv run scripts/ec_report.py
    uv run scripts/ec_risk_series.py              # AI-as-risk time series, 12-month ranking, verbatim quotes
    uv run scripts/ec_topics.py

## 9. Compute

The witnesses are GPU-bound, at 617,600 window×hypothesis pairs per model.
These are the measured options (bfloat16, DeBERTa-v3-large):

| Where | Throughput | Notes |
|---|---|---|
| Modal L40S | 1,443 pairs/s per GPU | **Default.** `scripts/ec_classify_modal.py`, up to 8 GPUs in parallel. List price $0.000542/s, about $0.23 of GPU time per model on one GPU, plus container start-up. The Starter plan includes $30/month and up to 10 concurrent GPUs. Auth comes from the local `modal` profile via `uvx`. |
| Apple M5 (MPS) | 134–152 pairs/s | `scripts/ec_classify.py`, about 1.2+ h per model. Shards resume after interruption. |
| RunPod | not yet measured | API key in BWS as `RUNPOD_API_KEY`. Not wired up; Modal covered the need. |
| k3s on the Proxmox cluster | not yet measured | The hosts are CPU-only (Hetzner EX44, 20 threads; no GPU), and a VM is bounded by one node. To use them, run `ec_classify.py --workers N --worker i` on each node, with float32 and `--threads`, then `--merge-only`. Best use is a full-corpus float32 cross-check, not speed. |

Shards are tagged by model, dtype and backend (`modal-L40S`, or none for a
local run), so scores from different hardware or precision never merge into
one output. `run-<model>.json` records the device, the GPU name and every
library version.
