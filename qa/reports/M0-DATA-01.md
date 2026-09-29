# M0-DATA-01 — telemetry and correction event schemas v1.0.0 — build notes and QA pass

2026-09-29, gj-operator (overnight worker; Builder work, then the gj-data review hat). Delivered as a direct
commit to `main` (fast-forward model, AUTH #006/#007). The freeze is authorized by **APPROVED #029**
(2026-09-23), which also asks for the field design to be surfaced for the Owner's review and App Store
privacy-label alignment. That review is the one open item (see "Owner review" below).

## What was built
- `data/schemas/telemetry_events.schema.json` (JSON Schema 2020-12, `schema_version` const `1.0.0`): a common
  envelope (schema_version, event_id, pseudonymous user_id, session_id, env_id, client_version, platform,
  ts, scale_multiplier) plus `event` and a per-event `props` object selected by `allOf` / `if`–`then` on
  the event name. 18 events: session_start/end, scan_started/completed/failed, avatar_generated/failed,
  character_selected, play_started, fall, stuck, quit, summit_reached, route_started/completed, vista_found,
  rating_submitted, report_submitted.
- `data/schemas/correction_events.schema.json`: the same envelope plus `correction_submitted` (surface_id,
  old_label/new_label from the 14 Bible §4 classes, env-local position, confidence 0–1, training_opt_in).
- `data/schemas/fixtures/`: 38 valid fixtures (2 per event, both schemas) and 19 invalid ones (15 telemetry,
  4 correction), each rejected for one privacy or range rule.
- `data/schemas/tests/test_telemetry_schemas.py` (pytest, 70 cases; run by the lint workflow's pytest step).
- `data/schemas/README.md`: the version table, change rule, privacy invariants, envelope, event catalogue with
  weekly-report use, and a proposed App Store privacy-label mapping.

## Acceptance tests
| AT | Level | Result | Evidence |
|---|---|---|---|
| AT-1 envelope + catalogue | required | PASS (with a note) | `telemetry_events.schema.json`; `test_schema_is_valid_2020_12`, `test_every_event_has_a_props_definition`. avatar_generated/failed are defined (durations only) but marked **reserved for V2**: AUTH #020 removed avatar generation from v1, so v1 clients never emit them. |
| AT-2 correction_submitted | required | PASS | `correction_events.schema.json`; the Bible §4 enum is checked against `design/MOVEMENT_BIBLE.md` §4 (14 classes). |
| AT-3 forbidden fields | suggested | PASS | `test_no_forbidden_field_names` (GPS/lat/lon/location, email, phone, names, IDFA/IDFV/IMEI/serial/MAC/IP, media/URL/path/file), `test_no_unconstrained_strings` (every string is an enum, const or pattern, so no free text), `test_objects_are_closed` (`additionalProperties: false` on every object), `test_forbidden_pattern_catches_obvious_pii`; invalid fixtures `telemetry.gps-in-props`, `email-in-envelope`, `device-id-in-envelope`, `free-text-report`, `media-url-in-props`, `platform-device-model`, `correction.free-text-note`. |
| AT-4 fixtures + CI | suggested | PASS | `test_valid_fixture_accepted` (38), `test_invalid_fixture_rejected` (19), `test_every_event_has_two_valid_fixtures_and_one_invalid`; lint workflow on the delivery commit. |
| AT-5 gj-data sign-off | suggested | PASS (bot review) | See "gj-data review" below. The Coordinator may want an independent second review. |
| AT-6 APPROVED #n + README | required | PASS | The commit message cites `APPROVED #029`; the README records 1.0.0 and the change rule. |

Local: `pytest -q data/schemas/tests` gives 70 passed (jsonschema 4.26.0, as pinned in CI); ruff check/format clean.

## Design choices worth a look
- **Pseudonymous user_id** is a random UUID bound to the account server-side (not the Supabase auth id), and
  delete-all rotates it. Ingest must enforce this; the schema can only require UUID form.
- **Positions** are environment-local A units bounded to ±10,000 A. **Timestamps** must be UTC (`Z`), so the
  user's timezone offset is not logged.
- **Ratings**: each axis is 1–5 or null (the axis was left untouched), with at least one axis set. Skip sends
  no event.
- **Report reasons** follow decision 8d, including "other", with no comment field (no free text).
- **Added beyond AT-1** (all derived data, no PII): `session_id` (funnels), `character_selected` (the AUTH
  #024 roster), `surface_class` on fall, `falls` on summit/route events, and scan pass metrics (AUTH #025).

## gj-data review (weekly report needs)
- Fall, quit and stuck heatmaps: position, env_id and scale on all three. Covered.
- Completion rates: play_started, route_started/completed and summit_reached, keyed by route_id. Covered.
- Vista discovery: vista_found with vista_id and time. Covered. Ratings: four axes. Covered.
- Capture quality and readiness-predictor calibration: scan_completed metrics plus scan_failed stage and
  reason. Covered.
- Gap, not blocking: there is no event for "journey generated with template fallback" (AUTH #023). That is a
  backend pipeline event, not client telemetry, and belongs with the pipeline logs.

## Owner review (required by AUTH #029)
Please confirm: (1) the field list in `data/schemas/README.md`; (2) the proposed App Store privacy label:
User ID, Product Interaction and Diagnostics, all linked to the user and none used for tracking; no location,
contact info, photos/videos or device ID. Changes after this review need a new design-change AUTH, per the
change rule.

## Verdict
PASS. No defects. The freeze is technically complete; the Owner's field and label review is open.
