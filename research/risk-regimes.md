# How society regulates lethal and systemic risk

Leads, not pinned evidence. `risk-regimes.tsv` has 36 rows with regulator, instrument, incident window, backstop and URL (retrieved 2026-11-05). US figures are eCFR inflation-adjusted maxima (2026-10-01); cells marked "not fetched" were not read from a source. Six rows are omitted below.

L = licence, P = pre-market approval, S = an outside body can stop the work.

| Category | L | P | S | Penalty | Maximum |
|---|---|---|---|---|---|
| Nuclear power | Y | Y | Y | per day | $372,240/day |
| Select agents | Y | Y | Y | fixed | $870,549 |
| Chemicals (TSCA) | N | Y | Y | per day | $49,772/day |
| Pharma | Y | Y | Y | mixed | EU 5% turnover |
| Medical devices | Y | Y | Y | fixed | $2.36M aggregate |
| Aviation | Y | Y | Y | fixed | $75,000 |
| Space launch | Y | Y | Y | per day | $299,772/day |
| Automotive | N | N | recall | capped | $139.4M series |
| Maritime/oil | Y | Y | Y | per barrel | $7,093/barrel |
| Pipelines | N | partial | Y | capped | $2.73M series |
| Offshore oil | Y | Y | Y | per day | $55,764/day |
| Grid | Y | partial | Y | per day | $1.58M/day |
| Firearms | Y | partial | Y | criminal | n/a |
| Export controls | Y | Y | Y | 2× transaction | $1.27M or 2× |
| Banks | Y | Y | Y | per day | $2.51M/day, ≤1% of assets |
| Food | N | N | recall | criminal | n/a |
| Tobacco | Y | Y | Y | fixed | $1.46M aggregate |
| Gambling (UK) | Y | Y | Y | uncapped | none |
| Telecoms/online (UK) | Y | partial | Y | turnover | 10% revenue |
| **EU AI Act** | N | high-risk | Y | turnover | 7% |
| **SB 53** | N | N | **N** | fixed | **$1M** |
| **NY RAISE** | N | N | N | fixed | $1M / $3M |
| **RSPs** | N | N | N | none | none |

## What it shows for AI

Almost every lethal-risk regime above gives an outside body the power to stop the work, and most require a licence or pre-market approval. SB 53, RAISE and the RSPs have neither. The only AI regime with a stop power is the EU AI Act, whose AI Office can require a general-purpose model to be withdrawn or recalled (Art. 93).

Penalties scale in three ways: by duration (NRC, PHMSA, FERC per-day accrual), by harm (Clean Water Act per barrel, ITAR twice the transaction, 18 U.S.C. 3571(d) twice the gain or loss), and by firm size (GDPR 4%, EU AI Act 7%, DMA 10–20%, Online Safety Act 10%, EU pharma 5%). SB 53 uses none of them.

Caps bend under pressure: OPA 90 limits fall away for gross negligence, and New York cut RAISE penalties from $10M/$30M to $1M/$3M to match California.

## The case for scaled penalties

A fixed ceiling shrinks against the gain as the firm grows. The EU uses "whichever is higher" so the fixed floor protects small firms and the percentage reaches large ones. The UK health and safety guideline says a very large organisation's fine "cannot be reached by merely applying a mathematical formula" to the large-firm range.

## The case for fixed caps

- **Predictability and insurance.** Price-Anderson caps liability so that reactors can be insured.
- **Due process.** The Excessive Fines Clause bars grossly disproportional fines (*Bajakajian*, 524 U.S. 321), and *State Farm v. Campbell* (538 U.S. 408) limits punitive ratios.
- **Pre-emption.** A state setting revenue-scaled fines invites federal pre-emption.
- **Scale is not harm.** Turnover measures size, not danger; per-day or per-harm scaling targets the conduct.
- **Stacking.** SB 53's fine is per violation and can multiply.

## Pasted claims

| Claim | Verdict | Source |
|---|---|---|
| (a) A "National AI Charter Act" models AI testing on nuclear protocols | **Confirmed, with nuance.** Rep. Jayapal's 1 Oct 2026 framework (not bill text) requires "containment protocols on par with those used for nuclear energy". The charter itself is modelled on national banks. | jayapal.house.gov framework PDF |
| (b) RSPs legally or contractually oblige upgrades at thresholds | **Refuted.** RSP v3.4 calls itself "our voluntary framework", and its Frontier Safety Roadmap goals "are not hard commitments". The only legal hook is SB 53, which fines failure to follow one's own framework, up to $1M. | `sources/rsp-v3.4.pdf`; SB 53 s.22757.15 |
| (c) EU AI Act tiers mirror biosafety levels | **Refuted.** The Act tiers by intended use (prohibited, high-risk, transparency), not by containment, and does not mention BSLs. A loose analogy at most. | Regulation 2024/1689 |
| (d) Cloud KYC rules exist for AI compute | **Not in force (US).** Commerce proposed IaaS KYC on 29 Jan 2024 (89 FR 5698). A Federal Register search to 5 Nov 2026 finds no final rule. Whether it was withdrawn is unverified. | federalregister.gov 2024-01580 |
