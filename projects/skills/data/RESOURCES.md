# gj-data — Resources (curated foundation)

Curated, verified starter set for telemetry, moderation, anti-cheat, and privacy-preserving ML. Expand to the full annotated top-100 in a live pass. All entries real/canonical.

## Telemetry & analytics
- JSON Schema (json-schema.org) — frozen event validation.
- Game telemetry design — "Game Analytics" (Seif El-Nasr et al., book); GDC Vault analytics talks.
- Privacy by Design (Cavoukian) — pseudonymous-by-construction.

## UGC moderation
- Apple — App Review Guideline 1.2 (developer.apple.com/app-store/review/guidelines) — the UGC bar.
- Trust & Safety / content moderation frameworks (Digital Trust & Safety Partnership; TSPA — tspa.org).
- Vision content classifiers (cloud moderation APIs; open NSFW/again-check models) — the auto-clear pass.
- DMCA takedown process (copyright.gov) — §5A of our ToS.

## Anti-cheat & leaderboards
- Deterministic replay/validation for leaderboards (anti-cheat GDC talks, GDC Vault).
- Rate-limiting + anti-gaming patterns (backend security literature).
- Our own deterministic reachability validator (M1-SCEN-05) — reuse for the plausibility floor.

## Privacy-preserving ML / active learning
- Differential privacy — Dwork & Roth, "The Algorithmic Foundations of DP" (book/paper).
- Federated learning overview (Google AI blog) — learn without centralizing raw data.
- Active learning survey (Settles, 2009) — learning from corrections efficiently.

## Reference internal
- `data/schemas/`, SECURITY_CHECKLIST §10, `design/proposals/publish-browse-rank-moderation-v1.md`, `legal/`.
