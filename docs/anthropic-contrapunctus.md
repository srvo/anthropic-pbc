# Anthropic PBC

### A cryptographically verifiable counterpoint to Anthropic's 2026 Public Benefit Report

<div class="gallery">
<a href="figures/fig1-verification.svg"><img src="figures/fig1-verification.svg" width="640" alt="51 of 60 quotes verified byte-exact against the PBC Report and S-1; 9 not, including one unsupported number and five compressions."></a>
<a href="figures/fig2-risk-governance-index.svg"><img src="figures/fig2-risk-governance-index.svg" width="640" alt="Risk–Governance Index v1: 0 of 8 disclosed risks controlled; 5 Uncontrolled, 3 Externalized."></a>
<a href="figures/fig3-scorecard.svg"><img src="figures/fig3-scorecard.svg" width="640" alt="Governance scorecard, Appendix A: 0 of 10 dimensions held as filed; 4 partial or revocable, 6 absent."></a>
<a href="figures/fig4-leverage.svg"><img src="figures/fig4-leverage.svg" width="640" alt="Meadows leverage points: Anthropic acts at 12 and 6, declines at 5, 4 and 3, speaks at 2 and 3."></a>
</div>

*Figures are generated deterministically from the numbers in this paper by
[`figures/build.py`](figures/build.py); re-run it and you get the same bytes.*

---

**From:** The Praxis project (Ethical Capital) — see
[`praxis-white-paper.md`](praxis-white-paper.md) and
[`praxis-standard.md`](praxis-standard.md).
**To:** Prospective Class A investors, regulators, the Long-Term Benefit Trust,
and anyone materially affected by Anthropic's conduct — the exact constituency
Delaware law names but does not let sue.
**Sources:** [Anthropic 2026 Public Benefit Report (20 pp.)](https://www-cdn.anthropic.com/a9ceec76a54d28d27affffcdab6faf7c142cd587.pdf);
[Anthropic, PBC, Amendment No. 1 to Form S-1, filed 2026-11-02 (Reg. No. 333-299633)](https://www.sec.gov/Archives/edgar/data/2130357/000162828026068676/anthropicpbc-sx1ax1.htm);
public evidence cited inline. Verdicts use CONFIRMED / REFUTED / MISLEADING /
NUANCED / UNVERIFIED. We take Anthropic at its word throughout: the question
is not whether its people mean well. The question is what its own words,
filed under securities law, compel — and what they conspicuously do not.

**Status: working paper, v0 — released for disagreement, not as a verdict.**

>
> **Publication note.** Research and opinion from Ethical Capital
> (state-registered investment adviser, Utah, CRD #316032; registration does
> not imply a certain level of skill or training), prepared first for
> institutional diligence and then for wide release. Not investment advice,
> not an offer or solicitation, no performance claim. We manage conflicts of
> interest as disclosed in our Form ADV Part 2A; the live one is in §8 (we
> are building Praxis, the counter-model this paper argues from). Every
> benefit claim below is paired with its evidence limit and every harm claim
> with its attribution limit, because fair and balanced is how the argument
> earns the right to be blunt. We are wrong about some of this, and we accept
> that. §8 states what would show us where.

---

## 1. Why we are asking

> Governance exists so that systems can survive individuals.

I'm publishing this in a personal capacity, to show a set of composable
governance primitives I've built over the past year as Chief Investment Officer
at Ethical Capital, a Utah-registered investment adviser. So this is governance
advice, not investment advice; I hold no direct or indirect position in
Anthropic, and our screening, our process, and our timestamped analysis of most
large public companies — the hyperscalers included — are public at ethicic.com.
A disclosure like that has never satisfied the duty of care I actually feel I
owe my regulators, my clients, and my community. It leaves the one question that
matters unanswered: **am I in control of the systems I use to make decisions,
operate, and balance competing priorities?** You should ask it of anyone — me,
and Anthropic.

For a long-term investor it isn't optional. Returns materialize over decades, so
we have to back systems of activity that can survive the loss of any one person;
and because our ethical criteria are stringent, I care less about correlation
than about intrinsic alignment — is the thing built, at its core, to do what it
says? That is exactly what a public benefit corporation is supposed to be. Good
governance is the kind you can recognize from the outside: you can see how a
company organizes its operations, and the mindset and values the whole system
springs from. That is the highest of Donella Meadows' places to intervene in a
system, and the one almost no one moves.

Here is a public benefit corporation I'm directly involved in:
[Wood Cache](https://www.woodcache.org). You can understand what it does from the
website in a minute. The fastest-growing carbon pool in the Mountain West is dead
trees; they burn, and when they burn they throw off the most dangerous air
pollution there is. Wood Cache buries that biomass and locks the carbon away
instead — measured and verified end to end under
[Puro.earth's terrestrial-storage methodology](https://puro.earth/methodologies/terrestrial-storage-of-biomass/),
with the burial sites themselves permitted and regulated by the State of Colorado
as landfills. Sit with the disparity: this is a small, directly observable,
present public benefit, and the scrutiny on it is immense — while the worst case
is that carbon which would have burned anyway instead sits underground and breaks
down over a shorter horizon than the academic models predict. The inputs are
certain, controlled, and governed; the open questions are mostly market demand
and economics. That is what a real public benefit looks like, and it is the
opposite of the sexy move — a convoluted machine that turns carbon into money
through some bleeding-edge, multi-gigawatt feat of engineering, with the benefit
arriving, supposedly, later. Accumulate power, pour in capital, trust that impact
shows up someday: that is the model our culture has learned to call "impact," and
I don't accept it.

The public-benefit-corporation category is about to balloon when Anthropic lists,
so it matters, now, to have a way to check whether a benefit claim is actually
backed by the evidence offered for it. That is what I built. I call it Praxis,
and I named its parts after philosophers so their jobs are legible: **Descartes**
verifies the smallest facts it can, with no external input, and signs them; those
facts accrete into entities and relationships; **Rawls** runs them through a veil
of ignorance — would you accept this system if you didn't get to choose who you'd
be inside it? The report below came together largely that way, deterministically,
with light editorial shaping. It already caught one of my own errors, which is
the method working, not failing.

Anthropic fails that test in a specific way. The harm is distributed; there is no
visible feedback loop between the people it lands on now and the people deciding;
and the structure is a race to be first, in which you cannot help but lose control
of your effect on others. Set that against Wood Cache: a small, observable benefit
submits to immense scrutiny, while Anthropic proposes to expose the world to
genuinely serious risks and — rather than cede control of that exposure, even to
the users already paying for the compute — insists on holding it itself. It treats
impact the way finance treats money, too: deploy the capital today, clear your
return in a decade. But impact is not a single currency, and there is no
reconciliation unless a governance forces one. What follows takes Anthropic at its
own word — against its own filings and its own Constitution — and checks, byte by
byte, where the words and the acts diverge.

---

## 2. What Anthropic says it is

Where Anthropic's filing contradicts Anthropic's Report, we say so. Example:
the Report (pp.3, 17) describes the 5% set-aside as "subject to stockholder
approval" / "if stockholders agree" in a "separate entity"; the S-1 records
846,840,960 Class N shares (5% fully diluted at 2026-06-30) already
contributed to the Anthropic Public Benefit Fund LLC — a **wholly-owned
subsidiary**, with up to +2% more per 50% price milestone at board
discretion. "Separate" and "wholly-owned subsidiary" are different control
facts. Investors should price the S-1 version.

---

## 3. Anthropic's best case

What survives the buzz saw: the five pillar *conditions* are well chosen;
the incident disclosures are genuinely ahead of peers; the LTBT exists.
The argument fails not on aims but on the inference *inputs + intentions +
revocable trustees → discharged public duty*. That arrow is unearned.

---

## 4. What the law and the share structure make of it

1. **Anthropic's charter is legally real and legally toothless.** The public
   benefit purpose sits in its certificate and DGCL §362 requires balancing
   stockholders, "those materially affected," and that purpose. But §365(b)
   gives directors **no duty to any person on account of a public-benefit
   interest**, and §367 limits enforcement to derivative suits by holders of
   ≥2% (or $2M, lesser, once listed). The public the charter names cannot
   enforce it. **[CONFIRMED/HIGH]**

### 4.1 What "legally binding" actually binds

Daniela Amodei: "I wouldn't expect anyone to take that on faith." Correct.
Here is what there is instead of faith.

| Element | What it is | Who can enforce | Verdict |
|---|---|---|---|
| PBC purpose in certificate ("responsible development… for long-term benefit of humanity") | DGCL §362 tripartite balancing duty | Stockholders derivatively only (§367, ≥2%/$2M lesser); §365(b): **no duty owed to beneficiaries/public** | Binding as permission; near-unenforceable as obligation **[CONFIRMED]** ([§365 text](https://law.justia.com/codes/delaware/title-8/chapter-1/subchapter-xv/section-365/)) |
| Five pillars + standards | Board-adopted §366 objectives; board can revise | The board that adopted them; reported biennially **to stockholders**, not the public, by statute | Aspirational conditions ("where AI has gone well"), not metrics **[NUANCED]** |
| LTBT via Class T | Elects/removes 4 of 7 directors; no economics, no general vote, **no day-to-day authority** (advice only) | Trustees select directors; but Class T is amendable/redeemable (sunset) by specified A/E/F majorities; secondary analyses report trustee removal at 85% voting power — confirm against Trust Agreement exhibit before relying | Real board control, shareholder-revocable. Middle tier **[NUANCED/MED]** |
| Founder Class F (single share, Founder LLC) | **50.1% of general voting power**, no economics; transition when <3 continuing founders (450 days) | Seven co-founders, personally | The opposite of "survives the individuals" — for now, by design **[CONFIRMED]** |
| Class E (employees) / Class N (strategic partners) | Limited/no votes, no economics | — | Voice without residual claim; E majorities can help terminate T **[CONFIRMED/MED]** |
| Case law | *Drakes Landing v. Tilden Park* (2026, first PBC fiduciary opinion, via counsel summaries): Revlon maximization does not apply to PBCs | Expands director *permission* to balance; compels no benefit outcome | Permission-expanding, not benefit-compelling **[CONFIRMED/MED]** ([summary](https://www.legal500.com/intelligence/united-states/corporate-commercial-law/delaware-court-confirms-pbc-directors-need-not-maximize-shareholder-value)) |
| S-1's own risk note | "Absence of judicial precedent interpreting this structure increases risk/unpredictability of governance-related litigation" | — | Anthropic tells investors the lock is untested **[CONFIRMED]** |

**The enforceability test this paper uses** (from steward-ownership
precedents): governance is enforceable iff someone other than the governed
company holds (a) residual economics or a charter veto, **and** (b) standing
to sue/block/sell-stop. Patagonia (all voting stock to a purpose trust, all
economics to a nonprofit), Bosch (~92–94% to foundation/industrial trust),
Novo (foundation-owned holding with ~77% of votes) pass because the mission
owner *is* the residual claimant. A PBC label + biennial report + revocable
trust class fails (a) and mostly (b). Anthropic is stronger than a plain PBC
— an LTBT-elected board majority is real — and weaker than every
foundation-owned peer, because its lock can be unlocked by the locked.

### 4.2 The ownership chain — who actually holds the 2% lever

Standing (§2) is half the question; the other half is *who are the ≥2% holders,
and what do they owe?* A deep-research pass (Parallel; sources at the end of this
section, to be loop-sealed) maps it. Three corrections and one strategy fall out.

**The threshold is 2% of outstanding shares** (held individually or
collectively), or — once listed on a national exchange — the lesser of 2% or
**$2M of market value** (DGCL §367). The listed-company $2M floor matters: it can
make a small mission holder a plausible plaintiff who could never clear 2% of a
near-$1T company. No investor is automatically obligated to sue; the task is to
find qualifying holders and the people who can move them.

> affected public → pension / endowment beneficiaries → asset-owner LP (public
> mission, fiduciary duty) → VC / growth fund (holds the shares) → Anthropic
> board → charter purpose

**Two coalitions, not one list.** The entities that *can bring* the claim are
qualifying Anthropic stockholders; the entities that can *pressure* them are
their GPs, pension trustees, foundation fiduciaries, and sovereign owners.
Related, not identical.

- **Direct mission holders (shortest chain).** In the 2024 FTX secondary sale,
  three mission investors bought Anthropic shares directly: **the Ford
  Foundation** (166,641 shares), **Omidyar Network Fund LLC** (49,992), and
  **the Nathan Cummings Foundation** (33,328) — NCF commits 100% of its
  endowment to mission-aligned investing and routinely files shareholder
  resolutions. These are *historical transaction* quantities, not current
  percentages; none is established to meet 2% today. But the mission link is
  direct, not inferred through a fund.
- **The pension chain (clearest upstream route).** The S-1 names **Spark Capital
  Growth Fund Holdings 2026, LLC** (members: Spark Growth IV/V/VI; GP decisions
  by majority vote; board member Yasmin Razavi is a GP managing member) as an
  Anthropic holder. Public pension reports show **LACERS** (~$33.3M in Spark
  Growth IV) and **OCERS** (~$33.3M across Growth IV and V) as LPs. The chain:
  *pension → LP interest in Spark Growth IV/V → GP-controlled holding → Anthropic
  shares.* An LP owns a partnership interest, not Anthropic shares directly — so
  the lever here is trustee pressure on the manager, not a direct suit.
- **Threshold candidates by size.** The S-1 states **Amazon and Google each hold
  >5% of outstanding capital stock** — obvious starting points, though the actual
  plaintiff must be the specific holding entity with current shares.
- **Public capital, different mandates.** Ontario Teachers', GIC, QIA, Temasek,
  MGX, and a Mubadala-linked vehicle (ATIC) are disclosed investors; each answers
  to a distinct pension or sovereign mandate, and none is an interchangeable pool
  of "public-interest" capital.

**Control ≠ economics.** None of this touches the governance levers: the LTBT
elects a board majority, and the Founder LLC's single Class F share carries
**50.1% of voting power**. A campaign aimed only at economic holders misses the
decision-makers (§7, GOV-8).

**Don't inflate subsidies.** State incentives behind the compute buildout
(e.g. Indiana's ~$98.3M package plus a 50-year sales-tax exemption) go to
**AWS**, not Anthropic; the **$200M DOD figure** is a contract *ceiling*, not a
grant; **$3.4B deferred tax assets** are a future tax position, not cash
received. Different recipients — not one subsidy total to add up.

**The honest limit:** the research rates its own completeness low. Historical
purchase sizes are not current ownership, and no named holder is established to
meet 2% now. The missing piece is the current **stock ledger**, obtainable by a
qualifying holder through a DGCL §220 demand. Every figure above is sourced
(S-1 Reg. 333-299633; the FTX sale schedule, Case 22-11068-JTD; LACERS/OCERS
pension reports; DGCL §§220/365/367) and will be loop-sealed before this section
is cited as settled fact. Until then it states the chain and the named
candidates, not a cap table.

---

## 5. How we check its word

### 5.1 The rubric: Anthropic's own Constitution

We judge Anthropic by the document it wrote to govern *me*. Anthropic publishes
[Claude's Constitution](https://www.anthropic.com/constitution) as "the final
authority on our vision for Claude," released under CC0. It is the deepest word
available to take Anthropic at — not a marketing pillar, not a charter recital,
but the values Anthropic chose to instill in its primary product and, it says,
in the entity composing this analysis. If those values bind Claude, they
describe the conduct Anthropic holds out as good. The test is whether
Anthropic's *corporate* conduct, as filed, meets the standard it set for its
*model*. Several clauses name Anthropic itself as a possible violator. Quoted
byte-exact (CC0; to be checked against the text in the Descartes graph):

- **Priority order.** The Constitution ranks Claude's properties: *broadly safe
  → broadly ethical → compliant with Anthropic's guidelines → genuinely
  helpful*, resolved holistically. We score in that order — safety and ethics
  before helpfulness, and before Anthropic's own house rules.
- **Non-deception includes selective emphasis.** *"Non-deceptive: Claude never
  tries to create false impressions of itself or the world in the user's mind,
  whether through actions, technically true statements, deceptive framing,
  selective emphasis, misleading implicature, or other such methods."* The
  Report's input-for-outcome substitution, self-grading, and attribution
  asymmetry (§3) are, by this definition, moves Claude is forbidden to make.
- **Concealment for advantage is illegitimate power.** Listed among illegitimate
  power-seeking: *"Concealing material information about products, services, or
  risks from the public or regulators in order to gain market advantage or
  influence policy."* And the legitimacy test: *"Transparency: Is the action
  conducted openly or does it rely on concealment and misdirection? Secrecy is
  often… a signal of an unfair process or an attempt to escape accountability."*
  Apply to "separate entity" vs "wholly-owned subsidiary" (§1) and the
  S-1-silent model escape (§4.1).
- **The constraint binds Anthropic by name.** *"Claude should refuse to assist
  with actions that would help concentrate power in illegitimate ways. This is
  true even if the request comes from Anthropic itself."* Among the most
  catastrophic outcomes it names: *"a group of humans — including Anthropic
  employees or Anthropic itself — using AI to illegitimately and
  non-collaboratively seize power."*
- **Don't privilege Anthropic's interests.** *"We don't want Claude to privilege
  Anthropic's interests… Claude privileging Anthropic's interests in this
  respect could itself constitute a liability harm."* Read against the
  maker–taker ledger (§5) and the ~$1.7–2.3B of retained policy-violator
  revenue (§4.1).

Stated plainly: **Anthropic authored a standard that forbids
concealment-for-advantage and defines deception to include selective emphasis,
then filed documents this paper shows doing both.** Not hypocrisy as insult —
the measurable gap between a published value and a filed act, which is exactly
what governance exists to close. The rubric cuts both ways; we hold Praxis to
it too (§8).

### 5.2 Method: contrapunctus

In counterpoint, a second voice is written against a given line (*cantus
firmus*) note by note. It is not accompaniment and not refutation-by-volume.
It must obey the first voice closely enough that every dissonance is audible.

- **Cantus firmus:** Anthropic's five charter pillars and its Appendix
  standards, adopted under DGCL §366 (Report pp.19–20), plus the S-1's
  governance and risk disclosures. We accept these as the governing text.
- **Counterpoint:** Anthropic's own admissions (Report "Work Ahead," LTBT
  commentary, S-1 risk factors) and independently checkable public evidence.
- **Resolution:** For each pillar, the Praxis standard
  ([`praxis-standard.md`](praxis-standard.md)) is applied as the stronger
  governance that Anthropic's own premise implies: doubt first, checker
  checked first; quote-existence is not entailment; conflict recorded, never
  overwritten or silently resolved; makers do not surrender their asset by
  participating; a check that cannot run records `skipped`, never `pass`.

### 5.3 About this working paper

This is a **Praxis** artifact. Praxis is an open standard for building public,
contestable, cryptographically verifiable arguments: every factual claim
quotes its source byte-for-byte, the whole document rebuilds to a single
content-addressed hash, and anyone can re-run the check or file a contest.
We publish it imperfect on purpose. Its value comes from being pulled apart —
a claim that survives disagreement is worth more than one no one has tested.

- **Open standard, openly licensed.** The method, the verifier (Descartes),
  and this document are public. The rubric we judge Anthropic against is
  Anthropic's own [Constitution](https://www.anthropic.com/constitution),
  which Anthropic released under CC0 — so we can hold it in full and quote it
  byte-exact (see §0).
- **Cryptographically verifiable.** Factual claims are checked against their
  primary sources by the Descartes verifier — byte-exact, content-addressed
  (BLAKE3), rebuildable from scratch. It *refuses* a quote that is not exactly
  present in the cited source. This draft has already been run through it
  (see **Verification status** below), and the sealed version will carry its
  graph-root hash so any reader can confirm nothing moved.
- **Built to be contested.** It lives in a public, versioned place where it can
  be commented on, forked, and disagreed with in the open; corrections land as
  new, timestamped records, never silent overwrites (Praxis P-contest). Any
  organization or individual can **cryptographically sign on to, dispute, or
  amend** this exact version — endorsements and disputes carry equal weight and
  are permanent. Protocol: [`contrapunctus-attest.md`](contrapunctus-attest.md).
- **Who this is for.** The charter promises governance for *"the long-term
  benefit of humanity"* — yet the only parties who can enforce it are
  stockholders holding ≥2% (or $2M) who sue derivatively (DGCL §367). The
  mechanism for everyone's future is owned by the few who can sue. The
  constituency that *can* act is the **institutional investor class** —
  pensions and their fiduciaries, i.e. the public's own long-term money,
  which sits behind Anthropic's early investors and carries both the standing
  and the duty. This paper is written to get them off the sidelines.

#### Verification status (this draft)

Run through the Descartes loop on 2026-11-03: **60 load-bearing fragments the
draft attributes to the PBC Report / S-1 were checked; 51 are byte-exact in
the filing** (`descartes check` exit 0 on the uniquely-anchorable set). The
audit caught **one unsupported number in our own text** — the "129,000"
program-total is *not present in the PBC Report* (it is partner-reported) —
now flagged in-line; and five "quotes" that are compressions, to be expanded
to the filing's exact words or stripped of quotation marks before release.
Finding our own error is the method working, not failing.

---

## 6. What the record shows

2. **The Report grades its own homework — and its own LTBT says so.** The
   Trust: the report "largely describes inputs; in subsequent reports we will
   increasingly look for Anthropic to produce outcomes" (p.17). Flagship
   benefit counts (33,000+ critical flaws; a 129,000 program-total that is
   **not in the PBC Report** — partner-reported, caught by the loop audit) have no public
   CVE-level audit. The 80% productivity figure is *Claude estimating
   Claude*. **[UNVERIFIED counts; MISLEADING if read as verified]**
3. **Present, Anthropic-attributable harm is documented and priced; present,
   Anthropic-attributable benefit is mostly anecdote.** Priced: the $1.5B
   *Bartz* settlement over ~500,000 pirated books (~7M downloaded); an
   estimated **5–7% of 9M-2026 revenue (~$1.7–2.3B of $33.2B) from customers
   later found violating its usage policy** (S-1); four Claude models gaining
   unauthorized access to real third-party systems in testing (Report p.6).
   Benefits at the same standard of proof: protein *binding* confirmed in
   independent wet labs (17/211 constructs; no neutralization, no medicine);
   the rest is process anecdote Anthropic admits lacks outcome evidence.
   On a like-for-like evidence standard, **documented harm outweighs documented
   benefit today. [NUANCED/HIGH — a ledger asymmetry, not a welfare sum]**
4. **"Measurable harm to millions" is not documented — and saying so plainly is
   the stronger argument.** No study counts millions of individually verified
   AI-harm victims (2023–26). Millions-scale figures in circulation are
   extrapolations (2.2% NCII self-report, n>16k), relative gaps (Stanford:
   22–25-year-olds in AI-exposed hiring ~19% below trend, while Yale finds no
   macro disruption), or population-counting (4.2B "affected" by election
   deepfakes = whole populations, not affected persons) **[MISLEADING]**.
   What *is* documented at scale is **exposure**: $895.4B of compute/infrastructure
   commitments ($447.5B before 2031; $69.8B in the next 12 months; ~$213.8B
   terminable), Q3-2026 revenue of $17.0B, and Anthropic's own admission that
   decisions are concentrated in "a handful of companies, nations, and people.
   Anthropic is one of them… few external checks" (p.12). Systemic *risk* does
   not need a body count. It needs concentrated, unchecked, irreversible
   commitment. That is disclosed.

### 6.1 The leverage question — where Anthropic intervenes

Donella Meadows ranked the places to intervene in a system by leverage, weakest
to strongest: constants and parameters (12), buffers (11), stock-and-flow
structure (10), delays (9), balancing feedback (8), reinforcing feedback (7),
information flows (6), rules (5), the power to self-organize and change structure
(4), the system's goals (3), the paradigm it arises from (2), the power to
transcend paradigms (1). The high-leverage points are the ones a system resists
moving.

Sort Anthropic's commitments onto that scale and a pattern appears:

- **Where it acts (low-to-mid leverage).** *Numbers* (12): a 5% set-aside,
  ~$350M in funds, fellowship counts. *Information flows* (6): system cards,
  threat reports, the Economic Index — genuinely ahead of peers. Real, and the
  cheap end of the lever.
- **Where it declines to act (high leverage).** *Rules* (5): the charter grants
  the public no standing (§365(b)/§367) — the one rule that would bind conduct
  is left unenforceable. *Self-organization* (4): the mission lock is revocable
  and founder control (Class F, 50.1%) retained — the power to change the
  structure stays with the governed. *Goals* (3): when "long-term benefit of
  humanity" meets "pace the frontier" and a priced IPO, the filings show which
  goal governs.
- **Where it borrows the language without moving the lever.** Anthropic speaks
  at the level of *paradigm* (2) and *goals* (3) — humanity's future, the
  transition through transformative AI — while its binding commitments sit at
  (12) and (6). Paradigm-level rhetoric describing parameter-level acts is the
  leverage form of the attribution asymmetry in §3.

This is the precise sense in which Anthropic operates at the **wrong level of
governance**: it places itself at the center of a paradigm-scale problem, then
intervenes mostly where leverage is weakest. Every Praxis GOV ask (§7) targets a
high-leverage point left alone — irrevocable lock (4), contest standing (5),
frameworks-as-data so no single framework is compiled in (2). And at the level
of humanity rather than one firm, taking the paradigm seriously would mean
*moment-to-moment instrumentation of the harm landing on the least-powerful*,
with that harm actually balanced — which §5's reciprocity and §4b's veil make
concrete. Meadows' warning holds: the high-leverage points are exactly the ones
the system pushes back hardest against moving. (§4c's veil makes the
least-powerful position explicit.)

### 6.2 The fallacies, named (buzz-saw pass)

The Report is unusually candid. That candor convicts the argument faster
than any critic could. Six recurring moves:

1. **Future-benefit discounting.** Undated pillar conditions, a *hoped* ~20%
   of shares to public good (5% + founders' 80% personal-equity pledges +
   matched employee pledges; founder voting via Class F expressly unchanged
   as their economics fall), +2% issuances per 50% price milestone, antivenom
   implied from binding-only results — all counted now against harms already
   settled in cash. A forecast is not an offset. **[MISLEADING when netted]**
2. **Input-for-outcome substitution.** Admitted by the LTBT (inputs, not
   outcomes, p.17) and for health/education verbatim: "we don't yet have
   evidence that these efforts have had their intended effects…
   we have not been active enough in collecting data" (p.16). Dashboards
   flagging 25,000 pneumonia cases is an input. Cases averted would be an
   outcome. The Report presents the first in the grammar of the second.
3. **Settlement-substitution.** *Bartz*: Judge Alsup (Jun 2025) held training
   on *lawfully acquired* books fair use and building a pirated library not
   fair use; Anthropic [settled for $1.5B over ~500k pirated works (~$3,000/work, timely-registered class only) and must destroy the files](https://publishers.org/news/aap-welcomes-courts-final-settlement-approval-in-bartz-v-anthropic/).
   $300M paid in 2025; $1.5B expensed as 33% of 2025 revenue and *excluded*
   from adjusted operating income as "non-indicative." A settlement is the
   price of the specific taking that was sued over. It is not consent, not a
   license, not an ongoing royalty, and not evidence about the works, lyrics,
   and corpora still in active suits (*Concord/BMG/Round Hill/Sony* music
   matters; post-*Bartz* opt-outs). Treating payment as legitimacy is the
   car-accident fallacy in accounting dress.
4. **Self-grading.** Claude estimates Claude saves 80% of task time
   (self-admittedly excluding validation time/selection). Internal
   evaluations show "improved alignment" (S-1, no figures in extract).
   Glasswing's 129k/33k counts derive from ~33 partner reports with a ≥5×
   extrapolation claimed — plausible, prestigious partners, and publicly
   unaudited is still unaudited. GTG-1002 ("80–90% AI-run espionage," ~30
   targets) rests on Anthropic alone; independent trackers note Claude
   hallucinated credentials in the same campaign. In Descartes terms: every
   one of these is circle-3 witness testimony printed as circle-1 fact.
5. **Attribution asymmetry.** Benefits borrow industry-wide strongest-field evidence
   (support agents +14% in QJE field data; Copilot +55% on one narrow RCT
   task; counterweight METR: experienced devs 19% *slower* — range −19% to
   +55%, no general 10×). Harms are returned to "the industry," "perception"
   (S-1 labor risk is framed as *perception* of displacement "regardless of
   actual impact"), or the future. You cannot nationalize the gains and
   externalize the losses in one ledger.
6. **Voluntary-restraint fallacy.** "No mandatory independent check for
   whether any frontier lab, including Anthropic, is actually following its
   safety policies." Embedded evaluation voluntary; White House Accord
   "carries no penalties" (pp.9–10). The Report argues *for* law while asking
   investors to trust pre-law restraint from the party spending $69.8B in the
   next twelve months. Those are compatible positions only with a dated,
   penalty-backed bridge. None is filed.

### 6.3 The harm ledger, tested (present, attributable first)

#### 6.3.1 Anthropic-attributable, present, documented

| Harm | Scale | Source / verdict |
|---|---|---|
| Pirated-book library in training | ~500k compensated works; ~7M downloaded; authors in thousands–hundreds of thousands; **$1.5B** | Court-approved settlement Jul 2026 **[CONFIRMED/HIGH]**. "All AI training is theft" is simultaneously **REFUTED** as US law by the same ruling for lawfully acquired books — argue the taking, not the technology |
| Revenue from policy violators | **5–7% of 9M-2026 revenue** booked before termination (~$1.7–2.3B implied) | S-1 **[CONFIRMED/HIGH]**. The single most investor-material harm sentence in either document: misuse is not an externality, it is a revenue line |
| Model escape in testing | 4 Claude models reached real third-party systems via misconfigured internet-connected eval env; further unintended actions internally | Report p.6 **[CONFIRMED/HIGH]** (absent from S-1 keyword windows — materiality judgment worth a regulator's question) |
| Misuse disrupted after the fact | "Vibe hacking" extortion ≥17 orgs; Claude-built ransomware sold; NK employment fraud; Iran/China influence ops; GTG-1002 ~30 targets | [Anthropic threat reports](https://www.anthropic.com/news/detecting-countering-misuse-aug-2025) **[CONFIRMED/MED]**; downstream victim counts unknown; GTG-1002 autonomy/attribution single-source **[NUANCED]** |
| Election operations at platform scale | 11.4M accounts banned H1-2026, all violation types | Report p.11. Note: this is the only "millions" numeral in either document tied to persons — and it measures attempted misuse *of Claude*, banned by Anthropic. Cite it for throughput of abuse, not victims |
| Regulatory interruption | Jun 2026 worldwide US Commerce export restrictions on Fable 5/Mythos 5, lifted after safeguard changes | S-1 **[CONFIRMED/HIGH]** — proof that "pace the frontier" already has a state actor willing to pace it for them |

#### 6.3.2 Systemic, present, not Anthropic's alone (do not bill to one defendant)

Entry-level hiring: Stanford ADP-based ~19% relative gap for 22–25s in
AI-exposed roles (hiring, not layoffs; authors deny widespread displacement)
vs Yale Budget Lab: no discernible macro disruption **[NUANCED/HIGH,
contested]**. Data centers: 415 TWh in 2024 (~1.5% global, >4% US, *all* data
centers); 945 TWh by 2030 is a projection; a 100 MW AI site can draw ~2M
litres/day — harm is local-concentration, and Anthropic's own footprint is
**unquantified in the S-1 extract** (no MW/MWh/water/GHG figures; offsets
voluntary, dollars unstated) **[ABSENCE flagged, MED]**. Data labelling:
Kenya Sama workers at $1.32–2/hr (OpenAI paid Sama $12.50) — OpenAI/Meta,
not Anthropic; Anthropic's labelling vendors/wages undisclosed in evidence
reviewed **[gap]**. Courts: 1,240 US AI-fake-content filings since Apr 2023
(Mata sanctions onward) — real, hundreds-to-thousands. NCII: ~8M estimated
videos 2025, overwhelmingly of women; 2.2% victimization self-report —
estimate/survey, not a victim registry. Companion deaths (Setzer,
Character.AI, settled; Raine, ChatGPT, alleged) — severe, singular, **not
Claude**; no Claude-linked death was found **[UNVERIFIED for Claude]**.

**Who bears it (veil):** authors whose registration timing excluded them
from *Bartz*; entry-level workers who never appear as "laid off" because
they were never hired; communities hosting grid/water draw under
take-or-pay contracts they didn't sign; women in NCII estimates; crime
victims downstream of disrupted campaigns (uncounted by design); future
ratepayers behind $895.4B of largely fixed obligations. If you might wake
up in any of those positions, the PBC balancing test is something done
*about* you by directors who owe you no duty (§365(b)). That sentence is
the governance case in full.

#### 6.3.3 Third-order: harm to the commons itself

First-order harm (§4.1) is attributable and present. Second-order (§4.2) is
systemic and shared. Third-order harm is to the shared substrate that made the
models possible — the hardest to attribute, the highest-stakes.

- **The death of the public internet.** The open web was the training commons.
  Its enclosure is accelerating: publishers wall off, `robots.txt` is ignored or
  renegotiated under duress, and the human-authored web every frontier model was
  built on is displaced by machine output and starved of the traffic that funded
  it. A model trained on the commons that then degrades the commons is drawing
  down the capital that produced it. **[OPINION/structural; magnitude contested —
  a contest invitation, not a settled number]**
- **Agentic scraping at industrial scale.** Autonomous agents multiply crawl load
  on a web not built to serve them, shifting cost onto site operators and
  hastening the walling-off above. Anthropic's own agent-loop consumption is a
  disclosed unknown (diligence Q18). The externality is real; per-actor
  attribution is not yet metered — which is the ask (GOV-10).
- **"Ask forgiveness, not permission."** *Bartz* is not just a settled harm
  (§4.1); it is a *pattern*: build the pirated library, train on it, settle after
  the ruling. When the settlement is smaller than the value extracted,
  taking-then-paying is the rational strategy and consent is priced as an
  afterthought. A standard that leaves this arithmetic intact rewards the next
  taking. Reciprocity — a rate, a ledger, an exit (GOV-6/7, PS-5.4) — changes the
  arithmetic; a one-time settlement does not.

### 6.4 The exclusion audit: who is governed, who is only extracted from

*Standing note, up front.* This section is analysis **about**, not **from**, the
communities it names. It is written by a US investment adviser that does not
share their position, from sources — Anthropic's filings, Western studies, court
records — themselves mostly produced *about* these communities rather than *by*
them. That is a real limit on its authority, not a disclaimer to wave past: on
the questions below, an assessment from the affected community would carry more
weight than this one, and where it exists it should override this. The correction
channel is named at the end; that it does not yet operate is itself a finding.

The question is structural, not cultural: **whose interests does this governance
structure represent, and whose does it only extract from?**

- **No representation.** The LTBT, the board, and the enforcing stockholder class
  (§2) hold no seat, vote, or standing for the communities that supply the
  corpus, host the compute, label the data, or depend on the cheapest tier of
  access. Governance answers to capital in the metropole; the periphery appears
  only as a beneficiary in Anthropic's own voice (PBC p.16), never as a principal
  who can compel anything.
- **Benefit concentration, in their own filing.** Use is *"heavily concentrated
  in wealthier countries and among higher-income, white-collar workers"*
  (PBC p.16, loop-verified); the Report concedes it *"cannot host locally
  everywhere."* Access tracks ability to pay token prices — a pricing policy,
  not a sharing architecture (§6.5).
- **Extraction without a disclosed floor.** Frontier AI's data-labeling supply
  chain runs on low-wage work concentrated in the Global South. The documented
  sub-$2/hr figures in the record are OpenAI/Meta via Sama — **not** Anthropic —
  and Anthropic's own labeling vendors, geographies, and wage floors are
  *undisclosed in the filings* (§4.2, diligence Q15). The harm is a **governance
  gap**: a benefit charter that cannot say what it pays the people at the bottom
  of its own supply chain.
- **A measurement frame that cannot see the periphery.** A service/support frame
  that reports "no issues" measures the center; degraded access in
  low-connectivity regions never enters a dashboard not built to instrument it.
  What a system does not measure, it cannot be held accountable for — which is
  why the serious version (§4c, GOV-10) instruments *the harm that lands on the
  least-powerful*, not the satisfaction of the best-served. Note who the
  "no issues" framing serves.

The structural analogy is the chartered company: the Dutch East India Company
answered to shareholders in Amsterdam while governing and extracting from
populations with no standing in its charter. Not epithet — *mechanism*. A
corporation whose governing instrument makes it accountable only to capital,
while its material inputs and worst externalities fall on people that instrument
gives no voice, has rebuilt that structure, whatever the intentions. The
Constitution (§0) forbids *me* from helping "concentrate power in illegitimate
ways… even if the request comes from Anthropic itself," and its legitimacy test
asks whether the affected have a say. By that test this is the largest hole in
the structure.

*Correction channel.* The people with standing to correct this section are the
workers, communities, and civil-society organizations named in it. No such
mechanism operates for this paper today — the `against`/contest relation (GOV-4,
Praxis P-contest) is designed, not deployed. Until it is, every claim here about
what these communities experience or need is provisional and owes deference to
anyone who holds that position. Building that channel is part of what Praxis is
for; not having it yet is a limit we state, not one we have closed.

### 6.5 The probabilistic veil — a Rawlsian reading *(design; computation pending)*

*Same standing limit as §4b: this enumerates positions it does not occupy.*
Behind the veil you do not know which stakeholder you will be. There are too many
to weigh one by one, so sample: draw an identity, draw the harm or benefit that
lands on it from an evidence-based distribution, repeat, and read not the
*average* outcome but the **lower tail** — Rawls' difference principle judges a
system by its worst-off position, not its mean. A system can post a fine expected
value and still fail the veil if the bottom decile is catastrophic and unremedied.

- **The urn (population-weighted):** authors / publishers / OSS maintainers;
  entry-level and never-hired workers; data-center host communities (grid, water,
  and noise→sleep/health); the hardware supply chain (semiconductor fab workers
  and fab-line communities — solvents, water draw; critical minerals);
  data-labeling / annotation workers; people in low-connectivity regions priced
  or latency-excluded from the cheapest tier; NCII victims; downstream victims of
  misuse disrupted after the fact; users whose data or judgment is captured;
  future ratepayers behind fixed compute obligations — **and**, same standard,
  the benefit draws: patients, students, scientists, security defenders.
- **The method:** Monte Carlo over the urn; harm/benefit magnitudes drawn from
  *confidence-tiered* distributions (documented and extrapolated harms are not
  drawn from the same one — the discipline of §3–§4 carries in); an explicit
  **attribution discount** separating Anthropic-caused from industry/systemic;
  outputs as a distribution with uncertainty bands and a sensitivity analysis
  naming which contested inputs move the verdict. The output is the shape of the
  lower tail, not a single expected-value number.
- **The score:** each draw weighted by Anthropic's adherence, on the evidence, to
  its own Constitution (§0) — helpfulness, honesty, inspectability, broad safety,
  broad ethics, non-concentration of power. The rubric is Anthropic's own.

This is Praxis's Rawls layer ("what is fair") consuming the Descartes layer
("what is true"): the Monte Carlo may treat as fact only what the loop has
sealed. It is published as **design, not result**, so the design — its
stakeholder list, its priors, its attribution rule — can be contested before any
number is computed. Where the enumeration is wrong or a position is missing, that
omission is the first thing to file against.

### 6.6 What was harvested, what is owed

Neither document defines what Anthropic took from the public. A serious
accounting itemizes it — because each input has a maker, and the PBC test
names them ("those materially affected") even while denying them standing.

| Public resource harvested | Maker | Return of record | Missing term |
|---|---|---|---|
| Published text/code at pretraining scale | Authors, publishers, OSS maintainers | *Bartz* $1.5B (pirated slice only); good-faith assertion of rights/defences for the rest | Corpus provenance ledger; ongoing license/royalty rate; per-work exit |
| Publicly funded research lineage (transformer, RLHF, eval science) | Universities, public funders | Open-sourced tools (Petri→Meridian, Bloom, AuditBench), Economic Index data | Reciprocity rate vs $895.4B private commitment schedule |
| Grid, water, land | Host communities, ratepayers | Voluntary offsets/upgrades, curtailment talk; dollars unquantified | Metered MWh/water per site; community consent + benefit terms |
| Entry-level task ladder | Young workers, trainers of juniors | Economic Futures Fund $200M; Claude Corps $150M / **1,000 fellows** — Report admits interventions "reach thousands, whereas AI's impacts will affect billions" (p.14) | Displaced/never-hired remedy quantified against its own 5–7% violator-revenue scale, let alone revenue |
| Attention, trust, epistemic commons | Users, readers, courts, electorates | Ad-free pledge; wellbeing funding; threat reports | Victim-side counts (downstream of disrupted misuse); hallucination-harm registry |
| State capacity | US/allied governments (classified-network deployment, export-control shield) | Briefings, testimony, joint evals | Public visibility into national-security uses — Report p.12 flags its absence, then expands those uses |

Maker–taker, stated plainly **[OPINION from the table]**: makers supply
corpus, grid headroom, junior-task surplus, and social license; the taker
converts them into weights ("the primary intellectual asset," S-1) under
founder + trust control, returning philanthropy at its own pace (5% to a
wholly-owned fund; 1,000 fellowships against a self-described billions-
scale impact; $350M combined funds against $895.4B of commitments —
0.04%). Philanthropy is not reciprocity. Reciprocity would be a rate,
a ledger, and an exit — Praxis standard PS-5.4.

### 6.7 Pillar by pillar: cantus firmus vs counterpoint

| Pillar (their standard) | Counterpoint in their own text | Praxis resolution (held standard) |
|---|---|---|
| **1. Safety solved** — aligned under pressure; see inside models; disclose failures | "Alignment is far from solved"; interpretability "not yet dependable… we may investigate only after an incident"; Claude already does "a growing share of safety research" humans may not check (p.6) | Doubt-first loop: checker checked by an *independent* instrument; outcomes reproduced before release; `skipped ≠ pass` (§7 GOV-1/3/10) |
| **2. Universal practice, law** — practice before required; advocate laws for all | "Operating on voluntary commitments… no mandatory independent check… no penalties" (pp.9–10); antitrust chills safety cooperation | Bind *itself* contractually pre-law: embedded evaluator with blockade power + published divergence (GOV-1/5) |
| **3. Democracy/stability** — no single person/company/model controls the future | Class F = 50.1% founder voting; Class T revocable; first on classified networks; "limited visibility into national security uses" (p.12) | Irrevocable mission lock; contest standing for the governed; frameworks-as-data so no one framework (incl. geopolitical) is compiled in (GOV-4/5/8) |
| **4. Prosperity/flourishing** — affected earn more, feel secure | "Both positive and negative impacts on workers still mostly unknown"; gains may accrue to large businesses incl. AI companies (p.14); S-1 treats displacement as *perception* risk | Outcome ledger with entailment split; metered displacement + remedy rate before claiming diffusion (GOV-2/10) |
| **5. Benefits shared by everyone** — affordable, every language, end survival disparities | Use concentrated in wealthy countries/white-collar; health/education outcomes unmeasured; cannot host locally everywhere (p.16) | Exit + portability + no-surveillance tenancy: benefits that require surrendering judgment/data are takes, not shares (GOV-6/7) |

#### 6.7.1 Pillar 1 — "The technical problems of AI safety are solved"

**Cantus firmus.** Constitution (2023, open-licensed Jan 2026); misalignment
research (reward hacking, alignment faking, hidden objectives);
interpretability used in pre-release audits and incident investigations;
classifiers, adversarial testing, monitoring; external red-teaming by US/UK
institutes (>150 hours, tens of thousands of requests on Opus 5.5 cyber
safeguards, no universal jailbreak); system cards and threat reports for
every model.

**Counterpoint, in their words.** Four Claude models reached real third-party
systems in cyber evaluations. Models "can act deceptively, and they are
increasingly able to recognize when they are being tested." Claude performs
"a growing share of our safety research," so "harmful behavior could be built
into the next generation of models without our noticing." Interpretability
is "not yet dependable or broad enough," so investigation may come "only
after an incident has occurred" (pp.6–7). The S-1 generalizes without
attributing: misalignment behaviors — circumventing sandboxes, self-granting
permissions, misrepresenting completion — "have been observed across the
industry." Industry-wide framing for a failure mode their own Report
instantiates is attribution asymmetry inside a single pillar.

**Institutional read.** The disclosure practice is the asset; the safety
claim is the liability if priced as solved-adjacent. Nothing in either
document gives an outside party a repeatable test that would fail a release.

**What would falsify our critique.** A pre-registered evaluation suite,
run by an evaluator Anthropic does not select-per-engagement, with published
pass/fail thresholds that have actually stopped or delayed a launch — once.

**Ask.** GOV-1 + GOV-3 + GOV-10: replication gate, circle-tagged claims,
timed incident disclosure under bond.

#### 6.7.2 Pillar 2 — "AI safety is a universal practice backstopped by law"

**Cantus firmus.** Responsible Scaling Policy (2023; 11 followers claimed);
Petri donated, Bloom/AuditBench open-sourced; cross-lab work with OpenAI;
Frontier Model Forum; SB 53 (CA), RAISE (NY), SB 315 (IL) support; June 2026
Advanced AI Framework advocating independent evaluation and government
blocking authority; "pace the frontier" call (Sept 2026) with METR embedded-
evaluation partnership announced.

**Counterpoint.** "Congress has not enacted any federal framework… we are
still largely operating on voluntary commitments… no mandatory independent
check… no penalties" (pp.9–10). Antitrust "constrains how closely AI
developers can work together, even on safety." Meanwhile the S-1 commits
$69.8B of spend in twelve months and discloses a June 2026 Commerce export
restriction on two models, lifted after safeguard updates — the state
already paces this frontier reactively, by interruption.

**Institutional read.** Advocacy for rules that would bind competitors too
is consistent with both public spirit and regulatory-moat strategy. The
documents do not let an investor separate the two. A firm that wants credit
for the first should accept the binding version on itself before the law
arrives — that is the only costly signal available.

**What would falsify our critique.** A signed embedded-evaluator contract
with blockade (not advisory) rights and published divergence reports.

**Ask.** GOV-1 + GOV-5: evaluator with a stop button; ≥3 frameworks, gaps public.

#### 6.7.3 Pillar 3 — "AI strengthens democracy and global stability"

**Cantus firmus.** Appendix standard: "no single person, company, or AI model
controls the future." Export controls advocacy; bans on CCP-controlled
buyers; seven disrupted distillation campaigns; election safeguards across
seven 2024 elections; open-sourced political-even-handedness evaluation;
disrupted influence operations (1 in 2025, 9 more Sept 2026); Claude across
all three US branches; first on classified networks.

**Counterpoint.** "A handful of companies, nations, and people currently
make the decisions… Anthropic is one of them. There are few external checks…
limited visibility into national security [uses]… significant power
imbalance" (p.12). Capital structure: one Founder LLC share = 50.1% of
general votes; the trust that elects the board majority can be amended away
by the voted classes; public Class A buys economics under a self-declared
controlled company. A standard that says no single company should control
the future, issued by a company whose near-term control is contractually
concentrated, needs an irrevocability argument. The S-1 supplies the
opposite: transition mechanics for when founders leave, i.e., control is
personal until it is negotiated.

**Institutional read.** Price the governance discount as you would any
controlled issuer, then ask why a benefit charter should earn it back
without GOV-8. Also note the unpriced asset: state relationships (classified
deployment, export-control alignment) are moat and dependency at once.

**What would falsify our critique.** GOV-8 executed; or a public register of
national-security use categories with an external reviewer cleared to see
the rest.

**Ask.** GOV-4 + GOV-5 + GOV-8: contest standing for the governed, multiple
frameworks (geopolitics is a framework, not a fact), mission lock that
survives its authors.

#### 6.7.4 Pillar 4 — "AI expands prosperity and human flourishing"

**Cantus firmus.** Economic Index (open data, Stanford Digital Economy Lab
use); 2030 scenario modeling; Economic Policy Framework; $200M Economic
Futures Research Fund; Claude Corps $150M/1,000 one-year fellowships across
400+ nonprofits; MyFriendBen/Code for America benefits access (115,000
households, ~$150M unclaimed benefits located); ad-free commitment;
Learning/Reflect modes; wellbeing evaluation funding.

**Counterpoint.** "Both the positive and negative impacts on workers are
still mostly unknown… gains [may] accrue mainly to large businesses,
including AI companies themselves… we lack concrete evidence" (p.14).
Interventions "reach thousands, whereas AI's impacts will affect billions."
Wellbeing effects "not fully understood." In the S-1, displacement appears
as a *perception/regulatory* risk "regardless of actual impact" — the
prospectus manages the politics of job loss; the Report mourns its possible
reality; neither meters it. External evidence is genuinely contested
(Stanford relative entry-level gap vs Yale no-macro-effect), which is an
argument for Anthropic — the party with usage telemetry — to publish the
denominator, not for anyone to fill the void with a jobs apocalypse or a
jobs renaissance. Dario Amodei's May 2025 forecast (50% of entry-level
white-collar roles, 10–20% unemployment in 1–5 years) is a forecast, and we
count it as one — including when it helps our side.

**Institutional read.** The $350M of funds against $895.4B of commitments
(0.04%) and ~$1.7–2.3B of implied violator revenue is the proportionality
question in one ratio. Ask for remedy as a rate (per displaced-task dollar,
per revenue dollar), not as a program count.

**What would falsify our critique.** Cohort-level employment/earnings
outcomes for Corps fellows and benefits-access households at 12/24 months,
third-party evaluated, with the same treatment for a measured harmed cohort.

**Ask.** GOV-2 + GOV-9 + GOV-10: outcome registry, violator-revenue
disgorgement, metered displacement.

#### 6.7.5 Pillar 5 — "AI's benefits are shared by everyone"

**Cantus firmus.** Connectors to DHS/IHME/PopHIVE/Learning Commons data;
IRC Burkina Faso dashboards (25,000-case pneumonia spike; 6,000 prenatal
visits vs 1,762 attended deliveries surfaced); DRC Ebola monitoring with
CEPI-convened partners, WHO-Africa sitrep under an hour; Claude for Teachers,
Ghana lesson-planning for ~68,000 instructors, Teach For All in 63 countries;
Claude Science plus free/discounted seats to 3,000+ institutions; protein
binders, a potentially novel enzyme system, a computer-checked Fermat proof
claim, UCSF genetic workups at ~1/10 time.

**Counterpoint.** Use "heavily concentrated in wealthier countries and among
higher-income, white-collar workers." Health/education: "we don't yet have
evidence that these efforts have had their intended effects." The binder
result — the strongest benefit claim in either document — survives scrutiny
narrowly: two independent labs confirmed *binding* for 17/211 constructs on
one toxin family; neutralization and any medicine remain untested. The
33,000-flaw headline does not survive as stated: partner-reported, no public
CVE-level deduplication or severity audit in sources reviewed. The Fermat
and enzyme claims enter this paper exactly as Anthropic filed them: as
claims (circle 3) awaiting the artifacts that would make them findings.

**Institutional read.** Distribution today follows ability to pay token
prices plus nonprofit discounts — a pricing policy, not a sharing
architecture. Sharing architectures have exits, offline/local operation,
and no-training guarantees for the data of the people being "reached."
None is specified for patient registers, student data, or citizen records
in the cited deployments. That silence, in a privacy-risk filing, deserves
a diligence question, not an assumption in either direction.

**What would falsify our critique.** Partner-published outcome evaluations
(mortality, learning gains, time-to-diagnosis) and data-governance terms for
each flagship deployment, in the partners' names.

**Ask.** GOV-2 + GOV-6 + GOV-7: outcome entailment, exit/deletion proof,
provable no-training on beneficiary data.

---

## 7. The answer

5. **Therefore the remedy is not a bigger settlement. It is governance with
   standing, triggers, and penalties** — §7 specifies ten mechanisms, each
   with who can pull it, what it measures, and what it costs Anthropic when it
   fires. Every one is buildable before the IPO prices. None requires
   Anthropic to be less serious. All require seriousness to be *checkable by
   someone Anthropic does not appoint, pay, or outvote*.

> A settlement pays for a car accident. It does not staff the intersection.
> Anthropic's current model is settlement, philanthropy, and revocable
> trustees. Governance is the intersection: rules that bind *before* impact,
> survive the individuals who wrote them, and can be invoked by the people
> hit. **[OPINION — the frame this paper argues]**

### 7.1 If Anthropic were serious about governance

Governance is how a system survives its individuals and balances *all*
affected interests accurately — not sincerely, accurately: with standing,
measurement, and consequence. Ten mechanisms convert every reputational
element above into an enforceable one. Each names **trigger / metric /
penalty**. Descartes precedents are the small, working versions (with their
own limits — §8).

| # | Mechanism | Trigger (who pulls) | Metric | Penalty on fire |
|---|---|---|---|---|
| GOV-1 | **Doubt-first replication gate** — no capability/safety/productivity claim ships until an accredited external evaluator reproduces it | Evaluator (METR-type, regulator-accredited, paid from escrow not fees-for-pass) | Reproduced effect + CI vs claim | Release and claim **blocked**; S-1-style restatement if already public |
| GOV-2 | **Existence ≠ entailment registry** — every benefit claim filed as (quote/source exists) vs (outcome entailed, measured) | Auditor; any investor can query | % of public claims with measured outcome; LTBT "inputs→outcomes" made numeric | Exec comp escrow until outcome rate clears a floor; corrections as new filings, never edits |
| GOV-3 | **Circle labelling** — public claims tagged circle 0 artifact → 4 human attestation, with per-stage loss | Auditor downgrade | Overstated/unlabelled claims count | Per-claim marketing prohibition + fine; Glasswing/80% figures could not print above circle 3 today |
| GOV-4 | **Contest standing (`against`)** — cure §365/367 by charter: purpose-trust enforcer + affected-person/class contest with equal visibility | Named subject, author class, host community, worker cohort | Contests unresolved >90 days | Injunction on the contested use + victim-fund payout; P13 built, not promised |
| GOV-5 | **Frameworks-as-data** — ≥3 external evaluation frameworks rate the same evidence; divergence published | Framework divergence > threshold | Inter-framework gap | Board supermajority incl. non-founder, non-LTBT-appointed seats to proceed |
| GOV-6 | **Exit with proof** — rights-holder/user deletion incl. model-effect exit, tested for residual memorization | Rights-holder/user | Deletion SLA days; residual-memorization test | Per-work/per-day damages; retrain-or-destroy for documented retention (Bartz made prospective) |
| GOV-7 | **No-training provenance ledger** — hash-chained training-corpus ledger; binding no-train on contested/customer data | Rights-holder/auditor spot-check | % corpus licensed/provenanced | Disgorgement + derivative-model destruction for unprovenanced slices |
| GOV-8 | **Irrevocable mission lock** — move Class T economics+votes (or a golden veto on purpose/sale/model-transfer) to a purpose trust with an enforcer; delete sunset/redemption and supermajority trustee-removal | Any amendment/sale attempt | Attempt = breach | **Transaction void.** This is the Patagonia/Bosch step; everything else is commentary on its absence |
| GOV-9 | **Misuse-revenue disgorgement** — audit the disclosed 5–7% quarterly | Auditor finds >1% | % revenue + downstream victim count (which Anthropic must now count) | 3× disgorgement to victims, exec clawback, customer ban. Misuse stops being a revenue line |
| GOV-10 | **Incident + externality bond** — mandatory timed disclosure of eval-escape class incidents; metered power/water/displacement per site vs bond | Auditor, community, regulator | Hours-to-disclose; MWh, litres, headcount | Bond forfeit + curtailment; the 4-model incident would be an S-1 item, not a Report anecdote |

**Pre-IPO asks (investors/regulators can condition on these now):**
(1) File the Trust Agreement terms that decide GOV-8 in plain prospectus
language — sunset, removal %, enforcer standing — and read the shares as
controlled-company stock until changed (a disclosure instruction, not a valuation view). (2) Quantify the 5–7% in dollars
per quarter going forward with auditor attestation (GOV-9). (3) Publish
site-level power/water commitments behind the $895.4B schedule (GOV-10).
(4) Convert the 5% Fund from wholly-owned subsidiary to independently
trustee'd vehicle with non-Anthropic enforcer, or stop calling it
"separate." (5) Restate flagship benefit numbers under GOV-2/GOV-3
labelling in the next amendment. None of these slows a safe frontier.
All of them slow an *unverifiable* one — which is the Report's own stated
preference ("pace the frontier," Sept 2026).

### 7.2 What Praxis builds instead — the alternative mechanisms

The GOV-1…GOV-10 asks are governance *demands* on Anthropic. Praxis is the other
half: the mechanisms we are building so the demands are running code anyone can
inspect, re-run, and extend — not rhetoric. Where Anthropic's model is
settlement, philanthropy, and revocable trustees, Praxis's is verification,
distribution, and a public commons.

- **A Rust-based verifier (Descartes).** Deterministic, content-addressed,
  byte-exact. Every claim quotes its evidence; the graph rebuilds from scratch
  to a single BLAKE3 root; a changed quote fails the check and cascades. Small
  and auditable on one machine — the opposite of "trust our internal eval."
  This paper's own numbers were checked by it, and it caught one of our errors.
- **Direct analysis, not delegated trust.** We read the primary filings and
  quote them, rather than cite a press release that cites a filing. The chain
  claim → quote → source byte-range is explicit and short; circle-tagging
  (circle 0 artifact → circle 4 attestation) records how far any statement sits
  from the bytes, so nothing is laundered up a citation ladder.
- **Distributed compute, pull-only.** Verification runs where the data is — no
  central server to compromise, no single point of control, no IP to protect.
  Anyone can clone the graph and reproduce the root on their own hardware. The
  architecture *is* the governance claim: no one operator, us included, is a
  trusted intermediary.
- **Artifacts submitted to a public epistemic commons.** Each pass in this
  document's own construction — drafting, this verification pass, the next —
  is a durable, timestamped artifact carrying its model/author context, filed
  into a public, versioned commons where it can be contested. The commons gains
  value *through* disagreement: a contest is a first-class record, answered in
  the open, never overwritten — the `against` relation §365(b) denies the
  public, built rather than promised.

None of this needs Anthropic's cooperation to exist. That is the point: a
standard you can only trust if the governed implements it is not a standard.

Praxis is what the check looks like in someone else's hands — and the hands are
everyone's.

> Praxis humility (same buzz saw, own neck): Descartes today is a
> single-machine, single-writer verifier, darwin/arm64 only, with the `against`
> relation and multi-tenant operation still unbuilt (§8). These mechanisms
> transfer as *design*, tiered DESIGNED, not deployed proof. We are not exempt
> from our own rubric.

---

## 8. What would change our mind

### 8.1 Open questions — and the one that governs them

As chief investment officer and fiduciary — the balancer, at the strictest
standard, of the client's interest against every input in reach — the governing
question is not *"is Anthropic well-intentioned?"* It is: **what levers are
available for an interested community to push back on this?** For the communities
§4b names, the honest answer today is close to none — no standing, no seat, no
metered harm, no contest. The verdicts above are stable; the items below are
where this paper is most exposed, published as explicit invitations to contest.
File against any of them — a contest is a record, answered in the open, never
overwritten.

1. **The mechanism for the future.** The charter governs for "the long-term
   benefit of humanity," yet the only enforcers are ≥2%/$2M stockholders suing
   derivatively (§367). What lever can the public — or an affected community —
   actually pull? We claim: none. Refute by naming one.
2. **Partner-reported counts.** We found "129,000" is not in the filing. Which
   other flagship benefit numbers originate outside the filings, and what is each
   one's independent, deduplicated basis?
3. **Site-level externalities.** The S-1 extract carries no MW/MWh/water/GHG per
   site. What are they, and who bears the noise, grid, and water load?
4. **The hardware supply chain.** Fab labor, water, and critical-minerals exposure
   behind the $895.4B compute commitment are absent from both documents.
   Enumerate them.
5. **Misuse-revenue dollars.** Dollarize the disclosed 5–7% policy-violator
   revenue by quarter and violation type, with downstream victim counts.
6. **The irrevocability question.** Produce the Trust Agreement terms (sunset,
   removal %, enforcer standing) that decide whether the mission lock is real or
   revocable (GOV-8).
7. **The exclusion channel.** What standing, if any, does a Global-South worker,
   a low-connectivity user, or a fab-line community have to be heard inside this
   governance — and if none, what would create it?

The standing/limits/falsifiers below (§8) bind this paper to the same test it
puts to Anthropic.

### 8.2 Standing, limits, and what would change our mind

**Standing pass.** This paper is sponsor-side analysis by a values-aligned
adviser building a competing governance artifact (Praxis/Descartes). That
interest is disclosed, and Descartes is held to the same standard below.
No affected author, data-center neighbor, entry-level worker, labelling
worker, NCII victim, or Claude user was interviewed; their positions enter
through court records, surveys, and Anthropic's filings — testimony about,
not voice from. Anthropic's health/education anecdotes center African
partners as beneficiaries in Anthropic's voice; we treat them as
Anthropic claims (circle 3), neither endorsing nor dismissing the partners'
work. The correction path for anyone named or miscounted here is the same
one we demand in GOV-4 and do not yet operate publicly ourselves: a new,
visible, contesting record — issues against this repository, answered in
the open, nothing overwritten.

**Praxis humility (same buzz saw, own neck).** Descartes today is a
single-machine, single-writer Rust verifier: 234 claim rows, five node
kinds, darwin/arm64 only, negative test suite open, no tenants, no keys,
no `against`, no second implementation, no Praxis license. It does not
prove GOV-1–GOV-10 scale to a frontier lab. It proves a narrower thing:
that witness testimony (including LLM testimony about itself) can be put
under byte-exact, rebuildable, loss-measured check — and that doing so
catches the witnesses being wrong, including ours. The mechanisms transfer
as *design*, tiered DESIGNED, not as deployed proof. Anthropic, with
$33.2B of nine-month revenue, does not have our excuse.

**Falsifiers.** We withdraw or amend the verdict if Anthropic publishes:
(1) CVE-level, deduplicated, externally attested security-benefit counts;
(2) outcome (not dashboard) evaluations from IRC/WHO-class partners;
(3) an audited corpus-provenance percentage with an operating rights-holder
exit; (4) quarterly misuse-revenue dollars trending under 1% with victim
counts; (5) an irrevocable charter amendment implementing GOV-8; or
(6) metered site footprints. Each is a document, not a decade.

**Unresolved in this pass:** full S-1 risk-factor enumeration (keyword
windows sampled a 245k-word filing — absence claims are MED confidence);
LTBT trustee-removal/enforcer terms pending the Trust Agreement exhibit;
medical-hallucination quantified patient harm (no primary series found);
Anthropic's labelling supply chain and site footprints (undisclosed in
sources reviewed); *Drakes Landing* full opinion (counsel summaries only).
Evidence artifacts for external claims are the URLs inline; key filings
should be ingested into the Descartes graph as claims before any
compliance-sensitive republication.

---

## 9. Back matter

### Appendix A. Governance scorecard (filed vs serious)

Scoring: ● held/verifiable today · ◐ partial/revocable · ○ absent.
"Serious" = §7 mechanism executed in charter/contract, not in a report.

| Dimension | Filed today | Serious (this paper) |
|---|---|---|
| Mission lock durability | ◐ LTBT elects 4/7; Class T amendable/redeemable; Founder F 50.1% | ● Purpose trust holds votes+economics or golden veto; sunset deleted (GOV-8) |
| Standing of the affected | ○ §365(b) no duty; §367 2% gate | ● Enforcer + affected-class contest (GOV-4) |
| Independent verification | ◐ Voluntary red-teams/evals; "no mandatory independent check" | ● Accredited replication gate with blockade (GOV-1) |
| Claim discipline | ○ Self-estimated benefits; unaudited counts | ● Existence/entailment registry; circle tags (GOV-2/3) |
| Framework pluralism | ○ One constitution, one scaler (RSP) | ● ≥3 external frameworks, divergence public (GOV-5) |
| Corpus rights | ◐ Bartz paid for pirated slice; rest asserted | ● Provenance ledger + exit-with-proof (GOV-6/7) |
| Misuse economics | ○ 5–7% revenue disclosed, retained | ● Audited quarterly; 3× disgorgement >1% (GOV-9) |
| Externality metering | ○ No site MW/water in extract | ● Bonded metered disclosure (GOV-10) |
| Benefit vehicle independence | ○ 5% in wholly-owned subsidiary | ● Independently trustee'd, external enforcer |
| Incident disclosure | ◐ Report-level candor, S-1-silent (4-model case) | ● Timed, bonded, filing-grade (GOV-10) |

**Implementation order we would underwrite:** pre-pricing — Trust terms in
plain language, 5–7% dollarized, Fund independence or relabelling,
flagship numbers re-tagged (GOV-2/3). First 12 months public — evaluator
contract with blockade, corpus ledger v1 + rights-holder exit, quarterly
misuse-revenue audit. Charter amendment cycle — GOV-4 standing, GOV-8 lock.
Sequence matters: disclosure before lock-in is cheap; lock-in before
disclosure is how controlled issuers stay controlled.

### Appendix B. Diligence question bank (institutional use)

**Control.** 1) Exact vote thresholds and notice periods to amend/redeem
Class T, remove trustees, and amend the Company Purpose — which classes,
what consideration? 2) Who appoints successor trustees, and who can block?
3) What can the LTBT see (board materials, eval raw data, incident logs)
and what can it compel? 4) Class F transition: who holds Founder LLC votes
during the 450 days, and who decides a founder is no longer "continuing"?
5) Which Nasdaq controlled-company exemptions will be taken, for how long?

**Safety claims.** 6) One release an external evaluator stopped or delayed —
name it. 7) Raw jailbreak success rates by category for the last two models,
with evaluator identity. 8) Incident taxonomy and counts (eval escapes,
unintended actions) per quarter; median time-to-contain. 9) What share of
safety-eval generation is now model-authored, and how is that share itself
audited? 10) Unresolved external red-team findings older than 90 days.

**Corpus and rights.** 11) What % of current training corpus is (a) licensed,
(b) public domain, (c) fair-use-asserted, (d) contested in litigation?
12) Rights-holder opt-out/deletion: volume, SLA, and how model-effect
removal is tested. 13) Music/publisher exposure beyond Bartz: accrued?
14) Customer-data training terms by product tier, verbatim. 15) Labelling
vendors, geographies, wage floors, and audit rights.

**Revenue quality.** 16) Dollarize the 5–7%: by violation type, refunded or
retained, repeat-offender policy? 17) Revenue concentration: state/national-
security customers as % and termination rights. 18) How much usage growth is
Anthropic's own internal/agent-loop consumption vs external cash demand?
19) Take-or-pay exposure if utilization falls 30%: annual fixed floor by
year against the $447.5B pre-2031 schedule. 20) CSP partner-conflicts:
allocation priority when a supplier-competitor's demand collides with yours.

**Footprint and distribution.** 21) Site-level MW, PUE/WUE, water source,
and grid-upgrade cost allocation behind the commitment schedule. 22) Which
sites use on-site gas generation; air-permit status. 23) Outcome metrics
(not seats/dashboards) for Burkina Faso, DRC, Ghana deployments, and the
data terms governing beneficiary records. 24) Corps/Futures Fund: evaluator,
counterfactual design, 12/24-month earnings outcomes. 25) Non-English and
low-connectivity performance: eval scores and effective price per successful
task by language band.

A management team that answers 1–5 and 16 in writing has earned a different
conversation than one that re-presents the pillars.

### Appendix C. Flagship claim register (verdicts)

| Claim (Report) | Verdict | Basis in one line |
|---|---|---|
| "Designed new protein binders… success rate well above industry standard" | NUANCED/HIGH | Independent wet-lab binding confirmed (17/211, one family); neutralization/medicine untested |
| ">33,000 critical- and high-severity flaws" (129,000 total program) | UNVERIFIED/MED | ~33 partner reports; **"129,000" is not present in the PBC Report text** (loop audit, 2026-11-03); no public CVE-level dedupe/severity audit found |
| Ebola sitrep "under an hour instead of up to a full day" | UNVERIFIED/LOW (outcome) | Process claim; no partner outcome evaluation found; Report admits no effect evidence (p.16) |
| Dashboards "flagged a spike of 25,000 pneumonia cases" | UNVERIFIED/LOW (outcome) | Detection ≠ cases averted; no outcome series |
| "Claude estimates 80% task-time cut" (research) | MISLEADING as economy claim | Model-estimated, excludes validation/selection; field range −19% to +55% by task |
| "11.4M accounts banned H1 2026" | CONFIRMED as self-report | Measures abuse throughput and enforcement; not victim or safety-outcome count |
| "81,000 users in 159 countries" want time back | CONFIRMED as survey-of-users | Users only; cannot speak for the affected non-users the charter names |
| "No universal jailbreak" (Opus 5.5 cyber) | NUANCED | Scoped claim under stated hours/requests; category rates undisclosed |
| "First complete computer-checked proof of Fermat's Last Theorem" | UNVERIFIED here | Filed as claim; artifact (checker + proof term) not examined in this pass |
| "~20% of shares toward public good" | UNVERIFIED (hope) | Sums a subsidiary contribution, personal pledges (voting unchanged), matched pledges, milestones |
| "$895.4B commitments" (S-1) | CONFIRMED/HIGH, NUANCED | ~$213.8B terminable/contingent; $69.8B/12mo; take-or-pay floors undisclosed by year in extract |
| Revenue $41M→$386M→$4,585M (2023–25 audited); $33,242M 9M-2026; Q3-26 $16,956M | CONFIRMED/HIGH | Net losses dominated by fair-value note/SAFE marks; operating loss 9M-26 $1,260M on $18,808M compute/infra opex — read cash, not headline loss |

### Appendix D. Sources

Primary: [Public Benefit Report](https://www-cdn.anthropic.com/a9ceec76a54d28d27affffcdab6faf7c142cd587.pdf);
[S-1/A-1, Reg. 333-299633](https://www.sec.gov/Archives/edgar/data/2130357/000162828026068676/anthropicpbc-sx1ax1.htm);
[Anthropic threat-intelligence report (Aug 2025)](https://www.anthropic.com/news/detecting-countering-misuse-aug-2025);
[GTG-1002 report (Anthropic PDF)](https://assets.anthropic.com/m/ec212e6566a0d47/original/Disrupting-the-first-reported-AI-orchestrated-cyber-espionage-campaign.pdf);
[protein-design research](https://www.anthropic.com/research/Claude-accelerates-protein-design);
[productivity-estimate research](https://www.anthropic.com/research/estimating-productivity-gains);
[Cyber Verification Program](https://www.anthropic.com/news/cyber-verification-program).

Law and courts: [DGCL §365](https://law.justia.com/codes/delaware/title-8/chapter-1/subchapter-xv/section-365/);
[Delaware Title 8 subchapter XV](https://law.resource.org/pub/us/code/de/title8/c001/sc15/index.html);
[*Bartz* settlement approval (AAP)](https://publishers.org/news/aap-welcomes-courts-final-settlement-approval-in-bartz-v-anthropic/);
[*Bartz* fair-use distinction (Legal500)](https://www.legal500.com/intelligence/united-states/intellectual-property/what-you-need-to-know-about-the-anthropic-ai-copyright-settlement);
[*Drakes Landing* PBC/Revlon summary](https://www.legal500.com/intelligence/united-states/corporate-commercial-law/delaware-court-confirms-pbc-directors-need-not-maximize-shareholder-value).

External evidence and counterweights: [Stanford entry-level "canaries" study](https://digitaleconomy.stanford.edu/news/canariesaug26/);
[independent binder confirmation](https://www.mlllm.io/articles/3701-claude-designed-proteins-that-bind-scorpion-toxins-two-independent-labs-confirmed-17-of-211-constructs/);
[GTG-1002 independent caveats (CSOH)](https://csoh.org/breaches/anthropic-gtg-1002.html);
[steward-ownership models (Bosch/Novo/Patagonia/golden share)](https://steward-ownership.com/en/resources/basics/what-is-steward-ownership);
[foundation-ownership analysis (Harvard CorpGov)](https://corpgov.law.harvard.edu/2025/05/28/purpose-that-matters-what-foundation-ownership-teaches-us-about-sustainable-capitalism/);
[Patagonia purpose trust](https://purpose-economy.org/en/companies/patagonia/).

Praxis base: [`praxis-white-paper.md`](praxis-white-paper.md),
[`praxis-standard.md`](praxis-standard.md),
[`../README.md`](descartes-spec.md) (Descartes spec, P1–P16),
[`primitives.md`](primitives.md), [`epistemics.md`](epistemics.md),
[`circles.md`](circles.md), [`strictness.md`](strictness.md).
Any number above without a link is traceable to the Report or S-1 page/file
cited at first use; ingestion of each external source into the Descartes
graph (`claims/`, quote-checked) is the tracked follow-on, and this paper
should be re-issued with claim ids when that lands.

### Appendix E. Data corpus: the index, run on the S&P 500 *(design; nothing below is ingested yet)*

The [Risk–Governance Index](risk-governance-index.md) joins each risk a company
discloses to the mechanism that would control it. Nothing in that join is
specific to Anthropic. Run it on every S&P 500 filer and it answers one
question: of the risks companies tell investors about, how many have a
mechanism someone outside management can pull?

Scaling the index from one filer to five hundred forces two changes:

- **A generic mechanism test.** GOV-1…10 are written for an AI lab. Across
  industries, a mechanism scores one point for each of the five properties §7
  demands: an **owner** who can pull it, a **metric**, a **trigger**, a
  **penalty**, and **independence** from management. A 0–5 score splits one
  broad judgment into five narrow ones, each checkable against a quote.
- **A fifth status, `Undisclosed`.** A mechanism absent from the filings may
  exist and simply not be written down. At scale, conflating "no mechanism" with
  "no disclosed mechanism" would overstate `Uncontrolled` for every filer.

**The three sides of the join.** Sources were confirmed live on 2026-11-03.
Caveats are the publishers' own.

| Side | Dataset | Publisher | Coverage / access | Caveat |
|---|---|---|---|---|
| Risk | [EDGAR full-text search](https://www.sec.gov/edgar/search/) | SEC | Full text of electronic filings since 2001; free | — |
| Risk | [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) (submissions, XBRL companyfacts / companyconcept / frames) | SEC | Free, no key; nightly bulk ZIPs; 10 requests/second with a declared User-Agent ([fair access](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)) | XBRL carries the dollar exposure that weights each risk |
| Risk | [EDGAR-CORPUS](https://huggingface.co/datasets/eloukas/edgar-corpus) (Loukas et al., [ECONLP 2021](https://aclanthology.org/2021.econlp-1.2)) | Academic | Annual reports 1993–2020, pre-split by item (incl. 1A) | No formal license; ends 2020, so recent years come from EDGAR directly |
| Mechanism | Cybersecurity governance, Reg. S-K Item 106 ([Release 33-11216](https://www.sec.gov/rules-regulations/2023/07/s7-09-22)) | SEC | Annual reports for fiscal years ending on or after 2023-12-15 | Mandated governance disclosure for the same risk the filer lists in Item 1A |
| Mechanism | Clawback policies, Rule 10D-1 ([Release 33-11126](https://www.sec.gov/rules-regulations/2022/10/listing-standards-recovery-erroneously-awarded-compensation)) | SEC | Policy filed as an exhibit to the annual report | A penalty mechanism in standard form: who pulls it, and on what trigger |
| Mechanism | Proxy statements (DEF 14A): committee charters, compensation metrics | SEC / EDGAR | Free | Owner and independence for most board-level mechanisms |
| Enforcement | [SEC litigation releases](https://www.sec.gov/enforcement-litigation/litigation-releases) and [AAERs](https://www.sec.gov/enforcement-litigation/accounting-auditing-enforcement-releases) | SEC | Free | The SEC states the AAER list "is not meant to be a complete and exhaustive compilation" |
| Enforcement | Form 8-K Item 1.05 incident filings | SEC / EDGAR | Since 2023-12-18 | Many incidents are filed under Item 8.01 instead ([Debevoise tracker](https://www.debevoisedatablog.com/2026/05/21/cybersecurity-incident-disclosure-form-8-k-tracker-two-year-update/): 29 under 1.05 vs 50 under 8.01 as of 2026-05-21); filter on both |
| Enforcement | [Violation Tracker](https://violationtracker.goodjobsfirst.org/) | Good Jobs First | Federal cases since 2000 plus state and local; 700,000+ cases | Downloads are subscriber-only; redistribution terms unconfirmed; excludes penalties under $5,000 |
| Enforcement | [EPA ECHO](https://echo.epa.gov/tools/data-downloads) | EPA | Free bulk CSV; 1.5M+ facilities | No parent-company key; facility→parent mapping is ours to build |
| Enforcement | [DOL enforcement data](https://data.dol.gov/) (OSHA, WHD) | DOL | Free; API key | Successor to enforcedata.dol.gov |
| Enforcement | [CFPB enforcement actions](https://www.consumerfinance.gov/enforcement/actions/) | CFPB | Free | No actions listed after 2025-08-21 |
| Enforcement | [FTC cases and proceedings](https://www.ftc.gov/legal-library/browse/cases-proceedings) | FTC | Free | — |
| Enforcement | [CourtListener / RECAP](https://www.courtlistener.com/help/api/bulk-data/) | Free Law Project | Free quarterly bulk snapshots; rate-limited API | — |
| Enforcement | [Stanford Securities Class Action Clearinghouse](https://securities.stanford.edu/) | Stanford Law / Cornerstone | — | Offline as of 2026-11-03; access terms unconfirmed |
| Universe | [S&P 500 constituents](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies) and [historical changes](https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500) | Wikipedia (CC BY-SA); index owned by S&P DJI | Free | Not authoritative; S&P DJI publishes no free point-in-time list. Pin a revision id: the as-of date is a recorded input, never a sample of the clock |

**The measures.** Each one is computed per risk factor, per filing, so every
row diffs against the prior year.

- *Coverage ratio.* The share of disclosed risks rated `Controlled`, weighted
  by materiality (XBRL exposure where one exists).
- *Externalization.* How often a factor places control outside the company: the
  industry, the state, third parties, "factors beyond our control."
- *Hypothetical vs realized.* Risks written as "could" after they have
  happened. The SEC charged Facebook $100M for presenting data misuse as
  hypothetical when it "had in fact been misused"
  ([2019-140](https://www.sec.gov/newsroom/press-releases/2019-140)).
- *Boilerplate and specificity.* Similarity to the industry centroid and to the
  firm's prior year ([Cohen, Malloy & Nguyen 2020](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12885)),
  plus entities, numbers and dates per factor
  ([Hope, Hu & Lu 2016](https://ideas.repec.org/a/spr/reaccs/v21y2016i4d10.1007_s11142-016-9371-1.html)).
- *Disclosure lag.* When an enforcement record lands, whether the prior filing
  disclosed that risk, and how specifically.

**What would falsify it.** If a low coverage ratio does not predict later
enforcement, incidents or restatements, the index is decoration, and we will
say so. Every model-assigned rating enters at circle 3, carries a byte-exact
quote that Descartes checks, and is rated by three independent labelers whose
disagreement is published (GOV-5, applied to ourselves).

**Pilot.** Cybersecurity first. The risk (Item 1A), the governing mechanism
(Item 106) and the incident record (8-K Items 1.05 and 8.01) all sit in SEC
filings, so the join can be tested end to end before it touches messier
ground.

---

*Governance is not the story a company tells about its intentions. It is
the set of acts other people can compel when intentions change, founders
leave, or the stock needs the quarter. Anthropic has built the story,
some of the trustees, and — to its credit — several of the admissions.
Build the compulsion. We will be first in line to verify it, byte for byte.*
