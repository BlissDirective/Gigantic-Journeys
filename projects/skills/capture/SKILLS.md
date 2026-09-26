# gj-capture — Working Handbook

Remit: in-app guided capture (room walkthrough and tabletop orbital), the pre-upload quality gate, the capture→reconstruction upload contract, the self-hosted reconstruction pipeline (scan → Gaussian splat + collision mesh), splat renderer integration in Unity, and the test corpus. Re-read this file at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3, §9).

Executing agent (AGENT_GOVERNANCE §8): the **Builder** owns the pipeline, tools and app code. The **Operator** owns in-Editor scan import, capture-dashboard work, and babysitting reconstruction jobs (for example Modal runs, per `services/reconstruction/OPERATOR_RUNBOOK.md`). Owned paths (kit §3.1): `unity/Assets/Capture`, `services/reconstruction`, and the corpus (Owner supplies raw video).

Research list: `projects/skills/capture/RESOURCES.md`.

## 1. Rules this hat must follow

| Rule | Source |
|---|---|
| Session start, branches, PR template, evidence standard | `agents/grok/README.md` §3–§5 |
| AUTH before spend (GPU rental, vendors), accounts, schema or design changes | `agents/grok/README.md` §6 |
| Review rows, esp. C5 (EXIF/GPS), C7 (deletion path), C8 (pins), D3 (<90 s scan), D4 (per-scan cost), D6 (package size) | `governance/REVIEW_RUBRIC.md` |
| GPS/EXIF stripping on device and server | `governance/SECURITY_CHECKLIST.md` §4 |
| Signed URLs ≤ 15 min for splats and meshes | `governance/SECURITY_CHECKLIST.md` §3 |
| Raw media deleted once derived assets exist; bridge conditional; Bots never touch real user media | `governance/SECURITY_CHECKLIST.md` §6.1, §6.3, §6.5 |
| Exact pins, commercial-safe licences (no INRIA 3DGS/SuGaR), $50/day cap | `governance/SECURITY_CHECKLIST.md` §7, §8.5 |
| Capture UX rules 12–14 (coach four quality factors, two scripts, reject early and kindly); rule 10 (permissions in context); rule 11 (waits) | Design Skills §3.4–§3.5 |
| Pre-PR design checklist for capture UI | Design Skills §4 |
| Locked coaching UI + the AUTH #025 readiness/multi-pass extension | `design/DESIGN_SYSTEM.md` decision 6; decision 7 (create waits); decision 10 (Reduce Motion) |
| Scale examples (Lego stud 0.055A, furniture 3–5A) that decide what capture must resolve | Movement Bible §1 |
| Capture system, upload contract, privacy posture | `SPEC.md` §3.1, §3.9, §7 |
| Reconstruction architecture | `ADRs/0005-reconstruction-selfhost-and-avatar-onprem.md` (addenda 3–4; AUTH #030, #032) |

## 2. Capture coaching patterns

The flow and state machine come from SPEC §3.1 and `design/proposals/capture-ux-coaching-v1.md` §1: Scan → in-context camera pre-prompt → illustrated mode toggle → framing/relocalize → coached capture → missed-corner check → quality gate → 5 s preview with Retake → on-device strip + bundle → upload → create waiting state (decision 7).

- **Coach one cue at a time**, and only when the capture needs it. Go quiet when the user is doing well (proposal §2).
- **Room walkthrough:** start in a doorway or corner, arc at chest height, sweep back for overlap, and add a low and a high pass where there is verticality. **Tabletop orbital:** keep the build centered, then do one slow circle low and one high. "Keep the build centered" is the tabletop-specific nudge.
- **Use only the locked widgets** (decision 6): teal coverage wash + coverage ring, speed arc that turns amber with one haptic, a blur tick + amber edge pulse with no words, one low-light card, the missed-corner 3D arrow, the 90 s ring (a target, not a limit; amber past 3 min), Done at 60 % coverage or 60 s, and the 72 pt record button. **Never text-only instructions** (Design Skills §4; REVIEW_RUBRIC G5).
- **Never hard-stop.** "Upload anyway" and "Continue anyway" are always available (decision 6, SPEC §3.1).
- **First run:** one richer coach-through after the play-first demo, never repeated (SPEC §3.1, Design Skills rule 9).
- **People in frame:** coach "scan spaces, not people". There is no on-device person detection in v1 (SPEC §3.9, AUTH #025).
- **Failure paths:** tracking loss → "point at a spot you've already scanned" → relocalize, keeping coverage. Interruption → Resume or Start over. Downstream failure → a kind, free retry that keeps the mode (M1-CAPT-01 AT-6).

## 3. Quality gating (reconstruction-readiness)

- **Signals** (SPEC §3.1, M1-CAPT-04): coverage fraction, overlap/parallax (the signal users never think about, and the one most tied to splat quality), blur ratio, light (median luma or ARKit light estimate), ARKit tracking continuity, and duration/pace.
- **Posture:** the score recommends "add a quick pass over here" at the weakest region. Appended passes merge into the **same** upload bundle (M1-CAPT-04 AT-2). The score must be **predictive**: on the corpus, a higher score must mean fewer reconstruction failures (M1-CAPT-04 AT-1). Validate that before tuning the UI.
- **Thresholds are TBD.** No numeric score cut-offs are decided yet; they come from corpus runs (M1-CAPT-04, corpus from M0-OWNER-01). Do not hard-code guesses. Put them in one config and log them with each upload.
- **Log failures with their cause.** Every failed reconstruction logs the readiness score and coverage map (M1-CAPT-02 AT-5).

## 4. Upload pipeline (capture → reconstruction contract)

- **Bundle** (SPEC §3.1, proposal §4, M1-CAPT-01 AT-1): compressed video + frame timestamps, per-frame ARKit poses, camera intrinsics, optional LiDAR depth, gravity/up vector and metric scale, mode, device, duration, readiness score and coverage map. It has **the same shape as the corpus manifest** (M0-CAPT-01 AT-2), so corpus and live scans are interchangeable.
- **Strip before it leaves the device.** Remove GPS, EXIF, XMP and MP4/MOV location atoms, then re-verify and strip again server-side. Reject and count any upload still carrying location (SECURITY_CHECKLIST §4.1–4.2). The server tool is `services/reconstruction/tools/strip_metadata.py` (M0-CAPT-01 AT-3; not yet written, ticket open).
- **Pipeline** (`services/reconstruction/README.md`): ScanInput → SfM (COLMAP; GLOMAP selectable) → train (gsplat/Splatfacto, MCMC fixed budget; Brush pluggable) → compress (`@playcanvas/splat-transform` → `.spz`/`.sog`) → mesh (Open3D Poisson) → EnvironmentPackage. Two gates run before any GPU work: the **licence gate** (`licenses.assert_commercial_safe`) and the **spend cap** (`cost.CostLedger.guard`: $50/day plus the AUTH #031 $100 spike cap).
- **Measured so far** (one public Mip-NeRF 360 `room`, 311 images, Modal A10G; `research/vendors/reconstruction-spike-report.md` §2): the default is GPU COLMAP (GPU SIFT + GPU exhaustive match + **incremental** mapper), which beat GLOMAP on time and cost at equal quality. SfM took 3.0 min, the pipeline 9.7 min, and the full cost was about $0.26 per room (GPU + CPU + memory), with 311/311 registered and held-out PSNR 31.3 dB. **Corpus-room numbers are TBD** (M1-CAPT-03 step 5; needs M0-OWNER-01).
- **Orchestration:** Inngest durable steps submit, poll, store and track cost per job, and halt at the daily cap (M1-CAPT-02 AT-2, `api/`). Steps must be idempotent (REVIEW_RUBRIC E3).
- **Storage and delivery:** outputs go to staging storage behind signed, short-lived URLs (M1-CAPT-02 AT-1). Zero-egress storage (R2/B2) is the cost analysis's recommendation, not a decision. Adopting it is an AUTH (account/spend). **TBD:** M4-PLAT-01 / ADR.
- **Package budget:** ≤ 150 MB *(initial)* (SPEC §6). Record `package_bytes` in `cost.json` for every run (REVIEW_RUBRIC D6).

## 5. Splat renderer integration (Unity / iOS)

- **Baseline:** aras-p/UnityGaussianSplatting (MIT), pinned by commit in `Packages/manifest.json`, via `GaussianSplatURPFeature` (render graph, Compatibility Mode off) (M0-UNITY-02 AT-1, M1-UNITY-01 AT-1). The package choice becomes an ADR-0001 addendum by AUTH (M0-UNITY-02 AT-4).
- **The #1 program risk is the Metal depth sort.** The aras-p radix sort glitches on Metal (issue #226). Try Option A first: a tile-local bitonic sort (msplat technique). Option B is a native Metal plugin wrapping MetalSplatter. Option C (narrower keys + splat budget) only multiplies A or B (`design/proposals/ios-splat-render-v1.md`). "Solved" means correct depth order on a physical iPhone (M1-UNITY-01 AT-2).
- **Budget:** about 1–2.5M splats per room via gsplat MCMC; ship SOG (~20×) or SPZ (~10×) (cost analysis Part 3). aras-p has **no LOD**, so specify our own LOD/chunked streaming (M1-UNITY-01 AT-4).
- **Tuning knobs** (LOD/culling) live in one ScriptableObject for gj-gameplay (M0-UNITY-02 AT-5).
- **Load only through signed URLs**, never a direct storage URL (M1-UNITY-01 AT-5, SECURITY_CHECKLIST §3.1–3.3).
- Quality tiers (splat LOD, culling, resolution scale) scale older iPhones toward 30 fps. Measurements are suggested evidence, never a gate (SPEC §6, §11).

## 6. Corpus handling

- The corpus is **Owner-supplied and consented**: 10 rooms + 5 tabletops on day one (M0-OWNER-01). SPEC §5 references 30 rooms / 20 tabletops for Tier 2 metrics. Bots never handle real user media (SECURITY_CHECKLIST §6.5).
- **Raw media never enters git.** CI repo hygiene enforces this, and the rule is restated in `services/reconstruction/README.md`. Corpus lives on the VM path now and in the staging bucket once Supabase is live (M0-CAPT-01 AT-1).
- Use a **public dataset first** (Mip-NeRF 360 in `data/mipnerf360/`, `services/reconstruction/DATASETS.md`) for any new pipeline change. Move to corpus only after the public run is clean (`OPERATOR_RUNBOOK.md` Steps 4–5).
- The **manifest** records id, mode, lighting, duration, device, object classes (Bible §1 examples), and readiness + coverage (M0-CAPT-01 AT-2).
- A managed bridge (KIRI/APS) may touch **only** the corpus, and only with written no-train + DPA + residency terms on file (SECURITY_CHECKLIST §6.3, AUTH #030). Luma is rejected (ADR-0005). M0-LEGAL-03 (Luma terms) predates that decision; flag it to the Coordinator rather than working it.

## 7. Mistakes to avoid

- **Treating GLOMAP as automatically faster.** On the spike room, incremental GPU COLMAP was faster and cheaper (spike report). Benchmark before you switch.
- **Pricing only GPU time.** CPU cores and memory nearly doubled the real Modal bill on the first run. Use the full `cost.json` meter.
- Putting heavy CUDA deps in a CI-installed requirements file. Keep them in the Dockerfile; the `reconstruction` package stays stdlib-only so CI runs it with fakes.
- Low-texture walls and reflective surfaces break SfM. Coach for coverage and log the failure with its readiness score; don't silently retry.
- Stripping metadata only on the server, or only for JPEG. All four formats (JPEG, HEIC, MP4, MOV) must be stripped on device **and** on the server.
- Adding a new capture widget or failure screen. That changes locked decision 6 and needs an AUTH.
- Assuming "renders in the Editor" means "renders on iPhone" (issue #226).
- Exporting all `.env.local` into a Modal shell. The runbook exports only the two Modal values.

## 8. Checklists

**Pre-PR (capture or pipeline):**
- [ ] Ticket ATs mapped to evidence (CI job, file, `qa/reports/…`) (REVIEW_RUBRIC A1).
- [ ] GPS/EXIF/XMP/location atoms are stripped on device, re-verified on the server, and fixture tests cover four formats (suggested, SECURITY_CHECKLIST §4.3).
- [ ] Deletion path exists for every new media input (C7, SECURITY_CHECKLIST §6.1).
- [ ] New deps are pinned `==` with a one-line licence justification (MIT/BSD/Apache only) and pass `pip-audit` / `npm audit` (C8, SECURITY_CHECKLIST §7).
- [ ] Per-scan cost and wall-clock are reported for any pipeline change; the daily cap is untouched or improved (D4).
- [ ] `package_bytes` is recorded against ≤ 150 MB (D6).
- [ ] No backend, GPU or storage credential appears in the repo, logs or `cost.json` (M1-CAPT-02 AT-4).
- [ ] Capture UI: Design Skills §4 checklist, decision 6 widgets only, Reduce Motion equivalents, 56 pt+ controls, screenshots in `qa/evidence/<ticket>/`.
- [ ] No raw media, corpus frames, or faces in commits or screenshots.

**Pre-upload (runtime gate):** coverage · overlap/parallax · blur ratio · light · tracking continuity · location metadata stripped · bundle fields complete · size within limits.

## 9. Pointers

`services/reconstruction/{README,OPERATOR_RUNBOOK,DATASETS}.md` · `research/vendors/reconstruction-{cost-and-trainer-analysis,spike-report,selfhost,alternatives}.md` · `design/proposals/{capture-ux-coaching-v1,ios-splat-render-v1}.md` · `ADRs/0005-*` · tickets M0-CAPT-01, M0-UNITY-02, M1-CAPT-01..04, M1-UNITY-01.

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + curated RESOURCES.md starter set. |
| 2026-09-26 | The spike showed incremental GPU COLMAP beating GLOMAP on the public room ($0.26 vs $0.29, 9.7 vs 10.5 min). Full-cost metering matters. The standalone GLOMAP repo is deprecated and lives on as `colmap global_mapper`. Readiness thresholds are still undecided. | gj-operator expanded RESOURCES.md to 106 link-checked entries and rewrote SKILLS.md around coaching, gating, the upload contract, the renderer and the corpus (M0-SKILL-02). Replaced the outdated "GLOMAP is ~3.5× faster" advice. |
