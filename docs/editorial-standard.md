# Being understood

It is not the reader's job to understand us; it is our job to be understood
by them (Sloane, 2026-11-04). An argument can be correct line by line and
still leave most people with no idea what is happening. Correctness is
necessary, not enough. These rules apply to everything rendered from this
repository: the paper, its PDF and web versions, and their figures.

## One point per paragraph, made more than one way

- **One point per paragraph.** A paragraph's first sentence states the point;
  the rest of the paragraph earns it. If a paragraph makes two points, split it.
- **Make each point several ways.** A statement, a concrete example and, where
  possible, a picture or a number the reader can see change. A reader who
  misses the sentence should catch the picture.
- **Lead with the setup.** Say what the situation is before arguing about it.
- **Move between abstract and concrete.** Show one concrete case, then the
  general pattern, then back to the case, the way Bret Victor's
  [Ladder of Abstraction](https://worrydream.com/LadderOfAbstraction/) does.

## Show how it works

- **Inline illustrations.** Pictures sit next to the sentence they illustrate,
  not in a gallery at the end. The model is Victor's
  [Scientific Communication as Sequential Art](https://worrydream.com/ScientificCommunicationAsSequentialArt/):
  the argument told in a sequence of pictures, each with its words beside it.
- **Visualize as a rule** wherever there's a mechanism, a payoff or a
  comparison. For example, the Public Benefit Fund's share contributions
  should be shown with Anthropic's value on one axis and the Fund's shares on
  the other, as the S-1 milestones suggest.
- **Show our own machinery the same way.** How claims are pinned, checked
  and versioned is part of what we show, as a picture, not just a list of
  commit hashes.
- Every figure is generated from records, never drawn from hand-typed numbers
  (AGENTS.md, "Every rendering carries its verification chain").

## Primitives get their own page

A primitive is an idea or case that the argument stands on and that a
reader may meet cold, for example the **Woodcache case study** or **public
benefit corporations** themselves. Each primitive gets its own page (and its
own figure), written to stand alone. The argument links to it rather than
explaining it again in passing. A primitive page is written once and used
by every document that needs it.

**Questions point at primitives.** Before an open question goes on a trail
or into a ledger, it names the primitives it concerns (Sloane, 2026-11-04).
A question that fits no primitive either names a new primitive or isn't
ready. The draft primitive set is on Entire trail #30 ("Primitive set"):
method primitives such as pin, claim, graph, because-ness, check, circle,
badge, grant, fork, question and embargo, and domain primitives such as
public benefit corporations and the Woodcache case study.

## Links say what they carry

Links go both ways: the argument links to a primitive, and the primitive
lists everything that links to it. Every link also tells the reader how much
the target matters *here*, so the reader can decide whether to follow it.

That weight is **computed from the claim DAG, never assigned by hand**
(Sloane, 2026-11-04). The same computation orders the argument: a
*because-ness* score.

- **The DAG.** Each claim's `rests_on` column names the claims it stands on.
  In Descartes, `rests_on` is a conjunction: a claim fails if any claim it
  rests on fails (`descartes/src/claims.rs`). So every ancestor of a claim is
  load-bearing for that claim.
- **Order.** Premises come before what rests on them (a topological order).
  Where the order allows a choice, the claim with the higher because-ness goes
  first.
- **Because-ness of a claim** is how much of the argument rests on it: the
  number of claims that transitively rest on it, with the thesis (§0's
  conclusion) as the end point. A claim the thesis does not rest on has a
  because-ness of zero for the main argument, whatever else it supports.
- **Link weight** at a link from a passage making claim *c* to page *k*:
  - **needed** if *k* is an ancestor of *c*: *c* fails without it;
  - **more** if *k* is not an ancestor but supports something *c* also
    supports (they share a descendant);
  - **aside** otherwise.
- **Where it runs.** The computation reads only the claim graph, so it
  belongs in Descartes, in Rust, as a command beside `check` (AGENTS.md:
  no Python around Descartes).

## The argument lives in the DAG

Every inference a document makes is a claim row, not just its quotations
(Sloane, 2026-11-04). An argument row has `path` and `quote` set to `-` and
`rests_on` naming the claims it needs, so it stands only if they stand, and a
failure anywhere below it shows up in it.

- **List what a claim needs, not what corroborates it.** `rests_on` is a
  conjunction, so a corroborating quote listed there becomes a requirement.
  Descartes has no corroboration link yet; until it does, corroboration goes
  in a comment.
- **A premise with nothing under it stays in the file and fails.** It is
  not dropped and not quoted around: the failure is the finding that it needs
  a source.
- **The steelman is a row too**, and the thesis does not rest on it.

First encoding, 2026-11-04 (§0, rows A01–A09, T0, R0, step S15): the thesis
T0 fails. Five premises have no supporting claim yet: A02a (the Delaware
holding), A02b (the trust's four of seven), A02d (more disclosure than
peers), A03 (§367's 2% / $2 million standing) and A04 (amendability and the
50.1%). Two more fail through quotations that fail for instrument reasons:
A06 through Q025 (a PDF line break) and A09 through Q048 (duplicated HTML).
A01, A02c and A07 stand.

## The front page lays it all out

- **The title is the question** the document answers.
- **Authorship is set out cleanly:** who wrote it, for whom, and the conflicts.
- **Every output names its version:** the document's version, when it was
  generated, which commit it was generated from, and the versions of the
  software that did the work. This goes on the front page, as well as in the
  verification appendix.
- **How the method works is an editorial matter, kept in its own section.**
  It doesn't sit in the opening argument.

## Open (from the comments of 2026-11-04)

- A name for the form, other than "working paper": something like a
  *discourse*. The fact pattern is captured first; our algorithmic systems add
  context from different directions; our editorial sits on top as its own
  layer (`comments/anthropic-contrapunctus.tsv` C3).
- The version label should track the current state ("draft after v1", not
  "v0") (C2).
