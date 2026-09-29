# `research/tier2/`: Tier 2 research charter

Owner: gj-scenegraph · Charter ticket: M0-SCEN-01 · Charter v1.0, 2026-09-29 (gj-operator, drafted for gj-scenegraph)

Tier 2 research track: true physics on segmented real objects (object–scene decoupling, tet-embedded
Gaussians, XPBD). **Not a v1 feature.** Nothing from this track ships in v1. At the M4 checkpoint the Owner
decides, on R1–R5 evidence, whether it enters v1.1 or V2 or is shelved (SPEC §5).

> **No compute is spent in M0.** This charter is documentation only. Every GPU hour in this track needs an
> approved monthly compute AUTH first (SPEC §5; the template is in §4). The track runs on the Owner-supplied
> consented corpus and the open-licence corpus only, never on user data (SECURITY_CHECKLIST §6.5).

Other files here: `compute-budget-2026-10.md` (the October budget recommendation) and
`gpu-providers-2026-09.md` (provider comparison).

## 1. Goals

1. **Question** (SPEC §5): can physics on segmented real objects run at mobile frame rates and per-scan costs
   that make it a v1.1 or V2 feature?
2. **Pipeline to prove:** reconstructed splat → segment objects → decouple each object from the scene and fill
   the hole → embed the object for simulation (tet cage or particles) → simulate on device → render in the
   Unity test scene on the reference device.
3. **Classes:** at least three, namely cushion (soft volumetric), cloth or curtain (thin shell), and a small
   loose object (rigid: a book, cup or toy).
4. **Fit with v1:** reuse the v1 artefacts (gsplat splat, collision mesh, Bible §4 surface classes from
   M1-SCEN-01/02) and the existing Tier 1 soft reactivity (AUTH #022) as the A/B baseline.

## 2. Success metrics and measurement procedures (SPEC §5, R1–R6)

Every checkpoint report states the measured value against each target. "Corpus" means the Owner corpus once
M0-OWNER-01 delivers it (the 30-room and 20-tabletop targets). Until then, reports use the open-licence
reconstructions in `gj-corpus:/open-video-recon/` (14 usable scenes, `qa/reports/M1-CAPT-03-open-video-recon.md`)
and label the denominator.

| # | Target | Corpus subset | Device | Duration / sample | Testers | Procedure |
|---|---|---|---|---|---|---|
| **R1** Corpus feasibility | ≥ 70 % of rooms, ≥ 80 % of tabletops succeed with no manual fixes, for ≥ 3 classes | All corpus scenes that contain at least one of the three classes (per-class denominators reported) | Rented GPU (A100 80 GB class) | One batch run per checkpoint | 0 (automated) plus 1 reviewer | Run the pipeline headless with fixed configs. A scene passes a class when segmentation IoU ≥ 0.5 against a hand-labelled mask on 3 fixed views **and** the embedding step produces a valid simulation mesh (manifold tets, no inverted elements). Any manual parameter edit counts as a failure. Report the pass % per class and per corpus. |
| **R2** Per-scan preprocessing | ≤ $0.50 and ≤ 10 min wall-clock per scan (target $0.25) | The same R1 batch | Rented GPU; the provider and GPU are named in the report | Every scan in the batch | 0 | Log wall-clock per stage (segment, decouple/fill, embed) and billed seconds × list price. Report the median and p90 per scan; the pass condition is p90 ≤ $0.50 and ≤ 10 min. |
| **R3** Mobile runtime | ≤ 6 ms/frame added at 30 fps with ≥ 5 simulated objects; ≤ 150 MB added memory; no NaN or explosion in 5 min | 3 scenes: a room, a tabletop, and the worst R1-passing scene by object count | **Reference iPhone** (v1 is iOS-only, AUTH #003; SPEC §5 still says "Android", so see §8 Q1) via a TestFlight internal-debug build | 5-minute scripted stress run per scene (the avatar repeatedly lands on, pushes and drags objects) × 3 runs | 0 | Unity Profiler, delta vs the same scene with simulation off: the added CPU+GPU ms/frame median and p95, and added memory from the Memory Profiler. A NaN/explosion watchdog logs any non-finite position or a velocity above 50 A/s. The pass condition is median ≤ 6 ms, p95 ≤ 9 ms reported, memory ≤ 150 MB, 0 watchdog hits. |
| **R4** Plausibility | ≥ 70 % prefer Tier 2 or judge it "more real"; 0 "broken world" incidents per 5-min session | 10 scenes (5 rooms, 5 tabletops) | Reference iPhone | Paired 2-minute clips per scene (Tier 1 vs Tier 2, same inputs, randomised order), plus one free 5-min session per tester | ≥ 12 testers (Owner-recruited internal testers; no payment unless an AUTH exists) | Blind A/B on a form: "Which looks more real?" plus a 5-point realism scale. Incidents (sinking, tearing, jitter at rest, tunnelling) are logged by the tester and verified on the recording. The pass condition is ≥ 70 % Tier 2 preference across all pairs and 0 verified incidents. |
| **R5** Decoupling quality | No visible hole at play-camera distance in ≥ 80 % of cases | 30 object removals/moves sampled across R1-passing scenes | Desktop render of the play camera (Unity, the M1 play-camera rig) | 3 fixed play-camera views per case | 3 raters | Raters mark "hole/artefact visible: yes/no" per view on randomised stills. A case passes when the majority says "no" on all 3 views. Report the % of passing cases and PSNR/LPIPS vs a clean capture where one exists. |
| **R6** Budget discipline | Monthly spend within the approved line; paused within 24 h of the Owner's word | All Tier 2 jobs | Provider billing | Monthly | 0 | Tier 2 runs in its own Modal app (or provider project) so its bill is separable. The report quotes billed spend vs the AUTH line. A pause is proven by the last job timestamp after the Owner's pause message. |

## 3. Standing ticket format (`M<n>-RES-01`)

One standing ticket per milestone from M1 (the first is `M1-RES-01`, which already exists and is blocked on its
compute AUTH). Shape (abridged; fill every field `tickets/SCHEMA.json` requires, e.g. `evidence` and `automated` on each AT):

```json
{
  "id": "M<n>-RES-01",
  "title": "Tier 2 research, M<n>: <this milestone's focus>",
  "milestone": "M<n>", "area": "RES", "owner": "gj-scenegraph", "qa": "gj-qa-release",
  "status": "open", "priority": "P2", "size": "L",
  "summary": "Standing Tier 2 research ticket for M<n> per research/tier2/README.md. Corpus only. No GPU spend without the month's compute AUTH.",
  "depends_on": ["M<n-1>-RES-01"],
  "auth_required": [{"type": "spend", "what": "Tier 2 compute, <month>: $<amount>", "auth_id": null, "status": "pending"}],
  "acceptance_tests": [
    {"id": "AT-1", "test": "Checkpoint report research/tier2/reports/M<n>.md filed with R1–R6 measured against targets", "level": "required"},
    {"id": "AT-2", "test": "Spend within the approved AUTH line (R6), billing export attached", "level": "required"},
    {"id": "AT-3", "test": "This milestone's focus delivered (e.g., M1: pipeline on 3 scenes, 1 class)", "level": "required"}
  ]
}
```

Rules: a single ticket per milestone that carries over and is never cancelled mid-milestone. If the core build
needs the budget, the ticket is set to `blocked` with the reason "paused by Owner" (SPEC §5).

## 4. Monthly compute AUTH REQUEST template

File as `governance/auth-requests/RES-<YYYY-MM>-tier2-compute.md`. The Coordinator logs the decision.

```markdown
# AUTH REQUEST: Tier 2 compute, <YYYY-MM>

- Type: spend · Ticket: M<n>-RES-01 · Requested by: gj-scenegraph · Date: <date>
- Amount requested: **$<total>** for <month> (hard cap; jobs stop at the cap)
- Provider + GPU: <Modal / Runpod / Lambda> · <H100 | A100 80 GB> at **$<x.xx>/h** (list price, date checked)
- Estimated hours: <h> GPU-hours = <h> × $<x.xx> = $<a>
- Per-scan runs: <n> scans × $<per-scan estimate> = $<b>
- Storage/egress: $<c> · Contingency (≤ 10 %): $<d> · **Total $<a+b+c+d>**
- Work covered: <this month's experiments, tied to R1–R6>
- Data: corpus only (Owner corpus / open-licence); no user data
- Pause rule: stops within 24 h of the Owner's word (R6); separate app/project for billing
- Last month: approved $<x>, spent $<y>, results <one line>
- Decision: APPROVED / DENIED / AMENDED by the Owner, <date> (the Coordinator logs AUTH #<n>)
```

## 5. Checkpoint report template

File as `research/tier2/reports/M<n>.md` at every checkpoint.

```markdown
# Tier 2 checkpoint report: M<n> (<date>)

## Summary
One paragraph: what was tried, what worked, the recommendation (continue / change course / shelve).

## Metrics vs targets
| # | Target | Measured | Pass? | Evidence |
|---|---|---|---|---|
| R1 | ≥ 70 % rooms / ≥ 80 % tabletops, ≥ 3 classes | <% per class, n/N> | | run id |
| R2 | ≤ $0.50, ≤ 10 min per scan | <median / p90 $ and min> | | billing export |
| R3 | ≤ 6 ms, ≤ 150 MB, 0 NaN | <see the frame-time table> | | Profiler PNG |
| R4 | ≥ 70 % prefer, 0 incidents | <%, incidents> | | form export |
| R5 | ≥ 80 % no hole | <%> | | stills |
| R6 | within $<line> | <$ spent> | | billing |

## Per-scan compute cost
| Scene | Class(es) | Segment (s) | Decouple/fill (s) | Embed (s) | Total wall-clock | Billed $ |

## Mobile frame-time table (reference iPhone, 30 fps target)
| Scene | Objects | Sim off (ms) | Sim on median (ms) | p95 (ms) | Added memory (MB) | Watchdog hits |

## Plausibility results
| Scene | Tier 2 preferred (%) | Realism (mean 1–5) T1 / T2 | Incidents |

## Spend
Approved $<x> · Spent $<y> · Provider breakdown.

## Next month
Plan + AUTH amount requested.
```

## 6. M1 prototype plan and expected cost

**Scope (M1-RES-01, after its AUTH):** one end-to-end slice on the corpus.

1. **Weeks 1–2, segmentation:** Gaussian Grouping / SAGA-style object masks on 5 reconstructed scenes (the
   open-licence set first, the Owner corpus as it arrives). Measure R1 segmentation IoU for the three classes.
2. **Weeks 2–3, decouple and fill:** a DecoupledGaussian-style hole fill for removed objects. Measure R5 on 10
   cases.
3. **Weeks 3–4, embed and simulate:** a VR-GS-style tet cage + XPBD for the cushion (soft body), plus rigid
   XPBD for the loose object; cloth deferred to M2 if time runs out. Offline first, then a Unity CPU XPBD
   prototype in the test scene for a first R3 read on desktop. The device measurement follows
   once TestFlight is available (Owner item 13).
4. **Report:** R1, R2 and R5 measured; R3 desktop-only (labelled); R4 deferred to M2 (needs ≥ 3 classes on device).

**Expected cost** (from `compute-budget-2026-10.md` §2b, Modal list prices, hours estimated):
low **$301** (80 h A100 80 GB + 100 scan runs), expected **$451** (120 h + 150 runs), high **$1,017**
(200 h H100 + 200 runs). Recommended month-1 AUTH: **$500**. The Unity/XPBD work runs locally at $0.
**Prerequisite:** reconstructed corpus splats, which already exist for the open-licence set (14 usable).

## 7. Reading list

Each entry has a one-line relevance note. Read in order within a group.

**Segmentation (the Gaussian Grouping lineage)**
- *Gaussian Grouping: Segment and Edit Anything in 3D Scenes*, Ye et al., ECCV 2024. Identity encodings per Gaussian supervised by SAM masks; the base for per-object splat segmentation and removal.
- *Segment Any 3D Gaussians (SAGA)*, Cen et al., AAAI 2025. Promptable, fast 3D segmentation via contrastive affinity features; the alternative when the class list is open.
- *Feature 3DGS*, Zhou et al., CVPR 2024. Distils foundation-model features into Gaussians; useful for class labels that line up with the Bible §4 surface classes.

**Decoupling and inpainting**
- *DecoupledGaussian: Object-Scene Decoupling for Physics-Based Interaction*, Wang et al., CVPR 2025 (arXiv 2503.05484). Separates objects from their contact surfaces with joint Poisson fields; exactly the R5 problem.
- *GScream*, Wang et al., ECCV 2024. 3D-consistent object removal for splats; the baseline DecoupledGaussian beats and a cheaper fallback.

**Embedding and simulation on Gaussians**
- *VR-GS: A Physical Dynamics-Aware Interactive Gaussian Splatting System in Virtual Reality*, Jiang et al., SIGGRAPH 2024. Segmented Gaussians embedded in tetrahedral cages and simulated with XPBD in real time in VR; the closest existing system to the target.
- *PhysGaussian*, Xie et al., CVPR 2024. MPM on Gaussians ("what you see is what you simulate"); high fidelity but too heavy for mobile, so it is the quality reference.
- *Tetrahedron Splatting*, Gu et al., NeurIPS 2024. A tet-based representation in which rendering and simulation share one mesh; informs the tet-embedding choice.
- *Spring-Gaus*, Zhong et al., ECCV 2024. A spring-mass model on Gaussians with parameters learnt from video; a cheap elastic alternative to tets.
- *PhysDreamer*, Zhang et al., ECCV 2024. Material properties inferred from video priors; a route to per-class stiffness without hand tuning.

**XPBD (the mobile-friendly solver)**
- *XPBD: Position-Based Simulation of Compliant Constrained Dynamics*, Macklin, Müller, Chentanez, MIG 2016. Compliance with time-step-independent stiffness; the core solver.
- *Small Steps in Physics Simulation*, Macklin et al., SCA 2019. Substepping beats iterations; sets the frame-budget strategy for R3.
- *Detailed Rigid Body Simulation with Extended Position Based Dynamics*, Müller et al., SCA 2020. Rigid bodies in the same XPBD framework, so the loose-object class shares one solver.

**2026 scene-level physics**
- *Scene-Level Heterogeneous Physics Simulation with 3D Gaussian Splats*, arXiv 2606.21753 (June 2026). One particle abstraction lets 3DGS assets interact with captured static collision geometry through multiple solvers; the scene-level (not isolated-object) setting this project needs.
- *FastPhysGS*, Ma et al., arXiv 2602.01723 (Feb 2026). Instance-aware interior particle filling plus fast material optimisation (about 1 min, 7 GB); relevant to the R2 per-scan budget.
- *GS-Playground*, RSS 2026. A parallel rigid-body physics engine synchronised with batched 3DGS rendering plus a Real2Sim workflow; a reference for the collision-proxy and render sync design.
- *Towards Physically Executable 3D Gaussian for Embodied Navigation (SAGE-3D)*, arXiv 2510.21307. Hybrid mesh collision + 3DGS render (convex decomposition with CoACD); supports keeping physics on proxies, not raw Gaussians.

## 8. Open questions for the Owner

1. **R3 device:** SPEC §5 says "reference Android device", but v1 is iOS-only (AUTH #003). This charter measures
   on the reference iPhone. Confirm, and a SPEC wording fix would follow via the Coordinator.
2. **R4 testers:** ≥ 12 unpaid internal testers are assumed. Paid testers would need a spend AUTH.
