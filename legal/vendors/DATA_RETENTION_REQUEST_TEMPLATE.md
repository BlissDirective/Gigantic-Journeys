# Vendor data-retention & training request — template

**Purpose.** Send this to each data processor **before it touches user data** to collect the answers required by `governance/SECURITY_CHECKLIST.md §6.3` and to decide whether the vendor is usable (a vendor that trains on customer data by default is not used without an opt-out in place). Answers are filed under `legal/vendors/<vendor>.md`. Supports tickets **M0-LEGAL-03** (Luma) and **M0-LEGAL-04** (Meshy, Tripo).

Send from **[a project role address, e.g. legal@giganticjourneys.com]**, not a personal account. Do not include any secret, key, or real user data in the message.

---

**Subject:** Data processing, retention, and training terms — Gigantic Journeys (SparkForge Labs)

Hello [Vendor] team,

We are evaluating [Product/API] to process user-generated content in our iOS app **Gigantic Journeys**. Before sending any user data we need written answers to the following. A link to your DPA, sub-processor list, and retention policy is welcome in place of any answer already documented there.

1. **Retention.** How long do you retain (a) inputs we send (images/video/3D data) and (b) outputs you generate? Can we configure immediate deletion after a job completes, or delete via API? What is the guaranteed deletion timeline?
2. **Training.** Do you use customer inputs or outputs to train or improve your models **by default**? Is there an **opt-out** (or opt-in) and how is it enabled for our account? Please confirm in writing if opting out is available.
3. **Deletion.** Do you provide programmatic deletion and a deletion confirmation/receipt? How is deletion propagated to backups, and within what window?
4. **Sub-processors.** Who are your sub-processors and in what regions is data processed/stored?
5. **Security.** Encryption in transit and at rest; access controls; most recent security attestation (SOC 2 / ISO 27001) if any.
6. **DPA.** Can you sign a Data Processing Agreement? Please share your standard DPA. (See our required terms in `DPA_CHECKLIST.md`.)
7. **Biometric-specific** *(avatar vendors — Meshy/Tripo only)*: Do you treat face/body imagery as biometric data? Do you support **no-retention / immediate-delete** for such inputs? Are there jurisdictions where you cannot offer this?
8. **Incident handling.** Your breach-notification commitment and timeline.

We plan to send **no location metadata** (stripped on device) and, for avatar generation, to require **immediate deletion of source photos after the job**. Please flag anything about our intended use that your terms would not permit.

Thank you,
[Name / role], SparkForge Labs — Gigantic Journeys

---

## Filing the answers

Create `legal/vendors/<vendor>.md` with:

```
# <Vendor> — data terms on file
Date collected: <date>   Collected by: <name/agent>
Links: DPA <url> · Retention policy <url> · Sub-processors <url>

Retention (input/output): ...
Trains on customer data by default? yes/no   Opt-out available? yes/no   Enabled for us? yes/no
Programmatic deletion + receipt? ...
Sub-processors / regions: ...
Security attestations: ...
Biometric immediate-delete supported? (avatar vendors) ...
Incident/breach notification: ...

Decision: USABLE / USABLE WITH CONDITIONS / NOT USABLE — <one-line reason>
Gate: SECURITY_CHECKLIST §6.3 (M1 for Luma, M2 for the head vendor)
```
