# Decision 5 — Play layout: options for the Owner's lock

`design/proposals/decision-5-play-layout-options.md` · 2026-09-16 · Coordinator. Binding constraints are in `DESIGN_SYSTEM.md` §5 (two-thumb landscape; floating stick in the left third; jump the largest right-thumb target; one contextual action; repositionable and resizable; play controls ≥ 56 pt; HUD in the top 8 %; controller support from day one; camera per Bible §8; iPhone Duo variants). Pick one option per question. Reply `APPROVED #004: decision 5 = recommended package`, or list the letters that differ. The Coordinator then writes §5 and `gj-design` implements.

## 5a. Right-thumb cluster

- **A (recommended). Jump pad low-right, action above-left of it.** Jump is a 72 pt pad where the right thumb naturally rests; the contextual action appears 24 pt up and to the left only when a verb is available (Bible §3.5), so the thumb rolls to it without lifting. Camera orbit: drag anywhere else on the right half (Bible §8).
- B. Action to the left of jump on the same baseline (classic two-button row). Simpler, but the thumb travels farther and the row eats width in Duo stand mode.
- C. Jump anywhere on the right half (tap jumps, drag orbits), action as one floating button. Fewest elements, but tap-versus-drag ambiguity costs precision jumps.

## 5b. Left stick

- **A (recommended). Floating stick.** Appears under the first touch anywhere in the left third, 96 pt base, thresholds per Bible §3.1 (walk under 40 %, run over 85 %), hides after 1 s idle. Sprint by holding run 1.5 s or double-tap, no extra button.
- B. Fixed stick at a set position (repositionable). Predictable, but forces one grip.

## 5c. HUD content (top 8 %)

- **A (recommended, "standard").** Route timer (tabular figures, only while a route is active) at the left; vistas found as a sparkle glyph with a count (for example 2 of 3) beside it; pause at the top right. Nothing else. Summit orientation is the beam, never a HUD element.
- B ("minimal"). Pause only; the timer appears on route start and hides after 3 s unless tapped.
- C ("rich"). A plus summit distance in A units and the current route's beat. Rule 21 argues against it; listed in case the Owner wants it.

## 5d. Camera defaults

- **A (recommended). Bible §8 as written** (follow 4 A, height 1.6 A, look-ahead 0.8 A, run FOV +4 degrees, collision-aware dither-fade, manual orbit that recenters after 2 s), with a base vertical FOV of 60 degrees and rule 19's "slightly higher, wider" bias as +0.2 A height and +5 degrees over a typical platformer. Every value lives in a camera section of `config/movement.json` so M1 telemetry tunes it by AUTH.
- B. Tighter: 55 degrees, follow 3.5 A. More cinematic, worse in tight rooms.

## 5e. Control customization

- **A (recommended).** Settings › Controls: drag to reposition, size slider 56 to 96 pt, left-handed mirror toggle, opacity slider, Reset. Changes preview live on the demo scan.
- B. Presets only (default, mirrored, large). Less to build, less accessible.

## 5f. Controller mapping (day one)

- **A (recommended).** Left stick move, right stick orbit, A or cross jump, X or square action, B or circle drop, Options pause, a shoulder button opens photo mode at a vista. Touch controls hide 0.5 s after a controller connects and return on the next touch.

## 5g. Control styling (from decision 2)

- **A (recommended).** Neutral scrim discs (charcoal or cream per scan at about 60 % opacity, 1 pt outline); the pressed state and the action button's availability pulse are the only amber; icons in ink or paper at 3:1 or better. Glass and flat variants both defined.
- B. Amber outlines on every control. Breaks the 10 % amber rule on small screens.

## 5h. Safe zones and iPhone Duo

- **A (recommended).** Controls inset 16 pt from the rounded corners and the Dynamic Island in either landscape orientation; the HUD strip never overlaps the island. Duo stand mode (ticket M3-DUO-01): upper half photograph only; lower half has the stick at left, jump and action at right, the diorama overview (the summit, route, and vista markers at diorama scale) in the center, and the timer above it. Duo open flat: the standard layout on the 7.6-inch display with the stick zone widened to the left 40 %.

## Recommended package

5a-A, 5b-A, 5c-A, 5d-A, 5e-A, 5f-A, 5g-A, 5h-A.
