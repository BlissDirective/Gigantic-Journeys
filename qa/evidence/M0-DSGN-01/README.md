# M0-DSGN-01 evidence: implementation mockups for DESIGN_SYSTEM §5–§10

Captured 2026-09-29, around 00:00 CT, by gj-operator using `python design/proposals/mockups/tools/evidence.py`.
The renders are headless Chrome (google-chrome, `--force-device-scale-factor` 2, or 1 for wide contact sheets) of
the HTML mockups in `design/proposals/mockups/`. The QA verdict is in `qa/reports/M0-DSGN-01.md`; the design
notes and findings are in `design/proposals/M0-design-system-proposal.md`.

**Privacy:** there's no personal data. The scans behind the UI are CSS-drawn stand-ins (no photos, no captures).
Creator names and times are invented.

**Stand-in scans:** until the Owner's three test scans exist (M0-OWNER-01), `bright`, `dark` and `table` are CSS
stand-ins built to stress the scrim:
- `bright`: a blown-out white window.
- `dark`: near-black with a hot lamp.
- `table`: saturated clutter.

Re-run with `render.py --scan bright=… --scan dark=… --scan table=…` on the real scans.

| File | Shows | AT |
|---|---|---|
| `01-play-hud-three-scans.png` | Play HUD and controls on the three scans; auto scrim (charcoal on bright and table, cream on dark) | AT-1, AT-2 |
| `02-play-annotated-safe-zones.png` | iPhone 15 Pro landscape overlays:<br>- touch targets (magenta, with pt size)<br>- safe area (yellow)<br>- 16 pt control inset from the island and corners (green)<br>- HUD band, top 8 % = 31.4 pt (cyan) | AT-4 |
| `03-play-glass-flat-contrast.png` | Glass, flat twin (Reduce Transparency), Increase Contrast (90 %) | AT-3 |
| `04-play-states.png` | Run; jump pressed (the only amber fill); `+0:04` penalty; controller connected | AT-1 |
| `05-duo-stand-annotated.png` | iPhone Duo stand mode with the fold division (point size assumed) | AT-1, AT-4 |
| `06-capture-room-states.png` | Room capture: pre (mode toggle), recording, too fast, low light, long, missed corner | AT-1 |
| `07-capture-tabletop-dark.png` | Tabletop capture on the dark scan (cream scrim); hatch coverage option | AT-1, AT-3 |
| `08-capture-annotated.png` | Capture targets and safe area (portrait) | AT-4 |
| `09-create-wait-states.png` | Reconstruction wait; failure; daily-cap queue | AT-1 |
| `10-browse-states.png` | Grid; Near your scale; card back; report sheet; rating sheet | AT-1 |
| `11-browse-annotated.png` | Browse and rating targets | AT-4 |
| `12-results-store-loss.png` | Results (Share primary); store below the fold; loss (Keep going only) | AT-1 |
| `13-consent-age-gate.png` | Age gate; under 13; scan privacy; learn-more sheet (annotated) | AT-1, AT-4 |
| `14-settings-accessibility-controls.png` | Settings: Accessibility and Controls (live preview) | AT-1 |
| `15-state-colours-cvd.png` | Every state colour under typical vision, deuteranopia, protanopia, tritanopia | AT-3 |
| `16-deuteranopia-screens.png` | Whole screens under deuteranopia; solid vs hatch coverage wash | AT-3 |
| `17-glass-vs-flat.png` | Glass and flat twins of two panel surfaces | AT-3 |
| `contrast.csv` | 1222 measurements (148 renders), one row per element × state × scan × surface.<br>Columns: min and 5th-percentile ratio, threshold, pass. **0 failures.** | AT-2 |
