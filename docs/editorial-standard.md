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

## Links say what they carry

Links go both ways: the argument links to a primitive, and the primitive
lists everything that links to it. Every link also tells the reader how much
the target matters *here*, so the reader can decide whether to follow it.
For example: *needed* (you can't follow the next step without it), *more*
(there's substantial material that bears on this point if you want it),
*aside* (background; safe to skip). This vocabulary is a proposal to be
settled before the first primitive pages are built.

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
