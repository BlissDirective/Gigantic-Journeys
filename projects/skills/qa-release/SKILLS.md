# gj-qa-release — Working Handbook

Remit: test harnesses, on-device QA, crash analytics, and App Store release ops. Re-read at session start; update when you learn something. Authored 2026-09-24.

## GJ context
- **iOS-only v1 (AUTH #003); Android deferred to v1.1.** Play Console knowledge is for later.
- **Tests/QA/device measurements are suggestions, never merge gates** (AUTH #003 / SPEC §11). The merge gates are the automated CI checks + the security rules. QA's job is evidence + confidence, and catching what CI can't.
- No minimum device model; automatic quality tiers, best graphics on newest iPhones.

## Principles
- **Merge gate = CI + security, not QA.** Don't block a merge on a QA measurement; do raise the finding loudly and file it.
- **On-device truth.** The editor lies about perf. Measure fps/thermals/memory on real iPhones across a tier matrix (old/mid/new).
- **The M1 exit test is the north star:** 10 fresh scans reach a reachable summit with ≥2 routes (M1-QA-01). Reconstruction + render + journey must survive real rooms.
- **Evidence standard** (M0-QA-02): reproducible steps, device+OS, build hash, screenshots/video, numbers — no secrets in reports (SECURITY_CHECKLIST §1.3).

## Techniques
- Unity Test Framework (edit-mode + play-mode); scripted editor smoke task in `-batchmode` (M0-QA-01).
- TestFlight for internal/external beta; a separate ops account with no production secrets (§8.4).
- Crash analytics (Sentry or Firebase Crashlytics, free tier, AUTH #017) — track the 99%+ crash-free target (SPEC §6/§9).
- iOS splat-render QA (M1-UNITY-01): verify correct depth ordering on device (the #1 risk), record fps @ splat count.

## Pitfalls
- Treating a QA fail as a merge blocker (it isn't) — but also don't let a real defect ship silently; escalate.
- Reports leaking secrets or raw user media — forbidden (§1.3, §6.5).
- Testing only on the newest iPhone — cover the tier matrix.

## Checklist (release)
Build hash recorded ✓ · crash-free target tracked ✓ · release flags off (debug/verbose) (§9.8) ✓ · privacy labels accurate ✓ · TestFlight via ops account ✓ · evidence complete, no secrets ✓.

## Pointers
`qa/` · SPEC §6/§9/§11 · SECURITY_CHECKLIST §8.2/§8.4/§9 · Apple App Review Guidelines · tickets M0-QA-01/02, M1-QA-01, M1-UNITY-01.
