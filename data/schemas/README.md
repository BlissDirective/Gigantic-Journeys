# `data/schemas/`

Owner: gj-platform (owner), gj-scenegraph (scene_graph/traversal_graph/environment_spec), gj-data (review)

Frozen schemas: telemetry and correction events (M0-DATA-01), scene graph, traversal graph, environment spec (M1). JSON Schema 2020-12, semver in `schema_version`. Any change needs an AUTH (design-change); CI blocks PRs here without an `APPROVED #n`.

## Versions

| Schema | Version | Frozen by | Status |
|---|---|---|---|
| `telemetry_events.schema.json` | **1.0.0** | AUTH #029 (2026-09-23) | frozen; field design awaiting Owner review (privacy label) |
| `correction_events.schema.json` | **1.0.0** | AUTH #029 (2026-09-23) | frozen; field design awaiting Owner review (privacy label) |

## Change rule

1. Schemas are frozen at the version above. Any change (a new event, field, enum value or range) needs its own design-change AUTH, cited as `APPROVED #n` in the commit or PR.
2. Additive changes (a new optional field, event or enum value) bump the minor version (1.1.0). Removing or renaming anything, or tightening a range, bumps the major version (2.0.0), and the pipeline must accept both majors during the migration.
3. `schema_version` is a `const`, so a client can only send the version it was built against. The ingest keeps a validator for each live version.
4. Every change ships with fixtures (at least two valid per new event, one invalid per new rule) and must keep `tests/test_telemetry_schemas.py` green, including the privacy invariants below.

## Privacy invariants (SECURITY_CHECKLIST §10.1, §4.4; SPEC §7)

Enforced by `tests/test_telemetry_schemas.py`:

- Every object is closed (`additionalProperties: false`), so nothing unlisted can be logged.
- Every string is an `enum`, a `const` or pattern-bound (ids, semver, UTC timestamp), so no user free text can be logged. The report reason is an enum; "other" carries no comment.
- No field is named after GPS/latitude/longitude/location, email, phone, name, device identifiers (IDFA/IDFV/IMEI/serial/MAC/IP), or media/URL/path/file/photo/video/audio.
- Ids are random UUIDs. `user_id` is a pseudonymous id bound to the account server-side, never the auth id, email or a device identifier, and delete-all rotates it. `platform` is `ios | android | editor` only.
- Positions are environment-local, in A units (one avatar height), never world or geographic coordinates.
- `correction_submitted` carries `training_opt_in` (default off, SPEC §3.9). Corrections with `false` are never used for training.

## Envelope (every event)

`schema_version` (const `1.0.0`), `event_id` (UUID), `user_id` (pseudonymous UUID), `session_id` (UUID), `env_id` (UUID or null), `client_version` (semver with an optional `+build`), `platform`, `ts` (UTC `...Z`), `scale_multiplier` (number or null), `event`, `props`.

## Event catalogue (telemetry 1.0.0)

| Event | Props | Weekly report use (gj-data) |
|---|---|---|
| `session_start` | quality_tier | device-tier mix |
| `session_end` | duration_s | session length |
| `scan_started` | capture_mode, pass_index | capture funnel |
| `scan_completed` | capture_mode, duration_s, passes, frame_count, coverage_pct, blur_frame_ratio, low_light_frame_ratio, tracking_loss_count, readiness_score, quality_gate | capture quality and readiness calibration |
| `scan_failed` | capture_mode, stage, reason (enums), duration_s | failure taxonomy |
| `avatar_generated` / `avatar_failed` | duration_ms | **reserved for the V2 custom-avatar track**; v1 has no avatar generation (AUTH #020), so v1 clients never emit them |
| `character_selected` | character_id | roster popularity |
| `play_started` | mode, route_id | play funnel |
| `fall` | tier (soft/roll/hard/recover/void_respawn), height_A, position, surface_class | fall heatmap |
| `stuck` | dwell_s (≥ 20), position | stuck heatmap |
| `quit` | elapsed_s, beat_reached, position | quit heatmap |
| `summit_reached` | route_id, elapsed_s, falls | completion rate |
| `route_started` / `route_completed` | route_id, route_index / time_s, beat_reached, falls | per-route completion and time |
| `vista_found` | vista_id, elapsed_s, position | vista discovery |
| `rating_submitted` | fun, interesting, interactive, exciting (1–5 or null; at least one set) | ratings (DESIGN_SYSTEM decision 8) |
| `report_submitted` | reason (private_information_visible, inappropriate_content, not_a_real_place, broken_environment, other) | moderation queue (decision 8d) |

Correction 1.0.0: `correction_submitted` with surface_id, old_label and new_label (Bible §4 classes), position, confidence (0–1) and training_opt_in.

## App Store privacy label (proposed mapping, for the Owner's review)

| Apple data type | Collected by these schemas | Linked to the user | Tracking |
|---|---|---|---|
| Identifiers → User ID | pseudonymous `user_id` | yes (account-bound) | no |
| Usage Data → Product Interaction | play, scan, route, rating, report and correction events | yes | no |
| Diagnostics → Performance / Other Diagnostic Data | quality_tier, scan quality metrics, failure stages | yes | no |
| Location, Contact Info, Contacts, Photos or Videos, Identifiers → Device ID | **not collected** by telemetry | — | — |

Purposes: app functionality and analytics (product improvement). The capture video itself is covered by the capture flow and privacy policy, not by telemetry.

## Layout

- `fixtures/valid/<schema>.<event>.<n>.json`: must validate (two or more per event).
- `fixtures/invalid/<schema>.<case>.json`: must be rejected (GPS, email, device id, free text, media URL, out-of-range values, wrong version and so on).
- `tests/test_telemetry_schemas.py`: pytest, run by the lint workflow.
