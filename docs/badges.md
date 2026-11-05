# Badges: citations last, status expires

A badge is a small image of a check result that someone can embed and click
through. There are two kinds, with opposite duties (Sloane, 2026-11-04).

## Citation badges are durable

A citation badge says *this is what I think, and here is exactly what it
rested on when I said it.* It must outlive its host, its links and the
repository's later history.

- **Pinned.** It names one commit and never changes. A later result gets a
  new badge; the old one stays true about its moment.
- **Self-contained.** The badge file carries its full reference in its own
  `<metadata>`: the document, repository and commit; the claim, its statement,
  witness and `rests_on`; the quote; the source (id, URL, fetch date, bytes,
  BLAKE3); the text it was checked in (path, recipe, SHA-256, offset); the
  checker binary's SHA-256; the SHA-256 of the full check output; and the
  command that re-verifies it. With every link dead, the file alone is enough
  to check it.
- **Content-addressed.** Its file name is `<claim>@<commit>-<digest>.svg`,
  where the digest is of the badge itself, so a copy can be checked against
  its name.
- **Deterministic.** The same commit and check output give the same bytes.

## Status badges expire

A status badge says *where this stands now.* Now ends, so the badge must too.

- **Dated on its face.** The visible text includes the date of the check it
  shows, so a screenshot dates itself.
- **Valid for a stated window.** After the window the host serves an
  expired badge that says *stale, recheck* in words and claims nothing. It
  never falls back to the last pass.
- **Unverified if the check can't run.** No result means no claim.
- **Time is an argument.** The as-of date and the window are recorded inputs,
  never read from a clock inside the generator (AGENTS.md, "Deterministic").

## Both kinds

- **Words, not just colour.** Every badge spells out its state ("fails",
  "ok", "5 unsourced", "stale").
- **Computed, never typed.** A badge is a pure function of the claims file
  and the check output.
- **Clicks through** to the claim's page: statement, quote, source, what it
  rests on and what rests on it.

## Who owns what

Three owners, split by authority (Sloane, 2026-11-04):

| Layer | Lives in | Owns |
|---|---|---|
| Sealing | Descartes | Computing the result and sealing it into the badge: the check, the digests, the embedded reference, signing. A Rust command beside `check`. |
| Design | Praxis | What a badge looks like and what it must carry: the visual form, the metadata schema, the rules on this page, shared by every Praxis producer. |
| Use | still to be named (not this repository by default) | What to do with badges: which to issue, where they're embedded and hosted, how long a status lasts. |

The prototype (`~/tray/argument-check-badges.html`, 2026-11-04) was a
throwaway script and belongs to none of them. This page is the design draft
until it moves to Praxis.

## Open

- The status window (the prototype used one day).
- Hosting for status badges and claim pages.
- Signing citation badges, once there's a key (Praxis `OPENQUESTIONS.md` Q1).
- Where the use layer lives. Tracked on Entire trail #29 for the central plan.
