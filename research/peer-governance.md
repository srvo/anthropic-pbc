# How firms that can kill people govern that risk

Leads, not pinned evidence. Each cell has a row in `peer-governance.tsv` with the finding, a verbatim quote and the URL (retrieved 2026-11-05). Sources: latest 10-K and DEF 14A, regulator pages, company reports; for Anthropic, the S-1, RSP v3.4, the 2026 PBC Report, SB 53 and the DGCL. Four metric rows (RTX, Lockheed, Quanta, Constellation) rest on unfetched search snippets.

Y = yes, P = partial, N = no.

| Firm | 1 Board committee | 2 Binding regulator | 3 Independent inspection | 4 Public safety metrics | 5 Incident disclosure | 6 Pay tied to safety | 7 Standing for affected | 8 Financial backstop |
|---|---|---|---|---|---|---|---|---|
| RTX | Y | Y | Y | Y | P | N | P | P |
| Lockheed Martin | Y | Y | P | Y | P | P | P | P |
| Quanta Services | Y | Y | P | Y | Y | Y | P | P |
| Boeing | Y | Y | Y | Y | Y | Y | Y | P |
| PG&E | Y | Y | Y | Y | Y | Y | Y | Y |
| Constellation | Y | Y | Y | Y | Y | N | Y | Y |
| Dow | Y | Y | P | Y | Y | P | Y | P |
| **Anthropic** | **Y** | **P** | **P** | **P** | **Y** | **N** | **P** | **N** |

## What the comparison shows

Every firm has a board committee for its lethal risk, and so does Anthropic. It is the cheapest mechanism, and the only one where Anthropic matches the strongest peers.

The firms differ most in whether an outside body can stop the work. The NRC can suspend or revoke a reactor licence, the FAA must approve any 737 production-rate increase, and the CPUC's enforcement process can end in receivership. Anthropic's nearest equivalent is SB 53: the California Attorney General can fine it up to $1 million per violation, including for failing to follow its own framework. No body can halt a training run or a deployment. This qualifies A050 and A057: a binding outside check exists, but it holds Anthropic to a standard Anthropic writes.

Inspection divides the same way. Nuclear plants have resident NRC inspectors and PG&E has a statutory independent evaluator. Anthropic's external review of its Risk Reports is voluntary, and Anthropic chooses the reviewers.

The utilities give the people they could harm both a claim and a fund to pay it: strict liability under inverse condemnation, Price-Anderson's pool, and a Wildfire Fund of at least $21 billion. These are weaker than they look, since Price-Anderson caps liability near $16.3 billion per incident and customers pay much of the Wildfire Fund. Anthropic has no fund sized to the harm, and the public has no claim to enforce its purpose (ordinary tort claims were not assessed). Its directors owe the public no duty under the PBC statute, and only holders of 2% of the shares (or $2 million of listed stock) can sue to enforce the public benefit.

Pay without a safety link is common (RTX, Constellation), so it is weak evidence on its own.

Anthropic is closest to the defense contractors: products that can cause mass casualties and weak standing for the people harmed. The difference is that RTX and Lockheed answer to a government customer that decides how their weapons are used, and Anthropic answers to no one in that position.

Some of these checks came after disasters: Boeing's 10-K says the FAA increased its oversight after the 2024 door-plug accident.
