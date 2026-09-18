# Avatar SDK / MetaPerson (itSeez3D) — data terms on file

**Date collected:** 2026-09-17 · **Collected by:** Coordinator (from public EULA/Privacy/docs). **Source:** public terms only — **NOT yet vendor-confirmed** via `DATA_RETENTION_REQUEST_TEMPLATE.md`. Selected as the head-generation vendor per **AUTH #019 / ADR-0005** (replaces Meshy). Full analysis: `research/vendors/avatar-alternatives.md`. Ticket: M0-LEGAL-04.

Links: EULA https://avatarsdk.com/eula/ · Privacy https://avatarsdk.com/privacy-policy/ · Unity/Local Compute https://docs.metaperson.avatarsdk.com/business-integration/unity/metaperson_creator_unity_project/

- **Capability:** recognizable head+body from a selfie in <40–60s; native Unity + iOS SDKs; Cloud API + **on-prem "Local Compute" (Enterprise)**. Recognizability is an explicit design goal (focus-group + face-recognition tested). Still subject to our own 60% blind test at M2.
- **Person-photos allowed?** **YES, with consent** — EULA §6.3 contemplates images "of individuals who have … provided their informed consent." (This is the key advantage over Meshy, whose ToS bans identifiable-person inputs.)
- **Trains on customer data by default?** **Cloud: YES** ("for training our computer vision algorithms"). **On-prem Local Compute avoids the training cloud** — the reason we take the Enterprise on-prem path. Bans training on *their* outputs (§3.2).
- **Deletion / retention:** retention "per customer agreement"; deletion timing + confirmation **must confirm** (not in public docs).
- **DPA:** **must confirm** (not public) — require itSeez3D named as **Processor** with biometric-aware language.
- **Region / sub-processors:** confirm for the chosen deployment (on-prem should keep data on our infra).
- **BIPA/CUBI/MHMDA:** not named in public docs (cites GDPR/CCPA) — our own in-app written consent + published retention/deletion schedule still required regardless.

**Decision: SELECTED (AUTH #019) — usable via Enterprise on-prem "Local Compute" (preferred) or a written no-train Cloud clause.** On-prem keeps biometric face data on infrastructure we control (cleanest BIPA posture). Do not use the default Cloud tier for real user faces without a written no-train clause.

**Confirm in writing before M2:** (1) Enterprise + on-prem Local Compute, or a written no-train Cloud clause; (2) source-photo deletion timing + confirmation; (3) a signed **DPA** (itSeez3D = Processor, biometric-aware); (4) Unity **6** support + iOS runtime specifics; (5) pricing for the on-prem/Enterprise plan.

**Gate:** SECURITY_CHECKLIST §6.3 (before any face processing, M2). Owner/legal-team action: pursue the Enterprise on-prem agreement + DPA.
