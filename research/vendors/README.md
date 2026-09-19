# `research/vendors/`

Vendor research + **build-vs-buy** analysis (Coordinator research pass, observed 2026-09-17). Decision-support, not decisions — all facts carry an observation date and sources; re-verify pricing/terms at build time. Vendor **data terms on file** live in `legal/vendors/`. Changing SPEC/ADR-0002 is AUTH-gated — nothing here changes them.

## The throughline
Both hard problems (reconstruction, avatar) come down to the same thing that bit us with Luma and Meshy: **vendor lock-in/deprecation, and vendors training on our users' biometric/home data.** The fix in both cases is **keep user data on infrastructure we control** — by self-hosting (reconstruction, feasible now) or by using a vendor's **on-prem** mode (avatar). That directly answers "could we build custom?": **reconstruction — yes, build; avatar — use a vendor's on-prem for v1, build only in V2.**

## Reconstruction (scan → splat/mesh) — build-vs-buy

| Path | Option | Verdict |
|---|---|---|
| **Build** | Self-host gsplat/Brush + COLMAP/GLOMAP + Open3D (or Epic RealityScan for mesh) | **Feasible-with-effort, legally clean, <$1/scan, full data control + no lock-in.** Main risk: iOS-in-Unity splat rendering + prod reliability. |
| **Buy** | **KIRI Engine API** (splat+mesh, ~$1/scan) | Turnkey and best output fit, **but weak data terms** (HK entity, silent on training, no DPA) → only with a written no-train + DPA. |
| **Buy** | **Autodesk APS Reality Capture** (mesh-only) | Clean managed **DPA** + delete; but mesh-only, photos-only, likely >10-min rooms. |
| **Buy** | Polycam / Niantic / Matterport | Don't fit a "server reconstruction API" need. |

**Recommendation:** the private-home data + the Luma lock-in lesson make **self-hosting the stronger strategic direction** — but **de-risk it with a 1–2 week spike** first (capture a room → gsplat/Brush → prune → render on a physical iPhone in Unity 6 URP; the iOS Metal splat sort is the real unknown). If early M1 validation needs a bridge, use **Autodesk APS** (has a real DPA) or **KIRI only with written no-train+DPA**. Details: `reconstruction-selfhost.md`, `reconstruction-alternatives.md`.

## Avatar (photo → recognizable head) — build-vs-buy

| Path | Option | Verdict |
|---|---|---|
| **Buy (on-prem)** | **Avatar SDK / MetaPerson (itSeez3D)** — Enterprise "Local Compute" | **#1.** Recognizable head+body, native **Unity + iOS SDKs**, EULA **already permits consented person-photos**, and **on-prem keeps biometric data on our infra** — the privacy win of self-hosting without the ML/licensing lift. |
| **Buy** | **Meshcapade** | Runner-up: **cleanest published terms** (train opt-in, not default), but body-first, weak face likeness, no turnkey Unity plugin. |
| **Buy** | **Meshy** (current pick) | Usable for face data **only** via a negotiated Enterprise agreement + DPA + a **PII carve-out** (its ToS bans identifiable-person photos) — the hardest path of the three. |
| **Buy** | Didimo | **Disqualified as written** (trains on biometric inputs, "no consent required"; won't guarantee deletion). |
| **Build** | Self-host (FLAME-2023-Open/ICT-FaceKit + own regressor) | **Not for v1** — the good models are non-commercially licensed; you'd trade a vendor-ToS problem for an IP-license one + an ML-quality risk. **V2 investment.** |

**Recommendation:** do **not** self-host avatars for v1. The best v1 path is **Avatar SDK / MetaPerson on the Enterprise on-prem plan** — it delivers recognizability + Unity/iOS fit + biometric data on our own infra. **This likely beats Meshy for our biometric use** (Meshy needs a negotiated carve-out just to allow face photos at all). Meshy remains your selected vendor unless you choose to switch — but the research makes a strong case to **reconsider Meshy vs Avatar SDK/MetaPerson** before M2. Details: `avatar-alternatives.md`, `avatar-selfhost.md`.

## Index
| File | Topic |
|---|---|
| `reconstruction-alternatives.md` | reconstruction API/cloud options (buy) |
| `reconstruction-selfhost.md` | self-host reconstruction feasibility (build) |
| `avatar-alternatives.md` | avatar API/SDK options with biometric-permissive terms (buy) |
| `avatar-selfhost.md` | self-host avatar feasibility (build) |
| `meshy.md` | Meshy dossier (current head-vendor pick) |
| `luma.md` | Luma dossier (reconstruction assumption at risk) |
| `iap-revenuecat-vs-unity.md` | IAP (M5 ADR) |
| `crash-reporting.md` | crash reporting (#017) |
| `character-roster-sourcing.md` | v1 character roster: license/commission vs open-base authoring (dual-track) |

## Decisions made
1. **Reconstruction backend (ADR-0005 / AUTH #018):** **self-host + managed bridge.** Self-host (gsplat/Brush + COLMAP + Open3D) is the target, de-risked by the **M1-CAPT-03 spike**; the bridge is **KIRI, corpus-only** (splat+mesh matches the target; only ever processes the consented corpus, never real user homes). **Luma dropped.**
2. **v1 avatar (ADR-0006 / AUTH #020 — supersedes the head-vendor decision):** **pre-made curated character roster, no biometric, no avatar vendor in v1.** The avatar-vendor work here (Avatar SDK/MetaPerson #1) and the self-host avatar analysis move to the **V2 custom-avatar R&D track** (`research/rnd/`). Meshy/Tripo/Avatar SDK all deferred/dropped for v1.

`meshy.md`, `luma.md`, and `avatar-alternatives.md`/`avatar-selfhost.md` are retained as the analysis behind the V2 track and the superseded ADRs.

## Standing caveats
- All vendor data terms here are from **public pages** — confirm directly (send `legal/vendors/DATA_RETENTION_REQUEST_TEMPLATE.md`) before any real user data flows (SECURITY_CHECKLIST §6.3).
- **iOS-in-Unity splat rendering** (~200–500K splats @30 fps) is the shared risk on any splat path; ship compressed splats and/or the mesh for gameplay/collision.
