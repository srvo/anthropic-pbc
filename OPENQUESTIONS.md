# Open questions

Decisions and questions waiting on someone. Each has an owner, the context
needed to answer it, and what it blocks. When one is answered, move it to
**Answered** with the answer, who gave it, and the commit that acted on it.
Never delete an entry.

New questions come from the work itself and from `PASTEBIN.md`.

## Open

### Q1 · Who signs the datasets?
- **Owner:** Sloane
- **Context:** Every corpus is hash-pinned and rebuilds byte-identical, but
  nothing is signed. The attestation protocol (`docs/contrapunctus-attest.md`:
  SSH Ed25519, `ssh-keygen -Y sign`, `verify.sh`) covers only the paper.
  `docs/praxis-standard.md` PS-3.7 says release signing is open because no key
  exists. Commits are unsigned.
- **Proposal:** each corpus gets a signing record (commit plus the hash of every
  output file), signed in a separate dataset namespace and checked by
  `verify.sh`. `DATASETS.md` shows the signers.
- **Options:** Sloane's key; an Ethical Capital dataset key; either one plus a
  build key. A build key proves only that this pipeline made these bytes; it
  does not mean anyone vouches for them. Separately: whether to sign commits.
- **Blocks:** the attestation part of the white paper's method for the corpora.

### Q2 · Approve the codebook v0.2 wording
- **Owner:** Sloane
- **Context:** `corpus/codebooks/codebook-v0.2-draft.tsv` keeps the 16 v0.1
  hypotheses and adds 14, each citing a Wikipedia heading and revision. The
  `democracy` item comes from the health-of-democracy question, not a heading.
  All four sources are scored against the draft so the wording can be judged
  on real output.
- **Blocks:** citing any v0.2 result; the cross-source map of who discusses
  which risks.

### Q3 · Who codes the gold sets?
- **Owner:** Sloane
- **Context:** `gold/earnings-calls/` holds two blind samples: 240 windows and
  200 analyst questions. `uv run scripts/ec_gold.py code --coder NAME` codes
  them; a second coder works on a copy (`--sample PATH`). Spec §9 bars LLM
  labels.
- **Blocks:** every rate leaving `proposals/` (spec §7, go criterion a). The
  controls category gets only a handful of positives into the sample; if it
  becomes the headline, it needs a targeted extra sample.

### Q4 · Seal version and date for the paper
- **Owner:** Sloane
- **Context:** `uv run scripts/seal.py seal --version vX --date YYYY-MM-DD`
  needs both values.
- **Blocks:** the next sealed version.

### Q5 · Wikipedia corpus scope
- **Owner:** Sloane
- **Context:** Category members came in unfiltered: fiction (Skynet, Universal
  Paperclips), some biographies, books and laws. The `via` column records how
  each article entered. The seed "AI-assisted targeting" does not exist;
  "AI-assisted targeting in the Gaza Strip" does and was not substituted.
- **Decide:** filter by article type? Add the Gaza article as a seed?

### Q6 · Hacker News after August 2026
- **Owner:** open
- **Context:** The pinned archive ends in August 2026. September to November
  would come from the HN API by item-id range, pinned as saved bytes.
- **Blocks:** HN numbers for the same 12 months as the earnings calls.

### Q7 · Excluded and local-only Epoch data
- **Owner:** Sloane
- **Context:** ChatGPT usage is excluded because YouGov's notice bars AI
  ingestion; access would have to come through YouGov. 67 third-party
  benchmark tables stay local because they keep their own licences.
- **Decide:** pursue YouGov access? Clear the benchmark licences?

### Q8 · Auto-regenerate DATASETS.md on commit
- **Owner:** Sloane
- **Context:** `uv run scripts/datasets_md.py check` detects a stale deck. A
  pre-commit hook would run it, but `.githooks/` holds another session's
  uncommitted work.

### Q9 · What would test "Anthropic is good for the health of democracy"?
- **Owner:** open
- **Context:** The proxies being built (GDELT phrase timelines, Rooney
  Institute toplines, the Trust Project and BCG Trust Index notes) measure
  attention and conditions, not Anthropic's effect. A test needs a mechanism
  and a comparison: what Anthropic does that others do not, and an outcome
  that could move.

### Q10 · Point-in-time S&P 500 membership
- **Owner:** open
- **Context:** The earnings-call universe is today's index applied backwards,
  so firms that left are missing (survivorship bias).

### Q11 · Voidly as a source
- **Owner:** Sloane
- **Context:** CC BY 4.0 censorship-incident records with ML-assigned classes
  and confidence scores, from one small vendor. It fits the democracy thread as
  one witness among several, not as ground truth (`docs/corpus-roadmap.md`).

## Answered

| # | Question | Answer | By | Commit |
|---|---|---|---|---|
