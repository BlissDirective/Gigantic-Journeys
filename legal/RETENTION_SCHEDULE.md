# Retention Schedule & Deletion Flow (DRAFT)

**Status: DRAFT v0.1 · 2026-09-17 · satisfies ticket M0-LEGAL-02 (draft).** The authoritative, publishable retention & destruction schedule and the deletion-flow specification, operationalizing `SPEC.md §7` and `governance/SECURITY_CHECKLIST.md §5–§6`. **Not legal advice;** counsel reviews before M5 (`SPEC §7`, §9.6). This document is written to be **published** (BIPA §15(a) requires a public retention/destruction schedule).

---

## 1. Retention schedule (the published table)

| Data class | Retention rule | Destruction trigger | Mechanism / evidence |
|---|---|---|---|
| **Face & body photos (biometric)** | Kept only for the duration of the avatar-generation job | Avatar generated (or job fails) | Deleted **immediately** on device, in storage, and at the vendor; **deletion receipt** logged (job id, timestamp, vendor response — no media). `SECURITY_CHECKLIST §6.2` |
| Raw scan video, poses, depth | Until derived assets exist; **failed jobs ≤ 7 days** | Derived assets created, or 7-day failure timeout | Automatic storage lifecycle job; per-user delete-all. `§6.1` |
| Derived environment assets (splat, mesh, graph, spec, thumbnail) | While the user keeps the environment; published copies while published | User deletes/unpublishes, or account delete-all | Unpublish removes from feeds immediately; delete-all purges. `§6` |
| Avatar assets (head mesh, textures, body params) | While the account exists | Account delete-all, or consent withdrawal | Per-user delete-all; withdrawal deletes avatar. |
| **Consent records** | As long as legally required, then destroyed | Statutory retention period elapses | Retained without media; destroyed on schedule (counsel sets the period — see §4). |
| Telemetry events (pseudonymous; no GPS/PII/media) | Raw events **[N days — counsel/Owner set, e.g. 90]**; aggregates retained | Raw-event TTL; delete-all | Scheduled purge of raw events; delete-all clears user-linked events. |
| Correction events (training opt-in) | Derived data only, while opt-in stands | Opt-out (future use), delete-all (past) | Opt-out flag; delete-all removes contributions. |
| Ratings, reports, leaderboard times | While the environment/account exists | Environment deleted or account delete-all | Cascade delete with the environment/account. |

**Location data:** never retained — GPS/EXIF is stripped on device and again server-side before storage (`§4`); any upload still carrying location is rejected.

## 2. The deletion flow ("Delete my data")

One tap in **Settings → Delete my data**. Completes within **30 days** including vendor-side deletion (`§5.4`). Steps:

1. **Confirm** with a clear, non-dark-pattern dialog (what will be deleted; that it is irreversible).
2. **Revoke & stop** new processing immediately (auth session, pending jobs cancelled).
3. **Delete derived + account data**: environments (and published copies/feeds), avatar assets, ratings/reports/leaderboard entries, user-linked telemetry and correction contributions.
4. **Vendor-side deletion**: issue delete calls to each processor holding user data; record receipts (no media).
5. **Source media**: raw scan media purged; biometric photos are already gone (deleted at generation).
6. **Consent records**: retained only as long as legally required as proof, then destroyed per §4; a deletion audit entry (no media) records completion.
7. **Confirm to the user** in-app/by email that deletion completed.

Failed jobs' media is deleted within 7 days regardless of user action (`§6.1`).

## 3. Deletion evidence (what we keep, safely)

We keep **receipts and audit entries that contain no media and no biometric data**: `{ user_id, data_class, action, vendor, timestamp, vendor_response }`. This proves deletion happened without re-collecting what we deleted.

## 4. Open items for counsel (before M5)

- **Consent-record retention period** — how long to keep proof-of-consent after account deletion (balance BIPA proof-of-compliance vs. minimization). Set the number here.
- **Raw telemetry TTL** — set `N` days in §1.
- **Statutory destruction ceilings** — confirm the immediate-after-generation biometric timeline and the derived-data timelines satisfy BIPA (≤ 3 yrs since last interaction), CUBI (≤ 1 yr after purpose), and any MHMDA/CCPA/GDPR duties in scope.
- **Backup handling** — define how deletion propagates to encrypted backups (e.g., backup rotation window) so "deleted" is true within a stated period.
- **Publication** — confirm this schedule (minus the counsel-notes section) is the version published at `[link]` and referenced from the consent sheet and Privacy Policy.

---

*This schedule is designed to be published verbatim (drop §4). It is the "written retention and destruction schedule" the consent flow (`legal/BIPA_CONSENT.md`) and Privacy Policy point to.*
