# Gigantic Journeys — Design System

`design/DESIGN_SYSTEM.md` · v0.5 · 2026-09-16 · Status: **LOCKED except by AUTH REQUEST (design-change)**

The Owner locks; `gj-design` implements (tokens in `design/tokens/`, Unity UI Toolkit in `unity/Assets/UI`); every UI and gameplay PR is reviewed against this file (REVIEW_RUBRIC §G). Binding constraints come from `Gigantic-Journey-Design-Skills.md` §3 (v1.1), which this file specializes and never contradicts. CI blocks PRs that edit this file without an `APPROVED #n`; appending under §12 Field notes is allowed.

## 0. How to read this file

Decisions 1–4 were **locked by the Owner in the design session of 2026-09-14** and transcribed by the Owner on 2026-09-16 (ticket M0-OWNER-02). Each section carries the binding constraints from the Design Skills, the locked decision text, and a Coordinator consistency note. The locked text changes only by AUTH. Decision 3 was amended on 2026-09-16 (AUTH #004) with five adopted Coordinator recommendations.

Decisions 5–10 are open until the M0 checkpoint: `gj-design` proposes (ticket M0-DSGN-01, under `design/proposals/`), the Owner locks by AUTH (ticket M0-OWNER-03).

## 1. Non-photo element language — LOCKED 2026-09-14 (transcribed 2026-09-16)

Scope: avatar treatment, summit beacon, route markers, vista markers, the flag-planting moment, the HUD's non-photo chrome.

Binding constraints (Design Skills rules 1, 2, 20, 21; Bible §8):
- The only non-photo things in play: the avatar, one summit beacon, optional route and vista markers, the HUD.
- Beacon and markers share one restrained treatment: thin light, low saturation, no solid geometry; always drawn on top with depth-fade so orientation is never lost.
- The avatar is the only rendered solid, set off by a subtle rim light and contact shadow; real objects stay photoreal, untouched except for Tier 1 displacement.
- Nothing encodes state by hue alone; nothing new enters the play viewport without an ADR.

**Locked decision text (Owner, transcribed 2026-09-16):**
- Avatar: warm rim light plus contact shadow; the only rendered solid.
- Summit: thin beam of light visible through geometry, toggle in settings, resolves into a flag on plant.
- Routes: faint footprints that fade behind you; shown only when a route is selected; off by default for explorers.
- Vistas: small lens-flare sparkle at the vantage point; reaching it opens photo mode.

Coordinator consistency note: matches rules 1, 2, 20, 21 and Bible §8. The beam is on by default; the settings toggle is read as a player preference (turning it off is the player's choice, and the beam still ignites in the signature transition so orientation is never lost at entry). A different default would be an AUTH.

## 2. Brand: palette, scrim strategy, wordmark, iconography, voice — LOCKED 2026-09-14 (transcribed 2026-09-16)

Binding constraints (rules 1, 3, 5, 23; §4 checklist):
- Every scan is an unknown full-color background: text and controls sit on a translucent scrim auto-picked per scan; contrast computed at runtime; text ≥ 4.5:1, icons ≥ 3:1; deuteranopia-safe state colors.
- Each surface is defined twice: glass and flat (Reduce Transparency, Increase Contrast, and the iOS intensity slider respected).
- Type scale of at most 5 steps on the platform body size (17 pt iOS, 16 sp Android); HUD numerals tabular; line length 45–75 characters.
- Voice: short, warm, verbs first, no jargon; permissions asked in context; errors framed as help.

**Locked decision text (Owner, transcribed 2026-09-16):**
- Accent: `accent.amber` #F2A93B; `accent.amberLight` #FFD27A (rim light, beacon core, flag highlight).
- Neutrals: `ink.charcoal` #1C1F26, `surface.charcoal` #2A2E37, `paper.cream` #F5EFE6, `surface.cream` #EDE5D8, `text.muted` #8A8F99.
- Cool anchor: `semantic.teal` #00585E (capture-state and progress only). Success `semantic.sage` #7A8F7B, error `semantic.terracotta` #C9573D, both muted.
- Rules: amber never body text on cream; scrims picked per scan (charcoal over bright rooms, cream over dark), text always ≥ 4.5:1; amber under 10 % of any screen.
- Wordmark: "Gigantic Journeys" in a clean geometric sans, the "i" in Gigantic dotted with a tiny avatar silhouette. Icon: summit beam rising from a tiny isometric room, amber on charcoal.
- Voice: short, warm, second person, verbs first. Vocabulary: environment / journey / summit / route / vista, never level / map / goal / user.

Coordinator consistency note (WCAG 2.x, measured 2026-09-16; full table in §12): ink on cream 14.4:1 and paper on charcoal 14.4:1 pass. `text.muted` fails body text on cream (2.8:1) and surface.cream (2.6:1) and is borderline on surface.charcoal (4.2:1). `semantic.sage` (3.0:1) and `semantic.terracotta` (3.7:1) on cream are icon and fill colors, not text; `semantic.teal` fails on charcoal (2.0:1). Token guidance for gj-design, which adds derived tokens without changing the locked palette: muted text on cream surfaces uses a darker derived token (`#63676E` reaches 4.5:1 on surface.cream) or sizes ≥ 18 pt; muted text on charcoal uses `#90959F`; semantic colors are never body text and pair with ink or paper text; amber and teal are used only on the surfaces they pass on. The vocabulary rule applies to every player-facing string, including the Duo "diorama overview" (never "map").

## 3. Signature transition: the shrink / diorama moment — LOCKED 2026-09-14 (transcribed 2026-09-16; amended by AUTH #004)

Binding constraints (rules 7, 8, 28; SPEC §3.11):
- The one hero animation; it has its own budget. Other UI motion is 150–300 ms, screen transitions 400–600 ms.
- A Reduce Motion equivalent (cross-fade) is required.
- It is the second beat of the store preview and must make the scale relationship obvious.
- Optional iPhone Duo variant (AUTH #003, ticket M3-DUO-02): the physical unfold triggers the same transition, spanning the outer-to-inner display change; one implementation, two triggers; the Reduce Motion variant applies to both.

**Locked decision text (Owner, transcribed 2026-09-16):**
- Continuous 2.5 s pull-back-and-up; room edges soften into a floating diorama over a soft-blurred version of the room itself; avatar drops in with a dust puff; beam ignites at the summit; camera settles into play framing.
- Auto-plays on first entry to an environment, tap-to-skip on repeats. Reduce Motion: cross-fade over the blurred room, beam ignition kept.
- The blurred backdrop is a low-res splat render blurred once and cached, not a live blur.

**Amendments adopted by the Owner, 2026-09-16 (AUTH #004; items 1, 2, 3, 6, 7 of `design/proposals/decision-3-transition-input.md`):**
- Scale anchor: the first 0.3 s of the 2.5 s hold the avatar at real size in the real room with its contact shadow visible before the pull-back begins.
- Summit last: the beam ignites as the final beat and the camera nudges 5 to 10 degrees toward it before settling into play framing.
- Sound and haptics: one rising tone across the pull-back resolving on ignition; the Tier 0 dust-puff sound on the drop; haptic light on the drop, medium on ignition.
- Short form on return: repeats play a 0.8 s cut that keeps the drop and the ignition; the full 2.5 s plays on first entry, first summit, and after a flag plant. Tap-to-skip remains.
- Reverse transition as the results backdrop: after a flag plant, the diorama grows back into the room behind the results screen with the flag visible; that frame is the default share image.

Coordinator consistency note: matches rules 7, 8, 27, 28 (own budget; Reduce Motion cross-fade; no live full-screen blur; the diorama as the hero shot). Items 4, 8, and 9 of the input remain suggestions for gj-design; item 5 follows from decision 2; item 10 is ticket M3-DUO-02.

## 4. Avatar presentation — LOCKED 2026-09-14 (transcribed 2026-09-16)

Binding constraints (rules 15, 16, 20; SPEC §3.2):
- Realistic proportions of about 7 heads, stylized grounded materials, rim light plus contact shadow.
- Likeness confirmation: the head turning beside the source photo, "Is this you?", Retake or Tweak (skin tone, hair, glasses, build); no slider editor.
- Default wardrobe roughly matches the photo; the store appears only after the first win.
- Optional iPhone Duo variant (AUTH #003, ticket M2-DUO-01): tent-posture capture with the rear cameras while the outer display shows framing, countdown, and coaching; the same consent gate and deletion path as the standard flow.

**Locked decision text (Owner, transcribed 2026-09-16):**
- Default wardrobe generated to match the user's photo, normalized onto four rig-clean silhouettes (casual, athletic, layered, dressed); more items as later DLC.
- Capture flow: full-body shot with 360° body rotation, then face close-up with rotation; retakes for better capture.
- Likeness confirmation: generated head turning beside the source photo; Yes / Retake / Tweak, where Tweak exposes four coarse controls (skin tone, hair, glasses, build).
- In-world: warm rim light and contact shadow; reactive idle (avatar reacts to the environment per Movement Bible Section 7).

Coordinator consistency note: matches rules 15, 16, 20 and Bible §7. SPEC §3.2 and §2 capture wording is aligned to this decision (SPEC v1.2). Player-facing copy says "your photo", never "user" (decision 2 vocabulary).

## 5. Play layout — OPEN (proposal M0-DSGN-01; lock M0-OWNER-03)

Binding constraints: two-thumb landscape; floating stick anywhere in the left third; jump is the largest right-thumb target; one contextual action button that appears only when relevant; controls repositionable and resizable; play controls ≥ 56; HUD in the top 8 %; controller support from day one; camera per Bible §8; optional iPhone Duo variants: the 7.6-inch near-square inner display and a stand-mode layout with the photograph on the upper half and every control on the lower half (`design/proposals/iphone-duo-track.md`, AUTH #003).

> Proposal slot.

## 6. Capture coaching UI — OPEN

Binding constraints: coach steady motion, overlap, angles, light; live coverage heat-map; speed meter turning amber; blur rejection with a haptic; "you missed this corner"; two scripts (room walkthrough, tabletop orbital) chosen by one illustrated toggle; reject early and kindly; no text-only instructions.

> Proposal slot.

## 7. Create-flow waiting states — OPEN

Binding constraints: progress on every wait over 1 s; determinate progress plus something to look at over 10 s; the splat resolves progressively; a "what's happening" explainer; never a blank spinner.

> Proposal slot.

## 8. Browse and ranking cards — OPEN

Binding constraints: browse by place, thumbnails are the room; sort tabs Top this week, New, Near your scale; one-tap four-axis rating; one-tap report with a reason sheet; creator stats visible; "Under review" badge.

> Proposal slot.

## 9. Results and store screens — OPEN

Binding constraints: one primary action ("Share"); the store after a win, never on a loss; two SKUs with clear prices; one-tap restore; no fake scarcity; the results screen carries the detail the HUD omits.

> Proposal slot.

## 10. Accessibility baseline — OPEN

Binding constraints: assist options (Bible §10 assist block), colorblind palettes, Reduce Motion and Reduce Transparency fallbacks, Dynamic Type in the shell, 44 pt / 48 dp targets.

> Proposal slot.

## 11. Change log

| Version | Date | Change | Authorization |
|---|---|---|---|
| 0.1 | 2026-09-15 | File created; decisions 1–4 recorded as locked with their binding constraints, text pending transcription; 5–10 open | AUTH #000 |
| 0.2 | 2026-09-15 | §5 gains the optional iPhone Duo layout variants | AUTH #003 |
| 0.3 | 2026-09-15 | §3 and §4 gain the optional iPhone Duo variants for the Owner's selected features | AUTH #003 (Owner selection) |
| 0.4 | 2026-09-16 | Decisions 1–4 transcribed from the Owner's 2026-09-14 lock; consistency notes and palette contrast measurements added; §5 vocabulary fix (diorama overview) | Transcription, M0-OWNER-02 (no AUTH consumed) |
| 0.5 | 2026-09-16 | §3 amended with the five adopted Coordinator recommendations (scale anchor, summit last, sound and haptics, short form on return, reverse transition as results backdrop) | AUTH #004 |

## 12. Field notes

(Bots append contradictions and measured values here; the Owner reviews them at each checkpoint.)

- 2026-09-16 (Coordinator): WCAG 2.x contrast of the decision 2 palette. Pass for body text (≥ 4.5:1): ink.charcoal on paper.cream 14.4, ink.charcoal on surface.cream 13.2, paper.cream on ink.charcoal 14.4, paper.cream on surface.charcoal 11.9, accent.amber on ink.charcoal 8.3, accent.amber on surface.charcoal 6.8, accent.amberLight on ink.charcoal 11.6, ink.charcoal on accent.amber 8.3, semantic.teal on paper.cream 7.2, paper.cream on semantic.teal 7.2, text.muted on ink.charcoal 5.1, semantic.sage on ink.charcoal 4.8. UI or large text only (3:1 to 4.5:1): text.muted on surface.charcoal 4.2, semantic.terracotta on ink.charcoal 3.9, semantic.terracotta on paper.cream 3.7, paper.cream on semantic.terracotta 3.7, semantic.sage on paper.cream 3.0. Fail (< 3:1): text.muted on paper.cream 2.8, text.muted on surface.cream 2.6, semantic.teal on ink.charcoal 2.0, accent.amber on paper.cream 1.8 (already forbidden by the rule). Derived tokens that pass: muted-on-cream `#63676E` (4.5:1 on surface.cream), muted-on-charcoal `#90959F` (4.5:1 on surface.charcoal).
