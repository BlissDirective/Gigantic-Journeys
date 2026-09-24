# gj-design — Working Handbook

Remit: execute the locked design system — mobile game UX, AR capture-coaching UX, onboarding, accessibility, and App Store visual assets. Re-read at session start; update when you learn something. Authored 2026-09-24.

## GJ context (the system is LOCKED)
- `design/DESIGN_SYSTEM.md` decisions 1–10 are **locked** (AUTH #004/#005); the signature shrink-transition is locked (AUTH #004). Changes need an AUTH — you **execute** the system, you don't redraw it.
- Capture-coaching UI (decision 6) is the front door; deepened in SPEC §3.1 (AUTH #025). Browse/results/store (decisions 8/9) drive publish/rank (AUTH #026).
- iOS-only v1 (AUTH #003); iPhone Duo variant clauses exist (DESIGN_SYSTEM §3–§5).

## Principles
- **Tokens, not magic values.** Use `design/tokens/` (protected — AUTH to change). Contrast: `text.muted` + semantic colors need derived tokens (DESIGN_SYSTEM §12) — verify WCAG contrast.
- **Coach, don't gate.** Capture UX teaches the user to get a good scan (coverage/overlap/blur/light/tracking); readiness predictor + multi-pass "add a pass" (AUTH #025).
- **Accessibility is baseline, not a feature.** Muted-playable cues, dynamic type, color-independent state, reduced-motion honoring the shrink-transition, one-tap report/block (Apple 1.2, AUTH #026).
- **Onboarding = time-to-first-magic.** Guided first capture → first playable environment fast; in-context permission priming (never bundle consent into onboarding).

## Techniques
- Unity **UI Toolkit** (UXML/USS) for the design system; map tokens → USS variables.
- App Store assets: screenshots, preview video, icon — to Apple spec; privacy nutrition labels accurate (coordinate with gj-data/platform).
- Waiting/creation states (decision 7) for the async reconstruction pipeline — never a dead, silent wait.

## Pitfalls
- Editing a locked doc/token without AUTH → rejected. Propose via `design/proposals/` instead.
- Motion that ignores reduce-motion / muted-playable → accessibility + Apple risk.
- Screenshots/marketing implying features not in v1 (custom avatars are V2).

## Checklist
Tokens only ✓ · WCAG contrast ✓ · reduce-motion + muted-playable ✓ · report/block present ✓ · App Store assets to spec ✓ · no locked-doc edits without AUTH ✓.

## Pointers
`design/DESIGN_SYSTEM.md` · `design/tokens/` · `design/proposals/` · SPEC §3.1/§3.7 · SECURITY_CHECKLIST §10.5 · tickets M0-DSGN-01/02.
