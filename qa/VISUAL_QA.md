# Visual QA procedure and evidence standard

`qa/VISUAL_QA.md` · v1.0.1 · 2026-09-27 · Owner: gj-qa-release · Ticket M0-QA-02 · Sources: Design Skills §4 (pre-PR design checklist), SPEC §6 and §11 (AUTH #003), `.github/ISSUE_TEMPLATE/defect.md`, `.github/PULL_REQUEST_TEMPLATE.md`, plan §4 step 3, kit §3.7.

Every **gameplay, UI, and capture** PR goes through this pass before the Coordinator reviews it. Other PRs (services, docs, CI) skip it unless they change something on screen.

**Policy (SPEC §11, AUTH #003).** QA passes, device checks and performance numbers are **suggestions, never merge gates**. The merge gates are the automated CI checks and the security rules. Two parts of this document *are* enforced, because they are hygiene and security rules rather than quality measurements:
- the evidence rules in §2 (CI job `qa evidence standard`, `.github/scripts/check_qa_evidence.py`);
- the privacy line in §6 (SECURITY_CHECKLIST; REVIEW_RUBRIC C10).

---

## 1. The flow

1. **Builder**, before opening the PR: runs the Design Skills §4 checklist on the diff (UI and gameplay PRs) and ticks the PR template's QA section. The PR body requests a `gj-qa-release` visual pass.
2. **gj-qa-release** (the Operator in the QA hat, on the QA box or with the Owner's iPhone evidence):
   1. Check out the PR branch and note the build: branch and short SHA, Unity version, and the device or host with its graphics API.
   2. Run the checklist for the PR type (§5). Where a scripted path exists, use it: `qa/scripts/editor_smoke.py` for Editor renders (M0-QA-01) and the EditMode/PlayMode suites.
   3. Commit the evidence set to the PR branch under `qa/evidence/<ticket>/` (§2), including its `README.md` with the privacy line (§6). Attach clips to the PR (§3).
   4. File a DEFECT issue for every problem found (§7) and link it from the PR.
   5. Post the QA verdict as a PR comment (§8): **PASS**, **PASS WITH DEFECTS** (S3/S4 only), or **FAIL** (any S1/S2 open).
3. **Coordinator** reviews with the verdict in hand. An open S1/S2 is a strong signal, but not a gate by itself (AUTH #003); the Coordinator decides and records why.
4. After fixes, QA re-verifies: new screenshots take the **next** `nn`, old ones stay, and the DEFECT is closed with the new evidence path.

## 2. Evidence standard

| Rule | Detail |
|---|---|
| Location | `qa/evidence/<ticket>/`, where `<ticket>` is an existing ticket id (`tickets/<ticket>.json`) |
| Screenshot name | `qa/evidence/<ticket>/<nn>-<what>.png`: `nn` is two digits in capture order (`01`, `02`, …), `what` is lowercase kebab-case naming the subject and condition. Examples: `01-overlay-editor-bright-scan.png`, `04-profiler-iphone-15-pro.png` |
| Format and size | PNG only, **≤ 2 MB** (2 × 1024 × 1024 bytes) each. Downscale or crop rather than compress into artifacts; 1280×720 or the device's native landscape size is enough |
| Placement | Screenshots sit directly in the ticket folder (no subfolders). Machine sidecars (`*.json`, `*.txt`, `*.csv`) may sit in subfolders, e.g. `run-2/result.json` |
| Index | Every folder with a PNG has a `README.md`: one bullet per file (what it shows, build SHA, Unity version, device or host + graphics API, the steps), clip links if any, and the **Privacy:** line (§6) |
| Never committed | Clips (§3), raw Editor or device logs (sanitized excerpts go to `qa/reports/<ticket>/*.txt`), raw scans (`.ply/.spz/.splat`, already blocked by repo hygiene), photos of people or places that are not the test content |

Check locally before pushing: `python .github/scripts/check_qa_evidence.py`. CI runs the same script on every push (governance workflow, job `qa evidence standard`).

## 3. Clips

- **≤ 30 s** each. One behaviour per clip (a verb, a transition, a bug repro).
- **Attached to the PR** (drag into the PR description or a comment) and **never committed**. `qa/evidence/` rejects video and GIF files, and repo hygiene rejects `.mp4/.mov/.m4v` anywhere.
- List each clip in the evidence `README.md` (link and one line) so the set stays complete. The privacy line covers the clips too.
- Record with the in-game debug overlay visible (M0-UNITY-04) when frame rate matters.

## 4. Reference-device Profiler screenshot

- **Reference devices are the Owner's iPhones:** the newest one (60 fps target) and the oldest test one (30 fps target) (SPEC §6, §11.4). SPEC §11.4 supersedes Design Skills §4's "reference Android device" wording.
- **Every gameplay and UI PR** carries a Unity Profiler screenshot from a Development build on a reference iPhone, named `<nn>-profiler-<device>.png`. It must show the CPU and GPU frame-time lanes and the frame-time readout over a representative stretch (at least 10 s of play), with the device model and build SHA written in the README bullet.
- When no Profiler session is possible (no Development build reached the device, or no Owner device time), attach the debug overlay's **saved performance report** instead (fps p50/p99 over 60 s, device, build; M0-UNITY-04 AT-1) as a `.txt` sidecar, or write **"Profiler: not measured (<reason>)"** in the README and the PR's Performance section. Under AUTH #003 this is a required *line*, not a required *measurement*.
- Editor-only numbers from the QA box (Vulkan on lavapipe, a CPU rasterizer) are **not** performance evidence. They prove correctness only.

## 5. Checklists by PR type

Tick every item in the QA comment as ✅ pass, ❌ fail (with its DEFECT), or n/a with a reason.

### 5.1 All three types
- [ ] Build noted (branch, short SHA, Unity version, device or host + graphics API).
- [ ] The ticket's acceptance tests that need visual evidence each have a named screenshot or clip.
- [ ] Console clean while exercising the change: 0 errors, 0 exceptions (the smoke task counts them).
- [ ] Evidence set follows §2; the privacy line is present (§6).
- [ ] Profiler screenshot or "not measured" line (§4) for gameplay and UI PRs.

### 5.2 Gameplay (player, movement, camera, journey, HUD in play)
- [ ] Each changed verb or camera behaviour is captured in a clip ≤ 30 s from the default camera.
- [ ] Movement feel matches the Movement Bible values in `config/movement.json`; no hard-coded constants (CI `movement-sync` covers the file, QA covers the feel).
- [ ] HUD stays within the **top 8 %** in landscape; nothing new in the play viewport without an ADR (Design Skills §4).
- [ ] Readability on **three test scans**: a bright room, a dark room and a cluttered tabletop. Until the M0-OWNER-01 corpus exists, use the procedural sample (`Assets/Capture/Samples/SplatSample.unity`) and state the substitution.
- [ ] Frame rate against the SPEC §6 target for the tier (the overlay or the Profiler, §4).
- [ ] Reduce Motion equivalent for any new camera shake or animation.

### 5.3 UI (menus, create/browse/results, overlays, onboarding)
- [ ] Screenshot of every new or changed screen on the three test scans (bright, dark, cluttered).
- [ ] Contrast: text ≥ 4.5:1, icons ≥ 3:1 over the photo background (measure on the screenshot).
- [ ] Glass surfaces have a flat fallback: captured with **Reduce Transparency** and **Increase Contrast** on.
- [ ] Touch targets ≥ 44 pt, play controls ≥ 56 pt; safe-area insets respected (a notched or Dynamic Island iPhone, or the Device Simulator).
- [ ] One primary action per screen; it is the largest and highest-contrast element.
- [ ] Waits > 1 s show progress; waits > 10 s show determinate progress plus content.
- [ ] Deuteranopia simulation screenshot for any new state colour.
- [ ] Copy is short, warm, verb-first, no jargon (voice guide, DESIGN_SYSTEM once locked).

### 5.4 Capture (scan flow, coaching, readiness gate, upload)
- [ ] Each coaching state and the readiness-gate outcomes (pass, "add a pass", fail) are captured.
- [ ] No text-only instructions: illustrations or live overlays (Design Skills §4; DESIGN_SYSTEM capture constraints).
- [ ] Permission prompts appear in context, with the recovery path when denied.
- [ ] Progress through upload and processing; waits > 10 s determinate.
- [ ] Test content only: a corpus room or tabletop the Owner captured for testing (M0-OWNER-01) or public-domain/procedural content. **Never** a real person, a home address, documents or screens.
- [ ] Metadata: no GPS/EXIF survives into anything uploaded or committed (SECURITY_CHECKLIST; `services/reconstruction/tools/strip_metadata.py`).

### 5.5 Design Skills §4 items QA re-checks
The Builder self-checks all of Design Skills §4. QA independently **re-checks** the items a screenshot or device can disprove, and **trusts CI** for the rest:

| Design Skills §4 item | QA | Where |
|---|---|---|
| Contrast on three test scans (text ≥ 4.5:1, icons ≥ 3:1) | re-check | 5.3 |
| Flat fallback for glass (Reduce Transparency, Increase Contrast) | re-check | 5.3 |
| Touch targets ≥ 44 pt / controls ≥ 56; safe-zone insets | re-check | 5.3 |
| Reduce Motion equivalent for every animation | re-check | 5.2 |
| One primary action per screen | re-check | 5.3 |
| No text-only instructions in capture, create, play | re-check | 5.4 |
| Waits > 1 s progress; > 10 s determinate + content | re-check | 5.3, 5.4 |
| New movement/camera constant in the shared tuning file | CI (`movement-sync`) + feel check | 5.2 |
| HUD within the top 8 %; nothing new in the viewport without an ADR | re-check | 5.2 |
| Colorblind (deuteranopia) check on new state colours | re-check | 5.3 |
| Profiler screenshot on the reference device | re-check it is present, or the "not measured" line | §4 |
| Screenshots or clip attached; QA pass requested | this procedure | §2, §3 |
| Copy against the voice guide | re-check | 5.3 |

## 6. Privacy line (every evidence set)

Every evidence `README.md`, every QA comment and every DEFECT carries this line, filled in:

> **Privacy:** the evidence contains no faces, addresses, documents, or screens with personal data. Content: <what is visible, e.g. "procedural summit splat only" or "corpus room R03, no people">.

- It is checked **per screenshot and per clip**, by a person looking at each one. Automated lines (the smoke report's) state what makes them true, e.g. "0 project textures".
- If any evidence fails it: do not commit it. If it is already on a branch, remove it and tell the Coordinator before merge. If it reached `main` (a public repository), treat it as a security incident: tell the Coordinator and the Owner at once, because the file stays in git history until it is purged.

## 7. DEFECT issue flow (severities S1–S4)

File with the **DEFECT (QA)** issue template (`.github/ISSUE_TEMPLATE/defect.md`), title `DEFECT: <ticket id> — <one line>`, one defect per issue.

| Severity | Meaning | Handling |
|---|---|---|
| **S1** | Blocks the milestone exit test | Tell the Coordinator in the PR at once; verdict FAIL; fixed on the same PR or the exit test is re-planned. Listed in the checkpoint report |
| **S2** | Breaks an acceptance test of the ticket | Verdict FAIL; fixed on the same PR, or the AT is reported unmet and the ticket stays in review |
| **S3** | Visible problem, workaround exists | Verdict PASS WITH DEFECTS; follow-up ticket or fix in the next PR |
| **S4** | Cosmetic | Verdict PASS WITH DEFECTS; batched into polish |

Lifecycle: **filed** (evidence path or clip, steps, expected/actual, build, device, severity, design rule violated, privacy line) → **linked** from the PR and the ticket history → **fixed** (the fix PR says `Fixes #<issue>`) → **verified** by QA with new evidence under the next `nn` → **closed**. A severity changes only with a comment saying why. The template's `defect`/`qa` labels apply once those labels exist in the repository (they do not as of 2026-09-27); until then the title prefix identifies defects.

## 8. QA verdict comment (template)

```
QA pass — <ticket> — <PASS | PASS WITH DEFECTS | FAIL>
Build: <branch> @ <sha> · Unity <version> · <device/iOS or host + graphics API>
Checklist: §5.<type> — <n> pass, <n> fail, <n> n/a (list fails with DEFECT #)
Evidence: qa/evidence/<ticket>/ (01-…, 02-…) · clips: <links>
Profiler: <nn>-profiler-<device>.png | perf report | not measured (<reason>)
Defects: #<n> S<k>, …
Privacy: the evidence contains no faces, addresses, documents, or screens with personal data. Content: <…>
```

## 9. First live use: M0-UNITY-04 (debug overlay)

M0-UNITY-04 is the loop-proving ticket (M0 exit test). **Applied 2026-09-27** (§5.1 + §5.3 + §4) on commit `408e90a`, delivered as a direct commit to main, so the verdict lives in `qa/reports/M0-UNITY-04.md` instead of a PR comment. Delivered: `01-overlay-bright-scan.png`, `02-overlay-dark-scan.png`, `03-overlay-safe-area-iphone-15-pro.png` (simulated safe area, rendered by a Development Linux player rather than the Device Simulator), `run/` sidecars; the device shot and device report (rows 04 and perf-report below) wait for an Owner iPhone. Planned evidence set, `qa/evidence/M0-UNITY-04/`:

| File | Shows | AT |
|---|---|---|
| `01-overlay-editor-bright-scan.png` | Overlay (F3) over a bright scan in the Editor: fps 1 s avg + p99/5 s, frame ms, build, SHA, scene, device | AT-1, AT-3 |
| `02-overlay-editor-dark-scan.png` | The same over a dark scan: scrim readable | AT-3 |
| `03-overlay-safe-area.png` | Top-right inside the safe area, ≤ 8 % of landscape height (Device Simulator, notched iPhone) | AT-3 |
| `04-overlay-device-<model>.png` | Three-finger-tap toggle on an Owner iPhone (TestFlight Development build), when available | AT-1 |
| `perf-report-<model>.txt` | The overlay's saved performance report (fps p50/p99 over 60 s) | AT-1, §4 |
| `README.md` | Index, build, steps, EditMode test name for the GJ_DEBUG exclusion (AT-2), privacy line | all |

Clips: overlay toggle (≤ 30 s), attached to the PR. The Editor shots can come from the QA box (Unity 6000.0.84f1, Vulkan/lavapipe, the M0-QA-01 smoke tooling pointed at the scan scenes). Until M0-OWNER-01 scans exist, the "bright/dark scan" shots use the procedural sample under two lighting setups, labelled as a substitution.

## 10. Changes

| Date | Version | Change |
|---|---|---|
| 2026-09-27 | 1.0.1 | §9: first live use recorded (M0-UNITY-04 evidence set, verdict in `qa/reports/M0-UNITY-04.md`) |
| 2026-09-27 | 1.0 | Created (M0-QA-02). Existing evidence renamed to the rule (`M0-QA-01/01-editor-smoke.png`, `M0-UNITY-02/01-splat-sample-editor.png`); `check_qa_evidence.py` + CI job added |
