# `services/ranking/` — M4-DATA-02 ranking + anti-gaming

Owner: gj-data · AUTH #026 · SPEC §3.7

The ranking pipeline behind the locked sort tabs (DESIGN_SYSTEM decision 8b): **Top this
week · New · Near your scale**. Pure standard library; the score is a pure function of its
inputs, so the DB (ratings/leaderboard, M4-DATA-01) and telemetry adapters that feed it are
a thin layer added on staging.

## Score (composition option A — balanced blend, telemetry-tunable)

`base_score = ratings_weight · rating_component + signals_weight · signal_component`, scaled
to 0–100. Every weight lives in `weights.json` and is normalised at load, so weights can be
re-tuned from telemetry post-launch without a code change (AT-1).

- **rating_component** — the four community axes (fun / interesting / interactive /
  exciting, 1–5) blended per `rating_axes`, after anti-gaming, Bayesian-shrunk toward a
  prior and mapped to 0–1.
- **signal_component** — five derived objective signals blended per `signals`:
  `verticality` (summit height), `move_variety` (distinct verbs across the routes),
  `reachable_volume` (traversal-node bbox over the environment bbox — a proxy until the
  v1.1 signals block), `completion_rate` and `replay_rate` (from play telemetry).

## Sort tabs (AT-2)

- **Top this week** — `base_score × exp(-ln2 · age_days / half_life_days)`, so fresh,
  well-received places surface.
- **New** — recency (`published_at`).
- **Near your scale** — Room vs Tabletop filter, then Top-this-week order.

## Anti-gaming (AT-3, SECURITY_CHECKLIST §10.2 — survives a deliberate rate-spam test)

Layered so a scripted spam attack cannot materially move a rank (measured: 200 spam ratings
move the 0–100 score by ~1 point, vs a naive mean that a single burst pushes to ~99):

1. **One rating per account** — deduped to the latest (the DB also enforces `unique(env,
   user)`).
2. **No self-rating** — the creator's own rating is dropped.
3. **Per-device cap** — at most `per_device_cap` ratings counted per `device_hash`, so a
   Sybil farm sharing a few devices contributes little.
4. **Brigade discount** — a low-trust rating inside a burst (many ratings in a short window)
   is discounted.
5. **Account-age trust weighting** — new accounts count for a floor fraction until they age.
6. **Bayesian shrinkage** — the mean is pulled toward a prior by `rating_prior.strength`
   pseudo-ratings, so a handful of spam ratings barely move it.

The rate-limit + one-per-account + hashed-device foundations live in the M4-DATA-01 migration
(#038); this service is the scoring + weighting layer on top.

## Files

- `ranking.py` — config load, rating aggregation + anti-gaming, signals, blend, feeds.
- `weights.json` — the tunable weights and thresholds.
- `tests/test_ranking.py` — shrinkage, each anti-gaming layer, the rate-spam simulation, the
  three sort tabs, and determinism.
