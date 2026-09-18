# Avatar — API/SDK alternatives to Meshy (buy side)

**Decision-support · observed 2026-09-17 · Coordinator research pass.** Vendors that take person photos via API/SDK and produce a *recognizable* 3D head, with terms that permit identifiable-person (biometric) input. Sourced; legal quotes fetched 2026-09-17 — treat every "must confirm" as a hard gate before contracting. Not legal advice.

## Bottom line
The live field is smaller than it looks: **Ready Player Me is shut down** (acquired by Netflix; avatar creator + public APIs offline 31 Jan 2026 — independently confirmed) and was stylized anyway; **Union Avatars reported offline** (competitor-sourced — verify directly). Of vendors that are alive, take person photos, and make a recognizable head:

- **#1 — Avatar SDK / MetaPerson (itSeez3D):** best balance of recognizable head+body, native Unity + iOS SDKs, and a real compliance path via **Enterprise on-prem "Local Compute."** Its default **Cloud API trains on inputs**, so the recommendation is specifically the on-prem or written no-train path.
- **Runner-up — Meshcapade:** the **cleanest published biometric terms** (training opt-in, not default), but a **body specialist with weaker face likeness** and no turnkey Unity plugin.

## Comparison
| Vendor | Recognizable head? | Unity 6 / iOS | Gen time | Biometric terms | Verdict |
|---|---|---|---|---|---|
| **Avatar SDK / MetaPerson** (itSeez3D) | **High** — parametric face fitted to selfie, tuned for recognizability (focus-group + face-recognition tested) | **Native SDKs** (Unity, iOS, …); Cloud API + **on-prem Local Compute** (Enterprise) | **<40–60s** | Photos **YES with consent** (EULA §6.3). Train-by-default: **Cloud YES**, but **on-prem avoids it**; deletion/DPA **must confirm** | **#1** — recognizable + best engine fit + real compliance path |
| **Meshcapade** | Body excellent (SMPL); **face/head weaker**, parametric not identity-faithful | REST API + FBX/GLB; community C# SDK; no official Unity plugin | "seconds"–several min (mixed) | Photos **YES (Art. 9 consent)**; **train opt-in only (not default)**; Art. 17 erasure; Art. 28 DPAs | **Runner-up** — best terms + body; head likeness/speed/Unity are the risks |
| **Didimo** (Popul8) | High (photoreal) | Unity + Unreal SDK | ~minutes | **Trains on inputs for "scientific research … no consent required"; "not legally required to delete"** | **Disqualified as written** — this is the Meshy problem; only if an Enterprise contract strikes the ML carve-out (confirm) |
| **Avaturn** | Stylized/semi-real — misses photoreal head | Unity/Unreal, WebGL, iOS | fast | Thin 2021 policy; unclear — confirm | Not for a recognizable photoreal head |
| **in3D** | Realistic, but **phone SCAN (LiDAR/video), not photos** | Unity importer, iOS | ~minutes | Thin policy; confirm | Partial fit only if scan input acceptable |
| **Reallusion Headshot 3 / CC5** | High, likeness-preserving | Exports to Unity; **desktop plugin, not a runtime API** | manual | **Processes locally** (biometric photos never leave the machine) | Good **offline pipeline** for pre-authored avatars, not in-app runtime |
| **Ready Player Me** | Stylized | — | — | **APIs shut down 31 Jan 2026** | **Dead — out** |
| **Union Avatars** | Semi-real | Unity/Unreal | — | **Reported offline (verify)** | Out |
| Pinscreen / Luxand | Photoreal / moderate | SDK advertised | seconds | Availability + biometric terms unverified | Minor; confirm |

## #1 — Avatar SDK / MetaPerson (itSeez3D)
Engineered for recognizability (their framing: "recognizable over realistic," validated with focus groups + facial-recognition), rigged head+body in **<1 min**, first-class **Unity + iOS SDKs** (strongest engine fit now RPM is gone). EULA **explicitly contemplates consented identifiable-person photos** (§6.3) and bans training on *their outputs* (§3.2). Gap: the **Cloud** privacy policy trains on input images by default. Fix: **Enterprise "Local Compute" (on-prem)** so biometric photos process on infrastructure we control and never enter a training cloud — a path Meshy does not offer. This is the **hybrid sweet spot: vendor tech + our-infra data control.**

**Confirm in writing before committing:** (1) Enterprise + on-prem Local Compute **or** a written no-train Cloud clause; (2) source-photo deletion timing + confirmation; (3) a signed **DPA naming itSeez3D as Processor** with biometric-aware language; (4) Unity **6** support + iOS runtime specifics.

## Runner-up — Meshcapade
Take it if compliance certainty outranks head fidelity, or for accurate **body** parameters (best in field). Cleanest published stance: Art. 9 consent-gated, **training opt-in/revocable (not default)**, erasure honored, Art. 28 DPAs. **Confirm:** (1) a B2B/API contract with Meshcapade as **Processor + signed DPA** (its public policy governs its own consumer service as Controller — different posture); (2) the commercial API keeps the no-train default; (3) **single-image face recognizability vs the 60% blind-test bar** (real risk — body-first); (4) generation time (<2 min?) and official Unity support.

## Avoid / conditional
- **Didimo** — trains on biometric inputs for "scientific research … no consent required" and is "not legally required to delete" it: functionally the Meshy blocker. Reconsider only if an Enterprise contract removes the carve-out; don't assume it will.
- **Avaturn** (stylized), **in3D** (scan not photo), **RPM/Union** (offline), **Reallusion Headshot** (offline pipeline, not runtime).

## Cross-cutting compliance
All inputs are biometric under IL BIPA / TX CUBI / WA MHMDA. **No vendor's public docs name BIPA/CUBI** (they lean on GDPR Art. 9 / CCPA). Regardless of vendor we still need our own in-app **written consent + published retention/deletion schedule**, and the vendor contractually as a **Processor on our instructions (or on-prem)** so we remain the controller. Verify the DPA covers biometric identifiers and immediate post-job deletion with confirmation.

## Sources (observed 2026-09-17)
- Avatar SDK EULA — https://avatarsdk.com/eula/ · Privacy — https://avatarsdk.com/privacy-policy/ · Unity/Local Compute — https://docs.metaperson.avatarsdk.com/business-integration/unity/metaperson_creator_unity_project/ · recognizability — https://avatarsdk.com/blog/2026/08/03/why-we-chose-recognizable-over-realistic/
- Meshcapade Privacy — https://meshcapade.com/privacy-policy · from-photos — https://me.meshcapade.com/from-photos · C# SDK — https://github.com/tryAGI/Meshcapade
- Didimo Privacy — https://privacy.didimo.co/privacy-policy/ · API Terms/DPA — https://privacy.didimo.co/api-terms-of-use-license-agreement/
- RPM shutdown — https://variety.com/2025/digital/news/netflix-acquires-ready-player-me-games-avatar-creation-1236612915/ · https://techcrunch.com/2025/12/19/netflix-acquires-gaming-avatar-maker-ready-player-me/
- Reallusion Headshot — https://www.reallusion.com/character-creator/headshot/ · in3D — https://in3d.io/docs/privacy-policy · Avaturn — https://avaturn.me/

*Honesty flags: Union Avatars shutdown is competitor-sourced (verify); RPM shutdown independently confirmed. Load-bearing biometric quotes read from vendors' own pages 2026-09-17.*
