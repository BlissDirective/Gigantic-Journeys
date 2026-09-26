# gj-design — Working Handbook

Remit: execute the locked design system across every app screen: onboarding, capture coaching, create-flow waits, play HUD, results and store, browse, publish, settings and consent. The hat also covers store screenshots, the preview-video storyboard and brand assets. Mockups (Figma or HTML) come first, then the Unity UI Toolkit implementation with the gameplay hat (kit §3.6 role block; `agents/grok/roles/gj-design.md`). Re-read this file at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3, §9).

Executing agent: the **Builder** does tokens, USS/UXML and scripts. The **Operator** does computer-use work: mockup captures on the three test scans, simulator/device screenshots, store-asset drafts (`AGENT_GOVERNANCE.md` §2). Owned paths: `design/` and `unity/Assets/UI/`. `design/DESIGN_SYSTEM.md`, the locked design docs and `design/tokens/` are **protected paths**: `.github/scripts/auth_gate.py` fails any PR that touches them without `APPROVED #n`. You **execute** the system; you don't redraw it. Put alternatives in `design/proposals/`.

Research list: `projects/skills/design/RESOURCES.md` (102 link-checked entries).

## 1. Rules this hat must follow

| Rule | Source |
|---|---|
| Session start, branches, PR template, screenshots/clips for anything visual | `agents/grok/README.md` §3–§5 |
| AUTH before changing the design system, tokens, locked docs or SPEC | `agents/grok/README.md` §6; `auth_gate.py`; DESIGN_SYSTEM §0, §11 |
| iOS-only v1; tests/QA/perf are suggestions, only CI + security rules gate merges | `agents/grok/README.md` §0; SPEC §11; Design Skills field note 2026-09-15 |
| Tokens only, no literal values in USS/UXML | REVIEW_RUBRIC G1 |
| Contrast on three test scans: text ≥ 4.5:1, icons ≥ 3:1, scrim applied | REVIEW_RUBRIC G2; Design Skills rule 1 (§3.1); DESIGN_SYSTEM decision 2 |
| Glass + flat twin for every surface; Reduce Motion twin for every animation | REVIEW_RUBRIC G3; Design Skills rules 3, 8 (§3.1, §3.3); decision 10 |
| Targets ≥ 44 pt, play controls ≥ 56, safe zones, one primary action | REVIEW_RUBRIC G4; Design Skills rules 4, 6 (§3.2) |
| No text-only instructions; waits > 1 s show progress, > 10 s determinate + content | REVIEW_RUBRIC G5; Design Skills rules 11, 12 (§3.4, §3.5); decision 7 |
| Only the locked non-photo element language; nothing new in the play viewport without an ADR | REVIEW_RUBRIC G6; Design Skills rules 2, 21 (§3.1, §3.8); decision 1 |
| Voice: short, warm, verbs first; environment / journey / summit / route / vista | REVIEW_RUBRIC G7; decision 2 |
| Signature transition and avatar presentation per decisions 3 and 4 | REVIEW_RUBRIC G8; Design Skills rules 7, 28 |
| No full-screen blur in play; HUD in one overlay pass within the top 8 % | REVIEW_RUBRIC D5; Design Skills rules 21, 27 (§3.8, §3.12) |
| Camera, HUD and controls follow the Bible (stick thresholds, camera constants, assist block) | Movement Bible §3.1, §3.5, §8, §10; decision 5 |
| Permissions in context; consent a separate explicit step, never bundled | Design Skills rule 10 (§3.4); SECURITY_CHECKLIST §5 |
| One-tap report with a reason sheet, "Under review" visible, block available (Apple 1.2) | Design Skills rules 24, 25 (§3.10); decision 8; SECURITY_CHECKLIST §10.4, §10.5 |
| Store after a win only, cosmetic-only, no timers or fake scarcity | Design Skills rule 26 (§3.11); decision 9 |
| No real user media in fixtures, mockups or store assets without the Owner's say-so | SECURITY_CHECKLIST §6.5; REVIEW_RUBRIC F3 |

## 2. Token-first design system

- **Source of truth:** DESIGN_SYSTEM decisions 1–10, all LOCKED (decisions 1–4 transcribed 2026-09-16; decision 3 amended by AUTH #004; decisions 5–10 locked by AUTH #005; v0.6 in §11).
- **Tokens don't exist yet.** `design/tokens/` and `unity/Assets/UI/` aren't in the repo. **M0-DSGN-02 (open)** creates them:
  - `design/tokens/tokens.json` in DTCG format (AT-1), with groups: color (roles, light and dark scrim), typography (≤ 5 steps, tabular HUD numerals), spacing (8 pt grid, 4 pt half step), radius, elevation, and motion (150–300 ms UI, 400–600 ms transitions, the shrink transition's own budget).
  - `design/tokens/export_uss.py` generates `unity/Assets/UI/Tokens.uss` deterministically (AT-2). A golden-file test is suggested.
  - A CI contrast test: every text token on the three scans' scrims meets 4.5:1, icons 3:1 (AT-3).
  - Values match the decisions verbatim, and the PR cites v0.6+ (AT-4). The PR needs `APPROVED #n` because `design/tokens/` is protected.
- **Palette (decision 2, verbatim):**
  - accent: `accent.amber` #F2A93B, `accent.amberLight` #FFD27A.
  - neutrals: `ink.charcoal` #1C1F26, `surface.charcoal` #2A2E37, `paper.cream` #F5EFE6, `surface.cream` #EDE5D8, `text.muted` #8A8F99.
  - semantic: `semantic.teal` #00585E (capture state and progress only), `semantic.sage` #7A8F7B, `semantic.terracotta` #C9573D.
- **Derived tokens** (decision 2 consistency note; full table in §12): these fix the measured failures without touching the locked palette.
  - Muted text on cream surfaces: `#63676E` (reaches 4.5:1 on surface.cream), or `text.muted` only at ≥ 18 pt.
  - Muted text on charcoal: `#90959F`.
  - Sage, terracotta and teal are fills and icons, never body text. Teal fails on charcoal (2.0:1), so keep it off charcoal.
- **Layering:** primitive tokens (hex, pt, ms) → semantic role tokens (`text.primary.onScrimDark`, `surface.glass`, `surface.flat`) → component tokens. Components reference roles only, so Reduce Transparency and Increase Contrast become token swaps rather than code branches.
- **Type:** 5 steps maximum on 17 pt iOS body; HUD numerals tabular; line length 45–75 characters (rule 5). Dynamic Type applies in the shell only. The HUD stays fixed, with a Larger HUD +25 % toggle (decision 10).
- **Spacing:** 8 pt grid with a 4 pt half step (rule 6).

## 3. Contrast over photo backgrounds

- **Every scan is an unknown full-colour background** (rule 1). Never assume a palette gives contrast. Text and controls always sit on a scrim.
- **Scrim picking per scan** (decision 2): charcoal scrim over bright rooms, cream scrim over dark rooms.
  - Choose from the luminance of the region behind the element (a downsampled sample of the cached blurred room or thumbnail), not the whole frame.
  - Compute contrast at runtime against the worst-case sample under the element (a Leonardo-style approach; see RESOURCES §D).
  - Increase Contrast raises scrim opacity to 90 % and thickens outlines (decision 10).
- **Ratios:** WCAG 2.2 SC 1.4.3 (text 4.5:1; large text ≥ 18 pt or 14 pt bold at 3:1) and SC 1.4.11 (icons and UI boundaries 3:1).
- **Amber** stays under 10 % of any screen, and is never body text on cream (decision 2). In play, amber is only the pressed state and the action button's availability pulse (decision 5).
- **Colour independence:** state is never carried by hue alone (rule 21; decision 10).
  - Rating bars use position and a label.
  - The coverage wash offers a hatch pattern.
  - Sage and terracotta states carry a shape and a word.
  - A palette switch remaps state colours for deuteranopia, protanopia and tritanopia. Check amber in all three simulations.
- **Test scans:** bright room, dark room, cluttered tabletop (Design Skills §4; M0-DSGN-01). Which corpus scans are "the three" is **TBD until M0-DSGN-01 lands its mockups** in `design/proposals/mockups/`. Use the Owner's corpus only; never scan real people's homes for fixtures (§6.5).

## 4. Glass + flat surfaces

- **Each surface is defined twice**, glass and flat (rule 3; decision 2). The glass version follows the platform material for the app shell only.
- **The flat twin is an opaque scrim-coloured fill with the same geometry and a 1 pt outline.** It ships for Reduce Transparency, Increase Contrast and the iOS transparency intensity setting (decision 10). Read the flags from the system; never offer only an in-app copy of them.
- **No live full-screen blur in play** (rule 27; REVIEW_RUBRIC D5). The signature transition's blurred backdrop is a low-res splat render **blurred once and cached** (decision 3), and the create-flow wait uses the cached blurred room too (decision 7).
- **Play controls** are neutral scrim discs (charcoal or cream per scan, about 60 % opacity, 1 pt outline) with glass and flat variants (decision 5). The HUD is one overlay pass in the top 8 %.
- **UI Toolkit note:** UI Toolkit has no built-in backdrop blur. Implement the "glass" look as a pre-blurred cached texture sampled behind the panel (or a URP render feature scoped to shell screens) with a translucent tint token. Measure it (rule 27; Profiler screenshot suggested). If it costs frame time, ship flat.

## 5. Capture coaching UI (decision 6 + AUTH #025)

- **Four things decide scan quality:** steady motion, overlap, angles and distances, light (rule 12). Coach them with live overlays, never text walls (rule 12; REVIEW_RUBRIC G5).
- **Locked components** (decision 6):
  - **Coverage:** a translucent teal wash accumulates on captured surfaces (AR-anchored), with a coverage ring top-right. Hatch pattern for colour-blind users (decision 10).
  - **Speed:** a thin arc under the record button fills teal at a good pace and turns amber with one gentle haptic when too fast. "Slow down a little" appears after a full second of amber.
  - **Blur:** one soft haptic tick and one amber edge pulse, no words. **Low light:** one card, "Too dark here. Turn on a lamp?", with Continue anyway (rule 14's kind rejection).
  - **Mode toggle:** a two-segment toggle above the record button (Room: arc at chest height; Tabletop: slow circle at two heights), chosen before recording, remembered, never in settings (rule 13).
  - **Missed corner:** a 3D arrow at the largest unpainted region, "You missed this corner", with Got it or Upload anyway.
  - **Timing:** the ring fills over 90 s as a target, not a limit; past 3 minutes it turns amber ("Long captures rebuild worse"); Done appears at 60 % coverage or 60 s, whichever comes first.
  - **Primary action:** one 72 pt record button (neutral → teal → Done), then a 5 s preview with Retake.
  - **Capture never hard-stops.**
- **AUTH #025 extension (M1-CAPT-04):** an on-device readiness score (coverage, overlap/parallax, blur, light, tracking continuity) turns the missed-corner arrow into "add a quick pass over here". Extra passes append to the same scan, and Upload anyway stays available. Readiness **thresholds are TBD (M1-CAPT-04)**; don't hard-code numbers in the UI, and bind to whatever the capture module exposes.
- **Permissions:** camera access is primed when the player taps Scan, with a value-first pre-prompt, never on launch (rule 10).
- **Onboarding order:** play first, scan second. The demo room is playable within 60 s of install, then "now scan yours" (rule 9).
- **Waits after capture** (decision 7): the splat resolves progressively over the cached blurred room. Show "About N minutes" from the rolling median of recent jobs. Failure copy is kind and actionable, with error codes going to the report, never the screen. At the daily cost cap the job is queued with a ready-by time, never shown as an error.

## 6. Unity UI Toolkit implementation

- **Stack:** Unity 6 (`unity/ProjectSettings/ProjectVersion.txt`: 6000.0.84f1) with URP. UI Toolkit (UXML + USS + C#) is the target for the shell and HUD (kit §3.6). No UI scripts exist yet; `unity/Assets/UI/` is created by M0-DSGN-02.
- **Tokens → USS:** `export_uss.py` writes `Tokens.uss` as custom properties (`--color-accent-amber`, `--space-2`, …) on `:root`. Component USS uses `var(--…)` only (REVIEW_RUBRIC G1). Regenerate; never hand-edit the generated file.
- **Theme swaps:** keep the glass/flat, scrim-dark/scrim-light and Increase Contrast variants as USS classes on the root (`.flat`, `.scrim-light`, `.hi-contrast`) that re-point role variables. Toggle the classes from C# when the system accessibility flags or the per-scan scrim choice change.
- **Layout:** Flexbox (Yoga) in USS. Respect the safe area by reading `Screen.safeArea` into root padding. Controls sit 16 pt from rounded corners and the Dynamic Island; the HUD never overlaps the island (decision 5).
- **Units:** USS lengths are pixels scaled by the Panel Settings scale mode. Pick one reference DPI/scale so "pt" in the tokens maps consistently. Verify 44/56/72/96 pt on a real iPhone (screenshot + measurement), since the editor Game view lies about physical size.
- **Performance:** one overlay pass for the HUD (D5). Avoid per-frame style changes and allocations. Batch dynamic text updates (the timer) and use tabular figures so the layout doesn't jitter. Profile with the UI Toolkit Debugger and Frame Debugger. Frame target: 30 fps floor on older iPhones, 60 fps on current ones (Design Skills field note on rule 27).
- **Accessibility:** VoiceOver labels on every shell screen and the three HUD elements (decision 10). How VoiceOver is wired from UI Toolkit on iOS is **TBD**: it needs a spike (Unity's accessibility APIs vs a native bridge). File it with gj-gameplay before M3 rather than assuming it works.
- **Tests:** EditMode tests for the token export and contrast maths run in the `unity-tests` workflow; PlayMode UI tests are optional (SPEC §11). Attach screenshots or a clip for anything visual and request the `gj-qa-release` visual pass (Design Skills §4).

## 7. Store asset specs

- **What's required:** App Store screenshots with the diorama hero are **REQ** for launch; the preview video and top-5-market localization are **OPT** (`governance/OWNER_LAUNCH_CHECKLIST.md`, M5 section). A Bot drafts and uploads; the Owner approves and supplies gameplay footage.
- **Creative rules** (rule 28):
  - The hero shot is the **diorama view**: a real room as a tiny world with a tiny you in it.
  - The first screenshot communicates the concept without text.
  - Preview storyboard: 3 s of a real room → the shrink transition → 10 s of play → publish → a friend plays.
  - Localize screenshots for the top 5 markets before launch. Which markets is **TBD** (no ticket yet; raise it with the Coordinator at M5 planning).
- **Pixel sizes, counts and video length:** take them from Apple's current "Screenshot specifications" and "App preview specifications" pages at production time (RESOURCES §A). Don't copy numbers into the repo, because Apple changes them.
- **v1 truthfulness:**
  - Assets must not imply features that aren't in v1. v1 is a curated character roster with no biometric avatar capture (AUTH #020/#024). Capture, merge and likeness are V2.
  - DESIGN_SYSTEM decision 9's store copy ("Dress your avatar", "previewed on the player's own avatar") predates AUTH #020. For v1, read it as "your character" per the decision 4 banner. Changing the locked text needs an AUTH, so propose the wording in `design/proposals/`.
  - Apple 2.3 (accurate metadata) and 1.2 (UGC) both apply.
- **Privacy:** no real faces or identifiable homes without consent. Scans in marketing come from the Owner's corpus (§6.5). The share clip and link carry no location (decision 8).
- **Featuring and Duo:** the App Store featuring nomination and the iPhone Duo launch video are M5-DUO-01 (gj-qa-release).

## 8. Mistakes to avoid

- Editing `design/DESIGN_SYSTEM.md` or `design/tokens/` without `APPROVED #n`. `auth_gate.py` fails the PR.
- Literal hex, pt or ms values in USS/UXML or C# (G1), or hand-editing the generated `Tokens.uss`.
- Checking contrast against a flat grey instead of the three real scans, or checking only the scrim's centre rather than its worst sample.
- A glass surface with no flat twin, or an animation with no Reduce Motion twin. Live full-screen blur in play.
- Text-only coaching, a blank spinner, or a hard stop in capture.
- Amber over 10 % of a screen, amber body text on cream, teal on charcoal, or state carried by hue alone.
- Player-facing strings saying level, map, goal or user (decision 2 vocabulary).
- Store placed after a loss, before the first summit, or covering Share. Timers, badges or "limited" language (decision 9; rule 26).
- Marketing a biometric "you" avatar in v1 (AUTH #020/#024).
- Bundling camera permission or consent into onboarding (rule 10; SECURITY_CHECKLIST §5).
- Measuring touch targets in the editor instead of on a device.

## 9. Checklists

**Pre-PR (UI or visual)** — Design Skills §4 plus REVIEW_RUBRIC G1–G8 and D5. These are suggestions, not merge gates (SPEC §11), but run them:
- [ ] Tokens only; `Tokens.uss` regenerated and unchanged by hand (G1).
- [ ] Contrast screenshots on bright room, dark room and cluttered tabletop: text ≥ 4.5:1, icons ≥ 3:1; deuteranopia simulation on any new state colour (G2).
- [ ] Glass and flat both shown; Reduce Transparency, Increase Contrast and Reduce Motion tested (G3).
- [ ] Targets ≥ 44 pt, play ≥ 56, 16 pt insets, Dynamic Island clear; one primary action, the largest and highest-contrast element (G4).
- [ ] No text-only instructions; wait states per decision 7 (G5).
- [ ] Nothing new in the play viewport; HUD in the top 8 %, one overlay pass (G6, D5).
- [ ] Copy against the voice rules and vocabulary (G7).
- [ ] Transition and avatar presentation per decisions 3 and 4 (G8).
- [ ] Any new movement or camera constant goes in the shared tuning file (Design Skills §4; Movement Bible).
- [ ] Profiler screenshot for UI/gameplay PRs (suggested).
- [ ] Screenshots or clip attached; `gj-qa-release` visual pass requested.
- [ ] Protected paths touched? `APPROVED #n` is in the PR body.
- [ ] Repo checks green: `ruff check .`, `ruff format --check .`, `python tickets/validate.py`, `python .github/scripts/check_movement_sync.py`.

**Store assets:** Apple's current spec page checked · diorama hero first, no text needed · no V2 features shown · no real faces or identifiable homes without consent · no location in clips or links · Owner approval recorded.

## 10. Pointers

`design/DESIGN_SYSTEM.md` (§1–§12) · `design/Gigantic-Journey-Design-Skills.md` (§3 rules 1–28, §4 checklist) · `design/MOVEMENT_BIBLE.md` · `design/proposals/` (decision-*-options, `capture-ux-coaching-v1.md`, `character-roster-v1.md`, `iphone-duo-track.md`, `publish-browse-rank-moderation-v1.md`) · `governance/REVIEW_RUBRIC.md` G1–G8, D5 · `governance/SECURITY_CHECKLIST.md` §5, §6.5, §10 · `governance/OWNER_LAUNCH_CHECKLIST.md` · `.github/scripts/auth_gate.py` · SPEC §3.1, §3.7, §3.11, §11 · tickets M0-DSGN-01, M0-DSGN-02, M1-CAPT-04, M3-DUO-01, M3-DUO-02, M5-DUO-01.

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + curated RESOURCES.md starter set. |
| 2026-09-26 | `design/tokens/` and `unity/Assets/UI/` don't exist yet (M0-DSGN-02 open). The three test scans are unset until M0-DSGN-01's mockups. Decision 9's "Dress your avatar" copy predates AUTH #020 and needs a proposal + AUTH to change. VoiceOver from UI Toolkit on iOS needs a spike. Store pixel specs should be read from Apple at production time. | gj-operator expanded RESOURCES.md to 102 link-checked entries and rewrote SKILLS.md around the AT-2 topics (M0-SKILL-07). |
