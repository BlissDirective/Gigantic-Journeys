# M0 design system: implementation mockups for the locked decisions 5–10

`design/proposals/M0-design-system-proposal.md` · 2026-09-29 · gj-operator (gj-design hat) · ticket **M0-DSGN-01**

Decisions 1–10 are locked (DESIGN_SYSTEM v0.6, AUTH #004/#005). This document proposes nothing new. It
hands gj-gameplay and gj-platform **pixels instead of prose**: HTML mockups of every locked screen, their
contrast measured over scans, colour-vision simulations, touch-target and safe-zone annotations, and a list of
places where the locked text leaves a gap or conflicts with a later AUTH. Those gaps need a decision; this
document doesn't settle them.

## 1. How to view and re-run

- Open `design/proposals/mockups/index.html` in any browser. Every page takes the same query switches:
  `bg=bright|dark|table` (scan), `surface=glass|flat` (Reduce Transparency twin), `hc=1` (Increase Contrast),
  `cvd=deuteranopia|protanopia|tritanopia`, `annot=1` (touch targets, safe areas, HUD band), `state=…`,
  `img=<frame>` (a real scan frame instead of the stand-in).
- `python design/proposals/mockups/tools/render.py` measures every text and icon element over every scan and
  writes `qa/evidence/M0-DSGN-01/contrast.csv`. `tools/evidence.py` rebuilds the evidence PNGs. Both need
  google-chrome and Pillow. `tools/test_mockups.py` runs in CI without a browser.
- **The three scans are CSS stand-ins.** The Owner's three test scans don't exist yet (M0-OWNER-01 is open).
  Each stand-in is built to stress the scrim:
  - **bright:** blown-out white window, pale walls.
  - **dark:** near-black room with a hot lamp.
  - **table:** saturated clutter with white paper and a black keyboard.

  When the scans exist, run `render.py --scan bright=a.png --scan dark=b.png --scan table=c.png`; that run
  completes AT-2.

## 2. Screen inventory

The mockups use a 1 pt = 1 px coordinate system. The phone is an iPhone 15 Pro (852×393 landscape, safe
insets 59/59/21, Dynamic Island).

| Page | Locked source | What it shows |
|---|---|---|
| `play.html` | §5, §10 | **HUD:** route timer (tabular), vistas sparkle + count, pause.<br>**Controls:** floating 96 pt stick in the left third; 72 pt jump low-right; 56 pt contextual action 24 pt up-left, with an amber availability ring.<br>**States:** run, action, pressed (the only amber fill), time penalty `+0:04`, controller connected (touch hidden). |
| `duo-stand.html` | §5 (M3-DUO-01) | Duo stand mode.<br>**Upper half:** photograph only.<br>**Fold:** 40 pt division.<br>**Lower half:** stick left; jump and action right; diorama overview centred with the timer above it. |
| `capture.html` | §6 (+ AUTH #025 hooks) | **Both modes**, each with an illustration-first toggle chosen before recording.<br>**Elements:**<br>- teal coverage wash, with a hatch option<br>- coverage ring with the percentage<br>- 72 pt record button with the 90 s ring<br>- speed arc: teal, then amber + "Slow down a little"<br>- low-light card with Continue anyway<br>- long-capture warning<br>- missed-corner arrow with Got it / Upload anyway, and Done as the single primary action |
| `create.html` | §7 | **Progress:** blurred cached room with a sharp centre reveal; four-stage determinate bar; estimate; one "what's happening" line; "Journey the demo while you wait".<br>**Other states:** kind failure (Retry / Keep the capture) and the daily-cap queue (never an error). |
| `browse.html` | §8 | 4:5 two-column cards. Each has a diorama thumbnail and a bottom scrim with creator, summits and four labelled five-segment bars.<br>**Also:**<br>- sort tabs, with a Room/Tabletop segment inside Near your scale<br>- "Under review" badge<br>- card back (creator-only stats + report flag)<br>- report reason sheet<br>- four-axis rating sheet with Skip |
| `results.html` | §9 | **Results:** diorama with the flag; centred card with summit time, route this-run/best, vistas (filled vs outline + "2 of 3") and moves with counts; Share primary, Journey again / Next route.<br>**Below the fold:** two SKU cards with inline prices, Restore purchases, sticky Share.<br>**Loss screen:** Keep going only. |
| `consent.html` | §10 | Neutral birth-year age gate; under-13 exit; the scan-privacy screen before the first capture; a scrollable learn-more sheet with a persistent close. All at the large default body size, one primary action each. |
| `settings.html` | §5, §10 | **Accessibility:**<br>- Assist, with the locked copy<br>- Slower time 0.8×<br>- camera shake, haptics<br>- colour filters (deuteranopia/protanopia/tritanopia)<br>- Larger HUD<br>- coverage pattern, summit beam<br>- system-setting note<br>**Controls:** live preview with drag-to-move, 56–96 pt size, opacity, left-handed, Reset. |
| `state-colors.html` | §2, §10 | Every state colour with its non-hue cue, for the CVD sheet. |

Mockup-only choices: all of these are within the lock; values are quoted in `mockups.css`.
- **Text scrims:** 72 % opacity.
- **Control discs:** 60 % (the locked "~60 %").
- **Increase Contrast:** 90 % (locked).
- **Type steps:** 13 / 17 / 20 / 28 / 34 (five steps on the 17 pt body).
- **Radii:** 8 / 14 / 22.
- **Spacing:** the 8 pt grid with a 4 pt half step.

The canonical tokens are M0-DSGN-02's job (`design/tokens/`, a protected path); these values are its input.

## 3. Verification (AT-2, AT-3, AT-4, AT-5)

**Contrast (AT-2, on stand-ins):**
- Coverage: 148 renders (10 pages × states × 3 scans × glass/flat, plus Increase Contrast), **1222 measurements**, **0 failures**.
- Method:
  - Each element's foreground is tested against its nearest painted surface.
  - For translucent scrims, the scrim is composited over the real pixels under the element. For glass, those pixels are Gaussian-blurred (σ 20) first.
  - The minimum over the element box is kept; the 5th percentile is recorded as well.
- Thresholds: text ≥ 4.5:1 (strict, even for large text, per §2), icons and non-text UI ≥ 3:1.
- Tightest cases:
  - Derived muted tokens on their opaque surfaces: 4.52.
  - HUD text on the 72 % glass scrim over the bright scan: 5.78.
  - The play control glyphs on the 60 % disc: 4.12.
- During the pass the checks found and fixed: the amber alert glyph on the cream scrim (1.1:1), teal progress on charcoal (§4 item 3), terracotta tag text (item 4), and three touch targets under 44 pt.

**Colour vision (AT-3):**
- `15-state-colours-cvd.png` shows every state colour under typical vision, deuteranopia, protanopia and tritanopia (Machado 2009, linear RGB).
- `16-deuteranopia-screens.png` shows whole screens under deuteranopia.
- Every state keeps a non-hue cue:
  - pressed = fill plus glyph inversion
  - speed = arc length + words + haptic
  - success/error = shape + word
  - vistas = filled vs outline + count
  - ratings = position + label
- Every glass surface has its flat twin: `03-…`, `17-glass-vs-flat.png`, and `surface=flat` on every page.

**Targets and safe zones (AT-4):**
- `annot=1` draws every tappable element's hit box with its size; a box turns red under 44 pt, or under 56 pt for play controls.
- It also draws the safe area, the 16 pt control inset from the island and corners, and the 8 % HUD band (landscape play).
- Evidence: `02-…` (notched iPhone), `05-…` (Duo), `08-…`, `11-…`, `13-…`.

**Vocabulary (AT-5):**
- A CI test fails if any page's visible text or VoiceOver label says level / map / goal / user.
- Player-facing copy uses environment / journey / summit / route / vista, second person, verbs first.
- The Coordinator still reviews the voice.

## 4. Findings

Findings 1–5 are rules the mockups apply within the lock, and M0-DSGN-02 tokens should carry them.
Findings 6–13 need gj-design or the Owner.

1. **Text needs a denser scrim than controls.**
   - Over any background, paper text on a charcoal scrim reaches 4.5:1 only at ≥ 65 % opacity (ink on cream: ≥ 56 %). At 72 % the worst case is 5.7:1, which leaves room for runtime blending error. The locked "~60 %" disc is right for icons (worst case 3.8:1) but not for text.
   - Proposed tokens: `scrim.text` 0.72, `scrim.disc` 0.60, `scrim.increaseContrast` 0.90.
2. **Muted text never sits over the scan.**
   - The derived muted tokens (`#63676E`, `#90959F`) pass only on opaque surfaces. On a translucent scrim over a scan they fail even at 90 % (worst case 4.1 and 4.0).
   - Rule: muted text only on opaque shell surfaces; over the scan use paper or ink.
3. **Teal needs a keyline on charcoal.**
   - Teal on charcoal is 2.0:1, yet §6 locks the teal progress ring and speed arc, and capture uses the charcoal scrim over bright rooms.
   - The mockups add a 1.5 pt paper keyline to the ring and an ink keyline under the arc, so the shape clears 3:1 while staying teal.
   - The create-flow bar (colour not locked) uses a paper fill on charcoal and teal on cream.
4. **Terracotta can't carry words.** Ink on terracotta is 3.9:1 and paper is 3.7:1. Error states use a terracotta edge and triangle with ink words on cream. Sage is fine with ink words (4.8:1).
5. **Deuteranopia loses the solid coverage wash on dark scans** (`16-…`). Recommendation: turning on any colour filter also turns on the hatch pattern (§10 already offers it, and the settings mockup shows it as its own switch).
6. **Conflict: store copy.** §9 locks "Dress your avatar", but AUTH #020 says v1 copy is "your character". The mockups use **"Dress your character"**.
   - Owner decision: confirm AUTH #020 governs, or file a design-change AUTH to update §9's text.
7. **Obsolete v1 screens.**
   - §7's avatar wait and §10's "biometric consent step" describe the V2 custom avatar (AUTH #020), so they are not mocked.
   - The scan-privacy screen replaces the consent step. Its copy is an engineering draft for legal review.
8. **Gap: orientation.** The lock doesn't say which screens are portrait.
   - The mockups assume play, create wait and results are **landscape**, and capture, browse, settings and consent are **portrait**.
   - Needs a gj-design/Owner call: portrait capture versus the landscape-only game.
9. **Conflict: Larger HUD vs the 8 % band.**
   - The HUD pill is 28 pt inside the 31.4 pt band. §10's Larger HUD (+25 %) makes it 35 pt, which breaks §5's "HUD in the top 8 %".
   - Proposal: Larger HUD may extend the band to 10 %. That would be a design-change AUTH, or it needs a ruling that accessibility settings take precedence.
10. **Pause hit area.** The pause glyph is 28 pt inside the band, with a 44 pt hit area that extends below it; only the visible HUD stays in the top 8 %.
11. **Browse card density.**
    - At 175 pt wide, the 4:5 card's bottom scrim (name, summits, four labelled bars at ≥ 13 pt) covers about 45 % of the thumbnail, and "the place is the title" suffers.
    - Options for gj-design (either would be a design change): move the bars to the card back, or show one combined score on the front.
12. **Duo point size is assumed** (1016×720, about 1.42:1) until Apple publishes it. The fold division is taken as 40 pt, from the simulator observation in `research/duo/README.md`.
13. **Field-note rounding.** §12 lists amber on paper.cream as 1.8:1; it measures 1.75:1. The conclusion (forbidden) doesn't change.

## 5. Handoff

- **gj-gameplay (UI Toolkit, M1):**
  - Build against the pages and the measured values.
  - The runtime scrim picker should choose the scrim with the higher minimum contrast for the region under each HUD element, which is what the `auto` switch models.
- **M0-DSGN-02:** encode §2 plus findings 1–5 as tokens.
- **QA:** AT-2 becomes final once the real scans exist; re-run `render.py --scan …` and replace the CSV.
