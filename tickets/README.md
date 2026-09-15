# `tickets/`

One JSON file per ticket, validated in CI against `SCHEMA.json` by `validate.py`. Tickets are the unit of work, the unit of review, and the unit of progress tracking. If it is not in a ticket, nobody works on it.

## ID scheme

`M<milestone>-<AREA>-<nn>` — for example `M0-UNITY-04`. The filename is `<id>.json`. Areas: `REPO` harness and CI · `SKILL` Bot research handbooks · `UNITY` Unity project · `MOVE` movement constants and controller contract · `PIPE` Inngest / API · `PLAT` Supabase and platform · `DATA` schemas, telemetry, ranking · `QA` QA and release · `LEGAL` consent, retention, vendor terms · `DSGN` design system and UI · `CAPT` capture and reconstruction · `SCEN` scene graph, traversal, reactivity, Tier 2 · `AVAT` avatar · `GAME` gameplay features · `SEC` security work · `FORE` Foreman duties · `OWNER` Owner actions · `RES` research.

## Who does what

| Action | Who | How |
|---|---|---|
| Create a ticket | Coordinator (milestone decomposition) or Foreman (with Coordinator review) | PR adding `tickets/<id>.json`; must validate |
| Change acceptance tests | Coordinator only (Foreman may propose) | PR; acceptance tests are the contract a PR is reviewed against |
| Start work | Assigned Bot | PR (or the ticket's own PR) sets `status: in-progress`, `branch`, adds a `history` row |
| Open the PR | Assigned Bot | `status: in-review`, `pr` link, `history` row; PR uses the template |
| Request changes / merge | Coordinator only | Coordinator updates `status`, `history`, and `PROGRESS.md` on merge |
| Block / unblock | Bot or Foreman | `status: blocked` with `blocked_by`; file a BLOCKER issue if the Foreman cannot unblock within 8 h |

Status flow: `open → in-progress → in-review → (changes-requested → in-review)* → merged`. `done` is for tickets with no PR (Owner actions). `cancelled` requires a note.

## Rules

- Branch name is `ticket/<id>-<slug>` (exceptions: `setup/<role>-skills`, `auth/<nnn>-<slug>`, `checkpoint/M<n>`).
- Every acceptance test needs evidence in the PR (`evidence` says what). No evidence, no merge.
- A ticket that turns out to need spend, an account, or a change to a protected path stops and files an AUTH REQUEST; record it in `auth_required`.
- Scope creep goes to `BACKLOG.md`, not into the ticket.
- Run `python tickets/validate.py` before pushing; `python tickets/validate.py --summary` prints the table the Coordinator pastes into `PROGRESS.md`.
