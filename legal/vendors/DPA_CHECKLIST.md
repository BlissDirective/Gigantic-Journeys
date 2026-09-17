# Vendor DPA checklist

**Purpose.** The minimum terms a processor's Data Processing Agreement must contain before it touches Gigantic Journeys user data (`governance/SECURITY_CHECKLIST.md §6.3`; SPEC §3.9). Use this to review each vendor's DPA. A vendor missing a **must** is "not usable" until resolved. **Not legal advice** — counsel confirms the DPAs before M5.

Check each vendor (Luma, the head vendor Meshy/Tripo, Supabase) against this list; record the result in `legal/vendors/<vendor>.md`.

## Must have (blocking)
- ☐ **Processor role**: vendor acts as a processor/sub-processor on our documented instructions only.
- ☐ **Purpose limitation**: data used solely to provide the service to us — **no independent use**.
- ☐ **No training by default**: vendor does **not** train/improve its models on our inputs/outputs, or a working **opt-out is enabled for our account** in writing.
- ☐ **Retention + deletion**: defined retention; deletion on our instruction and on contract end; deletion timeline including backups; **deletion confirmation** available.
- ☐ **Confidentiality**: personnel bound to confidentiality.
- ☐ **Security**: appropriate technical/organizational measures (encryption in transit + at rest; access control).
- ☐ **Sub-processors**: list disclosed; notice of changes; equivalent obligations flowed down.
- ☐ **Breach notification**: notify us without undue delay (state the hours/days).
- ☐ **Assistance**: reasonable help with data-subject requests (access, deletion) and with our compliance duties.
- ☐ **International transfers**: lawful transfer mechanism if data leaves its region (e.g., SCCs) — where in scope.
- ☐ **Audit**: right to audit or evidence via attestations (SOC 2 / ISO 27001).

## Must have for biometric processors (Meshy / Tripo — blocking)
- ☐ **Biometric handling acknowledged**: treats face/body imagery as sensitive/biometric.
- ☐ **Immediate deletion**: supports no-retention / delete-immediately-after-job for source photos, with receipt.
- ☐ **No biometric training / disclosure**: never trains on or discloses biometric inputs.

## Should have (note, not blocking)
- ☐ Data residency options; ☐ named DPO/security contact; ☐ liability/indemnity for data incidents; ☐ deletion SLA in hours.

## Decision
Record one of: **USABLE** / **USABLE WITH CONDITIONS** (list them) / **NOT USABLE** (reason), with the date and who reviewed. Counsel confirms before the M5 gate.
