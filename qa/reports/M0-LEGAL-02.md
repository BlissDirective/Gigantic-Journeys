# M0-LEGAL-02 — retention schedule + deletion flow — QA pass

2026-09-29, gj-operator (overnight worker). Documentation ticket: no code, no evidence images. Delivered as a
direct commit to `main`.

| AT | Level | Result | Where |
|---|---|---|---|
| AT-1 one row per SPEC §7 class with period, trigger, location, access, vendor | required | PASS | `legal/RETENTION_SCHEDULE.md` §1: all 8 SPEC §7 classes plus account identity and deletion receipts. The face/body row is kept, marked not collected in v1 (AUTH #020). |
| AT-2 raw media on derivation and ≤ 24 h; failed ≤ 7 days; face/body immediately | required | PASS (with a scope note) | Raw scan media row: deleted in the derivation run, hourly sweep, ≤ 24 h / ≤ 7 days. Face/body: not collected in v1; the V2 rule (immediately on device, in storage and at the vendor, with a receipt) is stated for the V2 track. |
| AT-3 DELETION_FLOW: entry point, steps per class, vendor calls + receipts, 30 days, user view, staging test | required | PASS | `legal/DELETION_FLOW.md` §2 (Settings → Account → Delete my data, confirmation, re-auth), §4 (8 ordered steps + processor table), §5 (receipts), §1/§3 (30 days, 24 h target, 7-day escalation), §7 (synthetic-user staging test + CI coverage check). |
| AT-4 DRAFT pending attorney review; cross-referenced from SPEC §7 | required | PASS | Both headers read "DRAFT … pending attorney review". SPEC §7 already names `legal/` (M0-LEGAL-02), so no SPEC edit is needed. `legal/README.md` lists both files. |

Consistency checks: SPEC §7 classes match 1:1. SECURITY_CHECKLIST §5.4 (30 days), §6.1 (7 days), §6.4 (staging
run), §6.5 (Bots never handle user media) and §9.9 (local cache) are reflected. Storage paths match migration
`20260926120000_m1_environments_staging.sql` (private `environments` bucket, `{user_id}/…`, no anon read).
The references in `legal/BIPA_CONSENT.md` and the platform handbook were updated.

Counsel items (listed in both files): consent-record period, raw telemetry TTL (proposal 90 days), receipt
period (proposal 3 years), the Supabase backup window, confirming the 24 h / 7-day promise, and legal-hold
wording.

Verdict: **PASS**. BACKLOG: Privacy Policy v0.2 for v1; delete-all build + staging test (no ticket yet).
