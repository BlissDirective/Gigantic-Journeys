# Proposal — Capture UX + coaching (v1)

**Status: PROPOSAL for Owner review · 2026-09-19 · Coordinator.** Rationale doc (not a decision). Deepens SPEC §3.1 (capture) + §3.9 (privacy) and sharpens the capture tickets (M0-CAPT-01, M1-CAPT-01/02, M1-CAPT-03). **Builds on — does not re-open — the locked coaching UI (DESIGN_SYSTEM decision 6, AUTH #005)** and the locked create-flow waiting states (decision 7). Adopting it is a design-change **AUTH** touching SPEC §3.1/§3.9 (and DESIGN_SYSTEM decision 6 only if a "B" fork adds a widget). Grounded in Design Skills §3.5 (rules 12–15) and the self-host reconstruction backend (ADR-0005, AUTH #018).

## 0. Thesis
Capture is the **front door to the entire loop** — if the scan is bad, nothing downstream can save it, and a confusing capture is where new users quit. Decision 6 already locked the *coaching widgets* (paint-the-room coverage wash, the teal speed arc, blur/low-light handling, the illustrated mode toggle, the missed-corner arrow, the ring progress, the 72 pt record button). This proposal turns those widgets into a **system**: a complete flow, a real coaching curriculum for both modes, a quality gate that predicts *reconstruction* success, the capture→reconstruction data contract, failure/recovery, and the privacy of people who wander into frame. Three principles:
- **Coach by doing, never by reading** (rules 9, 19) — the room itself is the UI; words are a last resort.
- **The gate protects the user's time and our GPU** — reject early and kindly (rule 14); a 15-second nudge beats a 2-minute wait for a broken result.
- **Capture stays on our infrastructure** — GPS/EXIF stripped on device, processed self-host; no third party touches a real home (ADR-0005, §3.9).

## 1. The capture flow (state machine)
The locked widgets, wired into one sequence with explicit transitions:

`Scan tapped` → **Permission pre-prompt** (in-context, value-first; camera only, rule 10) → **Mode select** (the illustrated room/tabletop toggle, decision 6d) → **Framing/relocalize** (ARKit finds the space; "move your phone to look around") → **Coached capture** (decision 6a/6b/6c/6f live) → **Missed-corner check** (decision 6e arrow; *Got it* keeps recording / *Upload anyway*) → **Quality gate** (§3) → **Preview** (last 5 s + Retake, decision 6g) → **On-device strip + bundle** (§4) → **Upload** → hands off to the **create waiting state** (decision 7, progressive resolve).

Every state has a defined back/cancel and a recovery path (§5). The record button is the single primary action throughout (rule 4).

## 2. Coaching curriculum — two modes, two scripts (rule 13)
Decision 6 says *how* to show a cue; this says *what* to coach and *when*. Coaching is progressive: one cue at a time, surfaced only when the capture needs it, and it goes quiet when the user is doing well.

**Room walkthrough** (chest-height arc around the space):
1. *Start:* "Stand in a doorway or corner and hold your phone up." (framing)
2. *Motion:* arc slowly at chest height, keep the far surfaces in view — driven by the speed arc (6b) and coverage wash (6a).
3. *Overlap & angles* (rule 12): "Sweep back over what you've seen" if coverage is patchy; encourage a second height (a low pass under a table, a high pass over a shelf) when verticality is detected.
4. *Light:* the low-light card (6c) only where it's dark.
5. *Finish:* the missed-corner arrow (6e) points at the largest unpainted region; Done unlocks at 60 % coverage or 60 s (6f).

**Tabletop orbital** (slow circle at two heights around the build):
1. *Start:* "Put the build in the middle and step back a little." (keep the whole object in frame)
2. *Motion:* one slow circle at a low height, then one higher — the speed arc governs pace; the coverage wash accumulates on the object.
3. *Keep-in-frame:* a gentle nudge if the object leaves the frame ("Keep the build centered") — the tabletop failure mode.
4. *Light & finish:* as above; the missed-corner arrow points at unseen faces of the object.

Both scripts are **illustration + live overlay only** (checklist: no text-only instructions in capture). Copy is a single short line, teal (the capture-state color, decision 2), on an auto-contrast scrim (rule 1).

## 3. The quality gate — reconstruction-readiness, not just "dark/fast"
The pre-upload gate is where capture quality meets the reconstruction pipeline. It computes a cheap **on-device readiness score** from signals ARKit already gives us, and frames everything as help (rule 14):
- **Coverage** — painted-surface fraction vs the target (drives 6a/6f).
- **Overlap / parallax** — enough baseline between views for multi-view reconstruction (the signal most correlated with splat quality, and the one users never think about).
- **Blur ratio** — fraction of rejected frames (6c).
- **Light** — median luma / dark-region fraction (6c low-light card).
- **Tracking continuity** — ARKit pose confidence; drops flag a relocalization break (§5).
- **Duration/pace** — under 90 s active, warn past 3 min ("Long captures rebuild worse", 6f).

**Posture (the Owner's fork, §9.1):** the locked decision leans *kind and never hard-stop*. The open question is how much on-device intelligence to spend guaranteeing a good first result — a soft nudge only, an on-device predictor with a light **multi-pass "add coverage" loop**, or a predictive hard gate. Whatever the choice, the gate's verdicts map to the already-locked widgets; it never invents a new failure screen.

## 4. Capture → reconstruction upload contract
The bundle the client writes and uploads (referenced by M1-CAPT-01 AT-1, consumed by M1-CAPT-02, aligned to the M0-CAPT-01 corpus manifest so corpus and live scans share one shape):
- **Video** (compressed; frame timestamps).
- **Per-frame ARKit camera poses** + **camera intrinsics** (metric scale without LiDAR).
- **Depth** when present (LiDAR), flagged optional.
- **Gravity vector / world alignment** (up-axis for summit designation).
- **Mode** (room/tabletop), **device**, **capture duration**, **readiness score + coverage map** (so the server can log failure causes, M1-CAPT-02 AT-5).
- **No GPS, no EXIF, no location atoms** — stripped on device (`strip_metadata.py`, M0-CAPT-01) and re-verified server-side (§3.9).

Handed to the Inngest pipeline → self-host reconstruction (gsplat/Brush + COLMAP + Open3D) → splat + collision mesh behind signed URLs (M1-CAPT-02). Source video is deleted once derived assets exist (§3.9 retention).

## 5. Failure & recovery (the paths apps skip)
- **Tracking loss:** pause coaching, "Point at a spot you've already scanned" → ARKit relocalizes → resume with coverage intact; never silently discard progress.
- **Interruption** (call, app switch): the session is preserved; on return, *Resume* or *Start over*.
- **Too short / too little coverage:** the missed-corner arrow + (fork-dependent) an "add a quick pass" suggestion rather than a bare rejection.
- **Reconstruction failed downstream:** a kind result — "This one didn't come out — quick retake?" — with a **free retry** that pre-selects the same mode and keeps the user oriented. A failure never costs the user their place in the loop.

## 6. Accessibility & privacy
- **Permissions in context** (rule 10): camera requested on the first Scan tap with a one-line value pre-prompt, never on launch. No biometric prompt exists in v1 (AUTH #020).
- **Reachable while moving:** 56 pt+ controls (rule 6/27), one-handed record reachable, works muted (visual/haptic cues already carry capture per decision 6; no audio required).
- **Reduce Motion:** the AR overlays (coverage wash, arrow) respect Reduce Motion with calmer transitions (DESIGN_SYSTEM decision 10).
- **Well-lit indoor rooms and tabletop builds only** (SPEC §3.1); no outdoor/street capture (§4 non-goal).
- **People in frame (the Owner's fork, §9.2):** a real home may have people in it. Capture already stays on our infra and strips GPS/EXIF; the question is whether we (A) *coach* "scan spaces, not people" and rely on the opt-in publish-time moderation pass, or (B) add on-device person detection that warns/blurs at capture time. Either way, **published** environments still pass the §3.7 moderation pass.

## 7. First-run guided capture
After the play-first demo (rule 9: run and jump within 60 s, *then* "now scan yours"), the **first** capture gets a one-time, slightly richer coach-through — a short "here's how to sweep the room" overlay that doesn't repeat on later scans. This is the highest-leverage retention moment (rule 9), so it earns a little extra hand-holding, then gets out of the way.

## 8. Governance — what adopting this changes (AUTH-gated)
- **SPEC §3.1** — deepen with the capture flow/state machine, the two coaching scripts, the reconstruction-readiness gate signals, the upload contract, and failure/recovery.
- **SPEC §3.9** — add the people-in-frame posture chosen in §9.2.
- **DESIGN_SYSTEM decision 6 (LOCKED)** — unchanged unless a **"B" fork** adds a widget (a multi-pass "add a pass" prompt, or a person-in-frame warning/blur); if so, this AUTH extends decision 6 to cover it.
- **Tickets** — sharpen M1-CAPT-01 (readiness-score gate signals, the two coaching scripts, failure/recovery, the upload contract), M1-CAPT-02 (log readiness score + coverage on failures; free-retry handoff), M0-CAPT-01 (manifest carries mode/readiness/coverage to match the live bundle). No new tickets required unless a "B" fork adds a scoped one (on-device predictor / person detection).

## 9. Decisions needed before editing the protected docs
### 9.1 Capture quality-assurance strategy
- **(A) Soft coaching + friendly retry** *(recommended)* — trust the locked coaching + a light readiness heuristic that only nudges; allow "upload anyway"; on downstream failure, a kind free-retry. Simplest, matches the locked "never hard-stop" posture, fewest abandons; costs some wasted reconstructions (cheap on self-host, <$1/scan).
- **(B) On-device readiness predictor + multi-pass "add coverage" loop** — a cheap on-device score can recommend "add a quick pass over here" and let the user append passes to the same scan. Better first-try success on big rooms; more UX + on-device work (a scoped ticket).
- **(C) Predictive hard gate** — block weak uploads until re-captured. Best GPU-cost control; most friction and abandons.

### 9.2 People in the frame (privacy)
- **(A) Coach + publish-time moderation** *(recommended)* — guide "scan spaces, not people," strip GPS/EXIF, keep processing on our infra, catch faces at the opt-in publish moderation pass. Simplest; capture never leaves our infra.
- **(B) On-device person detection in capture** — warn (and optionally blur) when a person is in frame. Stronger capture-time privacy; more scope, on-device compute, and false positives.

On your answers I'll file the AUTH, deepen SPEC §3.1/§3.9 (and extend DESIGN_SYSTEM decision 6 only if a "B" is chosen), and sharpen the capture tickets. Unless you object, I'll adopt the **flow/state machine**, the **two coaching scripts**, the **reconstruction-readiness gate**, the **upload contract**, the **failure/recovery paths**, and the **first-run guided capture** as specified.
