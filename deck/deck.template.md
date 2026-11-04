---
marp: true
title: "Anthropic PBC: the public record in charts"
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

{{generated_notice}}

# Anthropic PBC
## The public record in charts

Built from commit `{{source_commit}}` with risk codebook **{{codebook}}**{{codebook_status}}.
Every number on these slides is read from a committed table at build time.

<span class="tag">Model labels come from two NLI witnesses; a label counts only when both score it ≥ {{threshold}}. Labels are proposals, not hand-verified findings: there is no gold set yet.</span>

---

## The argument (edition {{paper_edition}} of the paper)

**{{q_toothless}}**

- {{q_365b}}
- The public the charter names cannot enforce it.

Edition {{paper_edition}} of the paper (`docs/anthropic-contrapunctus.md` at `{{paper_v0}}`) rests on Anthropic's own filings. This deck looks outward at public data.

---

<!-- _class: chart -->

![w:900](deck/ai-risk-by-year.svg)

<div class="src">AI framed as a risk: {{ec_pct_witness_last}}% of {{ec_year_last}} S&P 500 calls (to {{as_of}}), against at most {{ec_pre2023_max}}% in any year before {{ec_cutoff_year}}. The call rate rises with AI talk itself: AI passages per call went from {{ec_wpc_base}} in {{ec_win_base_year}} to {{ec_wpc_last}} in {{ec_year_last}}, while the share of AI passages framed as a risk went from {{ec_win_base}}% to {{ec_win_last}}%.</div>

---

<!-- _class: chart -->

![h:520](deck/risk-ranking-ttm.svg)

<div class="src">Company executives and other company speakers at {{ec_ttm_risk_firms}} firms raised AI as a risk in the {{ttm_months}} months to {{as_of}}; analysts' questions are excluded (speaker role is a name heuristic). Most named: {{ec_top3}}.</div>

---

<!-- _class: chart -->

![h:520](deck/intent-ttm.svg)

<div class="src">Analysts ask how AI sells or what it costs ({{q_commercial_pct}}% of AI questions) far more than how its risks are governed ({{q_oversight_pct}}%). Each share counts a question once, however many topics in its group it carries. Question-intent codebook {{question_codebook}}.</div>

---

<!-- _class: chart -->

![h:540](deck/dialogue-space.svg)

<div class="src">Safety and ethics: {{ds_exec_safety}}% of executives' AI-risk passages, {{ds_hn_safety}}% on Hacker News about Anthropic, {{ds_wp_safety}}% on Wikipedia. HN's AI-security set is selected on security terms, so its cybersecurity share ({{ds_sec_cyber}}%) is high by construction.</div>

---

<!-- _class: chart -->

![w:950](deck/cve-ai-credit.svg)

<div class="src">CVE credits name Claude on {{cve_claude_total}} CVEs and any AI system on {{cve_ai_total}} ({{cve_first}} to {{cve_last}}). That cannot confirm or refute the claim of "{{q_33k}}", which edition {{paper_edition}} of the paper itself marks {{q_33k_status}}: not every flaw becomes a CVE, and credits need not name the tool.</div>

---

## What this deck does not show

- **No effect of Anthropic on any outcome.** Attention and counts only.
- **No gold set yet.** Witness precision is unmeasured.
- **Survivorship.** The earnings-call universe is today's S&P 500.
- **No news-attention chart.** GDELT's daily series omits days, so it is not used.
- **Draft codebook.** Wording of {{codebook}} awaits human review.

Sources, licences and rebuild commands: `DATASETS.md`. Build stamp: `deck/STAMP.json`.
