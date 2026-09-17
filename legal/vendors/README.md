# `legal/vendors/`

Vendor data-processing terms, on file **before** a vendor touches user data (`governance/SECURITY_CHECKLIST.md §6.3`; SPEC §3.9).

## Process
1. Send each vendor the questions in `DATA_RETENTION_REQUEST_TEMPLATE.md` (from a project role address; no secrets, no user data).
2. Review their DPA against `DPA_CHECKLIST.md`.
3. File answers + decision as `legal/vendors/<vendor>.md`.

## Vendors and gates
| Vendor | Role | Ticket | Gate |
|---|---|---|---|
| **Luma** | scan → 3D reconstruction | M0-LEGAL-03 | before any real user scan (M1) — `SECURITY_CHECKLIST §6.3` |
| **Meshy** | avatar head generation (candidate) | M0-LEGAL-04 | before any face processing (M2) |
| **Tripo** | avatar head generation (candidate) | M0-LEGAL-04 | before any face processing (M2) |
| **Supabase** | auth/db/storage | (accounts track) | before production user data |

The head-vendor comparison (M0-LEGAL-04) recommends Meshy **or** Tripo for M2; the other is dropped. A vendor that trains on customer data by default is not used without an opt-out in place.

## Status
_None on file yet — collected in M0. Owner: gj-capture (Luma), gj-avatar (Meshy/Tripo)._
