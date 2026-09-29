# M0-DSGN-01: implementation mockups and verification (QA pass)

2026-09-29, gj-operator: gj-design hat for the build, then the gj-qa-release hat per `qa/VISUAL_QA.md`.
The work was committed directly to `main` (Operator precedent), so this file carries the QA verdict.

## What was built
- **Mockups:** `design/proposals/mockups/` contains ten HTML pages (play, duo-stand, capture, create, browse,
  results, consent, settings, state-colors, index). They share `mockups.css`, which holds the locked §2 palette,
  the derived tokens and the mockup-local scale, and `mockups.js`, which handles the query switches for scan,
  surface, Increase Contrast, CVD simulation, annotations and state, plus the measurement export.
- **Tools:**
  - `tools/contrast.py`: WCAG maths, the palette, and the Machado CVD matrices.
  - `tools/render.py`: per-pixel contrast over the scans; writes `contrast.csv`.
  - `tools/evidence.py`: builds the contact sheets.
  - `tools/test_mockups.py`: 24 CI tests.
- **Proposal:** `design/proposals/M0-design-system-proposal.md` covers the inventory, method, 13 findings and the handoff.

## Acceptance tests
| AT | Level | Verdict | Evidence |
|---|---|---|---|
| AT-1 mockups for every listed screen, faithful to §5–§10 | required | **Met (pending Coordinator review)** | Pages and PNGs 01–14. The v1 exceptions are documented (no avatar wait or biometric step under AUTH #020; "Dress your character"). |
| AT-2 each screen on the three test scans, with measured contrast | required | **Partly met.** Measured on CSS stand-ins; 1222 measurements, 0 failures. **The real three test scans don't exist yet** (M0-OWNER-01). | `contrast.csv`; `render.py --scan …` is ready for them. |
| AT-3 deuteranopia for every state colour; flat twin for every glass surface | suggested | **Met** | PNGs 03, 15, 16, 17; `surface=flat` on every page |
| AT-4 targets annotated (≥ 44 / play ≥ 56); safe zones on a notched device and the Duo | required | **Met** | PNGs 02, 05, 08, 11, 13. Every hit box is sized in pt; undersized boxes render red. The renderer also fails the CSV on any undersized target (three were found and fixed). |
| AT-5 decision-2 vocabulary | required | **Met mechanically; the Coordinator reviews the voice** | `test_copy_follows_decision_2_vocabulary` (10 pages, visible text + VoiceOver labels) |

## Checks run
- `pytest design/proposals/mockups/tools/test_mockups.py`: 24 passed.
  - Covers: the WCAG reference values; the §12 field-note values reproduced; the palette equal to DESIGN_SYSTEM §2
    and `mockups.css`; scrim opacities that hold over any background; CSV coverage (every page; every scan ×
    surface for the over-scan pages; auto scrim charcoal on bright and cream on dark); no failures; vocabulary.
- `render.py`: 148 renders, 1222 measurements, 0 failures.
  - Tightest results: muted tokens on their opaque surfaces 4.52; HUD text on the 72 % glass scrim over the bright
    scan 5.78; control glyphs on the 60 % discs 4.12.
- Visual review of every contact sheet at full size. Issues found and fixed during review:
  - capture toggle segments at 38 pt;
  - the missed-corner "Done" overlapping the record ring;
  - wrapping button labels on the results card;
  - teal bars invisible on charcoal;
  - terracotta tag text;
  - a JS state-toggle bug that cleared inline `display: flex`;
  - a sub-44 pt palette segment.

## Open items (for the Coordinator and Owner; details in the proposal §4)
- **Real scans (AT-2):** re-run `render.py --scan …` once the Owner's three test scans exist.
- **Owner decisions:**
  - "Dress your avatar" (§9) vs "your character" (AUTH #020).
  - Screen orientation (portrait capture and shell?).
  - Larger HUD (+25 %) vs the 8 % HUD band.
  - Browse-card density.
- **Tokens for M0-DSGN-02:** `scrim.text` 0.72, `scrim.disc` 0.60, `scrim.increaseContrast` 0.90. Rules: no muted text over the scan; teal keyline on charcoal; terracotta never carries words; hatch coverage when a colour filter is on.

**Verdict:** ready for Coordinator review of AT-1, AT-4 and AT-5. AT-2 stays open until the real scans exist, so the ticket is
**blocked** on M0-OWNER-01 for AT-2 alone.
