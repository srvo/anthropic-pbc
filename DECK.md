---
marp: true
title: "Anthropic PBC: the report in charts"
paginate: true
size: 16:9
style: |
  section { background: #fcfcfb; color: #0b0b0b; font-family: "DejaVu Sans", system-ui, sans-serif; font-size: 26px; padding: 48px 64px; }
  h1 { font-size: 40px; margin-bottom: 8px; }
  h2 { font-size: 30px; margin: 0 0 12px; }
  p, li { line-height: 1.35; }
  section.chart { padding: 32px 48px; }
  section.chart img { display: block; margin: 0 auto; max-height: 520px; }
  .src { font-size: 15px; color: #52514e; position: absolute; bottom: 28px; left: 48px; right: 120px; }
  .tag { font-size: 16px; color: #52514e; }
---

<!-- Built from committed files only. Charts: docs/figures/build.py (the paper's own),
     the corpus report scripts under scripts/, and scripts/deck_charts.py.
     Render: npx @marp-team/marp-cli@3.4.0 DECK.md --pptx  (or --pdf, --html) -->

# Anthropic PBC
## A counterpoint to the 2026 Public Benefit Report, in charts

Working paper v0: "released for disagreement, not as a verdict."
Paper: `docs/anthropic-contrapunctus.md`. Every chart here rebuilds from committed files.

<span class="tag">Model output in these charts comes from witnesses: two NLI models whose labels are proposals, not hand-verified findings.</span>

---

## The argument in one line

**Anthropic's charter is legally real and legally toothless.**

- §365(b) gives directors no duty to any person on account of a public-benefit interest.
- §367 limits enforcement to holders of ≥2% (or $2M, lesser, once listed).
- The public the charter names cannot enforce it.

The Report argues from *inputs + intentions* to a discharged public duty. The paper finds that inference unearned (§3).

---

<!-- _class: chart -->

![w:1000](docs/figures/fig1-verification.svg)

<div class="src">51 of 60 load-bearing quotes verified byte-exact against the PBC Report and S-1 (loop audit, 2026-11-03). "129,000" is not in the Report.</div>

---

<!-- _class: chart -->

![w:1000](docs/figures/fig3-scorecard.svg)

<div class="src">Appendix A: 0 of 10 governance dimensions held as filed; 4 partial or revocable, 6 absent.</div>

---

<!-- _class: chart -->

![w:1000](docs/figures/fig4-leverage.svg)

<div class="src">§1a, Meadows leverage points: Anthropic acts at 12 and 6, declines at 5, 4 and 3, speaks at 2 and 3.</div>

---

<!-- _class: chart -->

![w:1000](docs/figures/fig2-risk-governance-index.svg)

<div class="src">Risk–Governance Index v1 on Anthropic's own disclosed risks: 0 of 8 controlled.</div>

---

# What the public record shows

The paper's evidence is Anthropic's own filings. The rest of this deck looks outward at what public data says about AI risk and Anthropic:

- **S&P 500 earnings calls:** what companies and analysts say about AI.
- **Hacker News:** what practitioners say about Anthropic and AI security.
- **Wikipedia:** the map of AI-risk ideas.
- **The CVE record:** what the vulnerability database credits to AI.

---

<!-- _class: chart -->

![w:900](proposals/earnings-calls/codebook-v0.1/report/ai-risk-by-year.svg)

<div class="src">AI as a risk on S&P 500 calls: 12.3% of 2026 calls (to 11-04) by both models, up from under 1% before 2023.</div>

---

<!-- _class: chart -->

![h:520](proposals/earnings-calls/codebook-v0.1/report/risk-ranking-ttm.svg)

<div class="src">Companies name cybersecurity, safety and overspending. Energy, bias and jobs barely register. Codebook v0.1.</div>

---

<!-- _class: chart -->

![h:520](proposals/earnings-calls/codebook-questions-v0.1/report/intent-ttm.svg)

<div class="src">Analysts ask how AI sells (21.2% of AI questions) far more than how it is governed (0.8%). This bears on App. E: almost nobody on a call asks about control.</div>

---

<!-- _class: chart -->

![w:1050](proposals/hacker-news/report/risk-ranking-ttm.svg)

<div class="src">Hacker News discussion of Anthropic is about safety and ethics (40%) far more than executives' calls are (12%). Codebook v0.1; HN precision on safety/ethics is weaker (method doc).</div>

---

<!-- _class: chart -->

![h:540](proposals/cross-source/codebook-v0.2-draft/report/dialogue-space.svg)

<div class="src">The dialogue space, under the DRAFT v0.2 codebook: executives and analysts talk about cyber and capex; Wikipedia covers the field. Draft wording; shares differ from v0.1.</div>

---

<!-- _class: chart -->

![w:950](deck/cve-ai-credit.svg)

<div class="src">The public CVE record credits Claude on 370 CVEs (2020-01 to 2026-10) and any AI system on 924. That cannot confirm or refute "33,000+": not every flaw becomes a CVE, and credits need not name the tool.</div>

---

## What this deck does not show

- **No effect of Anthropic on any outcome.** Attention and counts only.
- **No gold set yet.** Every model-labelled chart is a two-witness proposal; precision is unmeasured.
- **Survivorship.** The earnings-call universe is today's S&P 500.
- **No news-attention chart.** GDELT's daily series drops days (18 of 31 in October 2026), so it was left out.
- **The paper is unsealed.** The sealed version will carry its graph-root hash.

Sources, licences and rebuild commands: `DATASETS.md` and each corpus's method doc.
