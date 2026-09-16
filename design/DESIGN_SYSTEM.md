# Gigantic Journeys — Design System

`design/DESIGN_SYSTEM.md` · v0.6 · 2026-09-16 · Status: **LOCKED except by AUTH REQUEST (design-change)**

The Owner locks; `gj-design` implements (tokens in `design/tokens/`, Unity UI Toolkit in `unity/Assets/UI`); every UI and gameplay PR is reviewed against this file (REVIEW_RUBRIC §G). Binding constraints come from `Gigantic-Journey-Design-Skills.md` §3 (v1.1), which this file specializes and never contradicts. CI blocks PRs that edit this file without an `APPROVED #n`; appending under §12 Field notes is allowed.

## 0. How to read this file

Decisions 1–4 were **locked by the Owner in the design session of 2026-09-14** and transcribed by the Owner on 2026-09-16 (ticket M0-OWNER-02). Each section carries the binding constraints from the Design Skills, the locked decision text, and a Coordinator consistency note. The locked text changes only by AUTH. Decision 3 was amended on 2026-09-16 (AUTH #004) with five adopted Coordinator recommendations.

Decisions 5–10 were locked by the Owner on 2026-09-16 (AUTH #005), each choosing the recommended package from its option set under `design/proposals/`. All ten decisions are now locked; changes need an AUTH. `gj-design` implements them (tokens in `design/tokens/`, mockups and Unity UI Toolkit); the option docs hold the rationale behind each choice.

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

## 5. Play layout — LOCKED 2026-09-16 (AUTH #005)


Binding constraints: two-thumb landscape; floating stick anywhere in the left third; jump is the largest right-thumb target; one contextual action button that appears only when relevant; controls repositionable and resizable; play controls ≥ 56; HUD in the top 8 %; controller support from day one; camera per Bible §8; optional iPhone Duo variants: the 7.6-inch near-square inner display and a stand-mode layout with the photograph on the upper half and every control on the lower half (`design/proposals/iphone-duo-track.md`, AUTH #003).

**Locked decision (Owner, 2026-09-16; recommended package from `design/proposals/decision-5-play-layout-options.md`):**
- Right-thumb cluster: a 72 pt jump pad low-right where the thumb rests; the contextual action appears 24 pt up and to the left only when a verb is available (Bible §3.5); dragging elsewhere on the right half orbits the camera.
- Left stick: floating, under the first touch anywhere in the left third, 96 pt base, Bible §3.1 thresholds (walk < 40 %, run > 85 %), hides after 1 s idle; sprint by holding run 1.5 s or double-tap, no extra button.
- HUD (standard): a route timer in tabular figures at the left, shown only while a route is active; vistas found as a sparkle glyph with a count; pause at the top right; nothing else. The beam carries summit orientation, never the HUD.
- Camera: Bible §8 as written (follow 4 A, height 1.6 A, look-ahead 0.8 A, run FOV +4°, collision-aware dither-fade, manual orbit recentering after 2 s), base vertical FOV 60°, with +0.2 A height and +5° over a typical platformer. Every value lives in a camera section of `config/movement.json`, added by AUTH when M1 introduces it, and tuned by M1 telemetry.
- Customization: Settings › Controls with drag-to-reposition, a 56–96 pt size slider, a left-handed mirror, an opacity slider, and Reset; changes preview live on the demo scan.
- Controller (day one): left stick move, right stick orbit, A/✕ jump, X/□ action, B/○ drop, Options pause, a shoulder button opens photo mode at a vista; touch controls hide 0.5 s after a controller connects and return on the next touch.
- Styling: neutral scrim discs (charcoal or cream per scan, ~60 % opacity, 1 pt outline); the pressed state and the action button's availability pulse are the only amber; icons in ink or paper at ≥ 3:1; glass and flat variants both defined.
- Safe zones and iPhone Duo: controls inset 16 pt from the rounded corners and the Dynamic Island in either landscape orientation; the HUD never overlaps the island. Duo stand mode (M3-DUO-01): upper half photograph only, lower half stick at left, jump and action at right, the diorama overview centered, the timer above it. Duo open flat: the standard layout on the 7.6-inch display with the stick zone widened to the left 40 %.


## 6. Capture coaching UI — LOCKED 2026-09-16 (AUTH #005)


Binding constraints: coach steady motion, overlap, angles, light; live coverage heat-map; speed meter turning amber; blur rejection with a haptic; "you missed this corner"; two scripts (room walkthrough, tabletop orbital) chosen by one illustrated toggle; reject early and kindly; no text-only instructions.

**Locked decision (Owner, 2026-09-16; recommended package from `design/proposals/decision-6-capture-coaching-options.md`):**
- Coverage: a translucent teal wash accumulates on the live camera view over captured surfaces (AR-anchored); uncovered areas stay unpainted; a coverage ring shows the percentage top-right. The room itself is the map of what is missing.
- Speed: a thin arc under the record button fills teal at a good pace and turns amber with one gentle haptic when the phone moves too fast; "Slow down a little" appears after a full second of amber, then fades.
- Blur and low light: blur is one soft haptic tick and a single amber edge pulse, no words; low light shows one card, "Too dark here. Turn on a lamp?", with Continue anyway. Capture never hard-stops.
- Mode toggle: a two-segment toggle above the record button with looping line illustrations (Room: an arc at chest height; Tabletop: a slow circle at two heights), chosen before recording, remembered, never in settings.
- Missed corner: before upload, a 3D arrow anchored in the live view points at the largest unpainted region with "You missed this corner," offering Got it (keep recording) or Upload anyway.
- Progress and timing: a ring around the record button fills over 90 s as a target, not a limit; past three minutes it turns amber with "Long captures rebuild worse"; the coverage percentage sits inside the ring; Done appears at 60 % coverage or 60 s, whichever comes first.
- Primary action and states: one 72 pt record button (neutral at rest, teal while recording, Done afterward as the single primary action); a 5 s preview before upload with Retake.


## 7. Create-flow waiting states — LOCKED 2026-09-16 (AUTH #005)


Binding constraints: progress on every wait over 1 s; determinate progress plus something to look at over 10 s; the splat resolves progressively; a "what's happening" explainer; never a blank spinner.

**Locked decision (Owner, 2026-09-16; recommended package from `design/proposals/decision-7-create-flow-options.md`):**
- Reconstruction wait: the backdrop is the cached blurred room; the sharp splat resolves progressively from the center as chunks arrive; a determinate four-stage bar (Uploading · Rebuilding your environment · Finding the summit · Choosing routes) with one "what's happening" line; it flows straight into the signature transition.
- Avatar wait: the captured full-body silhouette turns and fills from wireframe to textured across stages (Reading your photos · Building your head · Fitting your body · Dressing you), ending on the likeness confirmation with no screen in between.
- Background continuation: both waits can run in the background via a Live Activity; the player can journey the demo environment or browse; a notification says "Your <environment> is ready."
- Estimates: "About N minutes" from the rolling median of recent jobs, updated as stages complete; under 10 s remaining the estimate disappears and the bar simply finishes; the bar never stalls at the end.
- Failure states: kind, specific, actionable copy in the decision-2 voice ("This capture was too dark to rebuild. Try again with the lamps on?") with Retry and Keep the capture; error codes go to the report, never the screen.
- Cost guard: at the daily cap, "We are rebuilding a lot of places today. Yours is queued and will be ready by <time>." and the job resumes automatically; the cap is never shown as an error.


## 8. Browse and ranking cards — LOCKED 2026-09-16 (AUTH #005)


Binding constraints: browse by place, thumbnails are the room; sort tabs Top this week, New, Near your scale; one-tap four-axis rating; one-tap report with a reason sheet; creator stats visible; "Under review" badge.

**Locked decision (Owner, 2026-09-16; recommended package from `design/proposals/decision-8-browse-options.md`):**
- Card: a full-bleed diorama thumbnail on a 4:5 card in a two-column grid; a bottom scrim carries the creator's name, the number of summits reached, and the four-axis score as four short bars. No title is required; the place is the title.
- Sort tabs: Top this week · New · Near your scale (a Room/Tabletop segment inside the tab). Friends arrives with social features later.
- Rating: after a summit or on leaving an environment, one sheet with four five-segment rows (fun, interesting, interactive, exciting) rated by tap; Skip is always visible; the sheet never blocks Share.
- Report: a flag on the card back and in the pause sheet opens a reason sheet (private information visible · inappropriate content · not a real place · broken environment · other); "Under review" shows immediately.
- Creator stats: plays, summits, best time per route, and ratings on the card back (tap to flip) and a profile page; visible to the creator only in v1.
- Deep links: an environment link opens its card with one primary action, Journey; if the app is not installed, the App Store page with the diorama thumbnail; the link carries no location data.
- Moderation visibility: environments awaiting the vision pass show an "Under review" badge and are playable only by their creator until cleared; a rejection tells the creator why in one line with an appeal action.


## 9. Results and store screens — LOCKED 2026-09-16 (AUTH #005)


Binding constraints: one primary action ("Share"); the store after a win, never on a loss; two SKUs with clear prices; one-tap restore; no fake scarcity; the results screen carries the detail the HUD omits.

**Locked decision (Owner, 2026-09-16; recommended package from `design/proposals/decision-9-results-and-store-options.md`):**
- Results layout: the backdrop is the reverse signature transition ending on the diorama with the flag visible; a centered card carries the summit time, each route's time (this run and best), vistas found as three sparkles, and the moves used with counts; primary action Share, secondary Journey again and Next route; after the first summit of an environment the rating sheet slides up once Share has been offered.
- Share format: a six-second vertical clip (2 s of the reverse transition, then 4 s of the auto-picked best moment), the wordmark small at the bottom right, no HUD or controls; a flag-frame still ships alongside.
- Store placement: on the results screen after a summit only, below the fold, a "Dress your avatar" card and a "Realism+" card with inline prices, each previewed on the player's own avatar in the diorama; Restore purchases is one tap here and in Settings; never after a fall or quit, never before the first summit of the account, never covering Share.
- Store copy and rules: verbs first ("Dress your avatar", "Sharpen the look"); local prices from StoreKit; no timers, badges, countdowns, or "limited" language; purchases apply immediately in the preview; Family Sharing and restore work on day one.
- Failure and loss screens: the diorama with the avatar at the last stable surface and one primary action, Keep going; store, ratings, and share are absent; a time penalty shows as a small "+0:04" next to the timer, never a red banner.


## 10. Accessibility baseline — LOCKED 2026-09-16 (AUTH #005)


Binding constraints: assist options (Bible §10 assist block), colorblind palettes, Reduce Motion and Reduce Transparency fallbacks, Dynamic Type in the shell, 44 pt / 48 dp targets.

**Locked decision (Owner, 2026-09-16; recommended package from `design/proposals/decision-10-accessibility-options.md`):**
- Assist mode: one Assist toggle (Settings and pause) enabling the Bible §10 assist block (longer coyote time, jump bonus, no slips, auto-grab), plus a separate Slower time toggle at 0.8x; copy "Assist makes climbs more forgiving"; leaderboard entries made with Assist are tagged with a small glyph, never excluded.
- Colorblind support: state is never carried by hue alone (rating bars use position and label; the coverage wash offers a hatch pattern; sage and terracotta states carry a shape and a word); a palette switch for deuteranopia, protanopia, and tritanopia remaps state colors; the amber accent is checked in all three simulations.
- Motion and transparency: Reduce Motion gives cross-fades everywhere plus decision 3's Reduce Motion variant; Reduce Transparency swaps every glass surface for its flat twin; Increase Contrast raises scrim opacity to 90 % and thickens outlines; all three read from the system settings.
- Text: Dynamic Type in the shell (browse, settings, results, consent) up to the largest accessibility size with reflow; HUD sizes stay fixed for the overlay budget, with a Larger HUD toggle (+25 %) in Settings.
- Controls and screen readers: controls repositionable and resizable with a left-handed mirror; VoiceOver labels on every shell screen and the three HUD elements; controller support doubles as switch access; a haptics toggle; no voice control in v1.
- Photosensitivity and sound: nothing flashes above 3 Hz; the beam ignition and the vista lens flare are single slow events; every sound cue has a visual twin; camera shake has its own toggle.
- Age and consent screens: the 13+ gate and the biometric consent step use the largest body size by default, plain sentences, and one primary action per screen; the "learn more" sheet is scrollable with a persistent close.


## 11. Change log

| Version | Date | Change | Authorization |
|---|---|---|---|
| 0.1 | 2026-09-15 | File created; decisions 1–4 recorded as locked with their binding constraints, text pending transcription; 5–10 open | AUTH #000 |
| 0.2 | 2026-09-15 | §5 gains the optional iPhone Duo layout variants | AUTH #003 |
| 0.3 | 2026-09-15 | §3 and §4 gain the optional iPhone Duo variants for the Owner's selected features | AUTH #003 (Owner selection) |
| 0.4 | 2026-09-16 | Decisions 1–4 transcribed from the Owner's 2026-09-14 lock; consistency notes and palette contrast measurements added; §5 vocabulary fix (diorama overview) | Transcription, M0-OWNER-02 (no AUTH consumed) |
| 0.5 | 2026-09-16 | §3 amended with the five adopted Coordinator recommendations (scale anchor, summit last, sound and haptics, short form on return, reverse transition as results backdrop) | AUTH #004 |
| 0.6 | 2026-09-16 | Decisions 5–10 locked (play layout, capture coaching, create-flow waits, browse cards, results and store, accessibility), each the recommended package | AUTH #005 |

## 12. Field notes

(Bots append contradictions and measured values here; the Owner reviews them at each checkpoint.)

- 2026-09-16 (Coordinator): WCAG 2.x contrast of the decision 2 palette. Pass for body text (≥ 4.5:1): ink.charcoal on paper.cream 14.4, ink.charcoal on surface.cream 13.2, paper.cream on ink.charcoal 14.4, paper.cream on surface.charcoal 11.9, accent.amber on ink.charcoal 8.3, accent.amber on surface.charcoal 6.8, accent.amberLight on ink.charcoal 11.6, ink.charcoal on accent.amber 8.3, semantic.teal on paper.cream 7.2, paper.cream on semantic.teal 7.2, text.muted on ink.charcoal 5.1, semantic.sage on ink.charcoal 4.8. UI or large text only (3:1 to 4.5:1): text.muted on surface.charcoal 4.2, semantic.terracotta on ink.charcoal 3.9, semantic.terracotta on paper.cream 3.7, paper.cream on semantic.terracotta 3.7, semantic.sage on paper.cream 3.0. Fail (< 3:1): text.muted on paper.cream 2.8, text.muted on surface.cream 2.6, semantic.teal on ink.charcoal 2.0, accent.amber on paper.cream 1.8 (already forbidden by the rule). Derived tokens that pass: muted-on-cream `#63676E` (4.5:1 on surface.cream), muted-on-charcoal `#90959F` (4.5:1 on surface.charcoal).
