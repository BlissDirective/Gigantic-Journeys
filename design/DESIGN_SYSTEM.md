# Gigantic Journeys — Design System

`design/DESIGN_SYSTEM.md` · v0.3 · 2026-09-15 · Status: **LOCKED except by AUTH REQUEST (design-change)**

The Owner locks; `gj-design` implements (tokens in `design/tokens/`, Unity UI Toolkit in `unity/Assets/UI`); every UI and gameplay PR is reviewed against this file (REVIEW_RUBRIC §G). Binding constraints come from `Gigantic-Journey-Design-Skills.md` §3 (v1.1), which this file specializes and never contradicts. CI blocks PRs that edit this file without an `APPROVED #n`; appending under §12 Field notes is allowed.

## 0. How to read this file

Decisions 1–4 were **locked by the Owner in the design session of 2026-09-14**. The Coordinator did not have that session's transcript when this file was created, so each of those sections carries (a) the binding constraints already in force from the Design Skills, which Bots implement now, and (b) a marked slot for the locked decision text, which the Owner transcribes (ticket M0-OWNER-02). Filling that slot for the first time is a transcription, not a change: no AUTH needed. Any later edit is a change: AUTH needed.

Decisions 5–10 are open until the M0 checkpoint: `gj-design` proposes (ticket M0-DSGN-01, under `design/proposals/`), the Owner locks by AUTH (ticket M0-OWNER-03).

## 1. Non-photo element language — LOCKED 2026-09-14

Scope: avatar treatment, summit beacon, route markers, vista markers, the flag-planting moment, the HUD's non-photo chrome.

Binding constraints (Design Skills rules 1, 2, 20, 21; Bible §8):
- The only non-photo things in play: the avatar, one summit beacon, optional route and vista markers, the HUD.
- Beacon and markers share one restrained treatment: thin light, low saturation, no solid geometry; always drawn on top with depth-fade so orientation is never lost.
- The avatar is the only rendered solid, set off by a subtle rim light and contact shadow; real objects stay photoreal, untouched except for Tier 1 displacement.
- Nothing encodes state by hue alone; nothing new enters the play viewport without an ADR.

> **Locked decision text: PENDING TRANSCRIPTION by the Owner (M0-OWNER-02).** Paste the exact treatment decided on 2026-09-14: beacon form and behavior, route marker form, vista marker form, the flag-plant moment, avatar rim and contact-shadow values or references.

## 2. Brand: palette, scrim strategy, wordmark, iconography, voice — LOCKED 2026-09-14

Binding constraints (rules 1, 3, 5, 23; §4 checklist):
- Every scan is an unknown full-color background: text and controls sit on a translucent scrim auto-picked per scan; contrast computed at runtime; text ≥ 4.5:1, icons ≥ 3:1; deuteranopia-safe state colors.
- Each surface is defined twice: glass and flat (Reduce Transparency, Increase Contrast, and the iOS intensity slider respected).
- Type scale of at most 5 steps on the platform body size (17 pt iOS, 16 sp Android); HUD numerals tabular; line length 45–75 characters.
- Voice: short, warm, verbs first, no jargon; permissions asked in context; errors framed as help.

> **Locked decision text: PENDING TRANSCRIPTION by the Owner (M0-OWNER-02).** Paste: palette (hex values and roles, light and dark scrims), wordmark description or file reference, iconography style, the voice guide with three example lines.

## 3. Signature transition: the shrink / diorama moment — LOCKED 2026-09-14

Binding constraints (rules 7, 8, 28; SPEC §3.11):
- The one hero animation; it has its own budget. Other UI motion is 150–300 ms, screen transitions 400–600 ms.
- A Reduce Motion equivalent (cross-fade) is required.
- It is the second beat of the store preview and must make the scale relationship obvious.
- Optional iPhone Duo variant (AUTH #003, ticket M3-DUO-02): the physical unfold triggers the same transition, spanning the outer-to-inner display change; one implementation, two triggers; the Reduce Motion variant applies to both.

> **Locked decision text: PENDING TRANSCRIPTION by the Owner (M0-OWNER-02).** Paste: what the camera does, duration, easing, sound, the HUD's state during it, the Reduce Motion variant.

## 4. Avatar presentation — LOCKED 2026-09-14

Binding constraints (rules 15, 16, 20; SPEC §3.2):
- Realistic proportions of about 7 heads, stylized grounded materials, rim light plus contact shadow.
- Likeness confirmation: the head turning beside the source photo, "Is this you?", Retake or Tweak (skin tone, hair, glasses, build); no slider editor.
- Default wardrobe roughly matches the photo; the store appears only after the first win.
- Optional iPhone Duo variant (AUTH #003, ticket M2-DUO-01): tent-posture capture with the rear cameras while the outer display shows framing, countdown, and coaching; the same consent gate and deletion path as the standard flow.

> **Locked decision text: PENDING TRANSCRIPTION by the Owner (M0-OWNER-02).** Paste: the default wardrobe set (names, count), material treatment references, rim and contact values, the confirmation screen layout.

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

## 12. Field notes

(Bots append contradictions and measured values here; the Owner reviews them at each checkpoint.)
