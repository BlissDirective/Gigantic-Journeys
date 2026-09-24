# gj-data — Working Handbook

Remit: telemetry, UGC moderation, leaderboard anti-cheat, and learning from corrections. Re-read at session start; update when you learn something. Authored 2026-09-24.

## GJ context
- **Telemetry + correction schemas are frozen v1.0** (`data/schemas/`, M0-DATA-01 / AUTH #029): pseudonymous ids only; **no GPS, email, raw-media references, or free text** (SECURITY_CHECKLIST §10.1). Field changes need their own AUTH.
- **Moderation = auto-clear + human-on-report** (AUTH #026): a vision-pass filter clears environments before public; one-tap report → human queue; block abusive users; published contact info (Apple 1.2, SECURITY_CHECKLIST §10.5).
- **Ranking = balanced blend** (four-axis ratings + objective signals; Top-this-week decay; anti-gaming/rate-spam). **Leaderboards = plausibility floor** reusing the deterministic reachability validator (M1-SCEN-05).

## Principles
- **Privacy by construction.** The schema admits no PII; a forbidden-field test guards it (§10.1). Never widen the schema without an AUTH.
- **Bots never see raw user media** beyond the published thumbnail/package (§10.4); the test corpus is Owner-supplied + consented (§6.5).
- **Anti-cheat is deterministic.** Impossible leaderboard times are rejected by validating against route length + movement.json constants (§10.3) — reuse M1-SCEN-05, don't reinvent.
- **Rate-limit everything** ratings/reports per user + device; anti-gaming rules pass a rate-spam test (M4 exit, §10.2).

## Techniques
- Vision-pass content filter for auto-clear; escalation to a human queue with an "Under review" state (§10.4).
- Active learning from user corrections (the correction-event schema) — improve scene/journey models over time without storing PII.
- Ranking blend: normalize the four ratings + objective signals (verticality, move variety, reachable volume, completion, replay); apply decay + anti-gaming.

## Pitfalls
- Any free-text/GPS/email/raw-media ref sneaking into telemetry → §10.1 violation (and CI/forbidden-field test should catch it).
- A leaderboard time not validated against movement.json → cheatable.
- Moderation giving Bots raw media → §10.4 violation.

## Checklist
Schema unchanged or AUTH-cited ✓ · no PII fields ✓ · rate limits + anti-gaming ✓ · plausibility floor on leaderboards ✓ · human-on-report queue ✓ · no raw media to Bots ✓.

## Pointers
`data/schemas/` · SPEC §3.7/§3.9 · SECURITY_CHECKLIST §10 · `design/proposals/publish-browse-rank-moderation-v1.md` · tickets M0-DATA-01, M4-DATA-01/02/03, M1-SCEN-05.
