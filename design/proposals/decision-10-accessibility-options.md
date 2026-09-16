# Decision 10 — Accessibility baseline: options for the Owner's lock

`design/proposals/decision-10-accessibility-options.md` · 2026-09-16 · Coordinator. Binding constraints (`DESIGN_SYSTEM.md` §10; Design Skills rules 3, 5, 6, 8, 17, 21; Bible §10 assist block: coyote 200 ms, jump bonus 0.2, slips off, auto-grab): assist options, colorblind palettes, Reduce Motion and Reduce Transparency fallbacks, Dynamic Type in the shell, 44 pt targets. Reply `APPROVED: decision 10 = recommended package`, or list the letters that differ; the Coordinator assigns the AUTH number when logging.

## 10a. Assist mode

- **A (recommended). One toggle, no shame.** Assist in Settings and on the pause sheet enables the Bible §10 assist block (longer coyote time, jump bonus, no slips, auto-grab). A separate Slower time toggle runs play at 0.8x. Copy: "Assist makes climbs more forgiving." Leaderboard entries made with Assist are tagged with a small glyph, never excluded (rule 17).
- B. One toggle per assist. More control, more settings to explain.

## 10b. Colorblind support

- **A (recommended).** State is never carried by hue alone (rule 21): the four-axis rating bars use position and label; capture coverage adds a hatch pattern option to the teal wash; sage and terracotta states carry a shape and a word. A palette switch for deuteranopia, protanopia, and tritanopia remaps the few state colors; the amber accent is checked in all three simulations.
- B. Rely on iOS system filters only. Free, and it recolors the photograph too.

## 10c. Motion and transparency

- **A (recommended).** Reduce Motion: cross-fades everywhere; the signature transition per decision 3's Reduce Motion variant. Reduce Transparency: every glass surface becomes its flat twin (rule 3). Increase Contrast: scrim opacity rises to 90 % and outlines thicken. All three read from the system settings with no in-app duplicates.

## 10d. Text

- **A (recommended).** Dynamic Type in the shell (browse, settings, results, consent) up to the largest accessibility size with layout reflow (rule 5); HUD sizes stay fixed for the 30 fps overlay budget, with a Larger HUD toggle (+25 %) in Settings.
- B. Dynamic Type everywhere, including the HUD. Correct in spirit, breaks the top-8 % rule at large sizes.

## 10e. Controls and screen readers

- **A (recommended).** Controls repositionable and resizable with a left-handed mirror (decision 5). VoiceOver labels on every shell screen and on the HUD's three elements; controller support (decision 5f) doubles as switch access. A haptics toggle. Play requires a touch or a controller; no voice control in v1.

## 10f. Photosensitivity and sound

- **A (recommended).** Nothing flashes above 3 Hz; the beam ignition and the vista lens flare are single, slow events. Every sound cue has a visual twin (rule 17), so muted play loses nothing. Camera shake has its own toggle.

## 10g. Age and consent screens

- **A (recommended).** The 13+ gate and the biometric consent step use the largest body size by default, plain sentences, and a single primary action per screen; the "learn more" sheet is scrollable with a persistent close (SECURITY_CHECKLIST §5.2).

## Recommended package

10a-A, 10b-A, 10c-A, 10d-A, 10e-A, 10f-A, 10g-A.
