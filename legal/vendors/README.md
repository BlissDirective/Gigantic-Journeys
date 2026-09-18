# `legal/vendors/`

Vendor data-processing terms, on file **before** a vendor touches user data (`governance/SECURITY_CHECKLIST.md §6.3`; SPEC §3.9).

## Process
1. Send each vendor the questions in `DATA_RETENTION_REQUEST_TEMPLATE.md` (from a project role address; no secrets, no user data).
2. Review their DPA against `DPA_CHECKLIST.md`.
3. File answers + decision as `legal/vendors/<vendor>.md`.

## Vendors and gates (current, per ADR-0005 / AUTH #018–#019)
| Vendor | Role | Ticket | Gate |
|---|---|---|---|
| **Avatar SDK / MetaPerson** (itSeez3D) | avatar head generation — **SELECTED** (on-prem "Local Compute"; AUTH #019) | M0-LEGAL-04 | before any face processing (M2) |
| **Self-host** (gsplat/Brush + COLMAP + Open3D) | scan → 3D reconstruction — **target backend** (AUTH #018); data stays on our infra | M1-CAPT-03 | spike, then before real user scans |
| **Autodesk APS** *or* **KIRI** | reconstruction **managed bridge** (only if used for early M1) | M0-LEGAL-03 | before any real user scan — DPA required (`§6.3`) |
| **Supabase** | auth/db/storage | (accounts track) | before production user data |
| ~~Luma~~ | reconstruction — **dropped** (API deprecated; trains by default; AUTH #018) | — | — |
| ~~Meshy / Tripo~~ | avatar — **dropped** (Meshy ToS bans person-photos; AUTH #019) | — | — |

Head vendor is **Avatar SDK/MetaPerson** on-prem (biometric face data on our infra). Reconstruction is **self-hosted** (target), with a **managed bridge** (Autodesk APS with a DPA, or KIRI only under a written no-train + DPA) permitted for early M1 validation. A vendor that trains on customer data by default is not used without a no-train commitment; on-prem/self-host is preferred precisely to avoid that.

## Status
- `avatar-sdk.md` — filed (public terms; on-prem + DPA to confirm).
- Reconstruction bridge terms — collect if/when a bridge is used (`autodesk-aps.md` / `kiri.md`).
- `meshy.md`, `luma.md` — retained as the superseded analysis behind ADR-0005.
