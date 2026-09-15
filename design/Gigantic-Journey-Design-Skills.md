# Gigantic Journeys — Design Skills

`Gigantic-Journey-Design-Skills.md` · v1.1 · September 13, 2026 (v1.1 reflects the v1 product lock: no synthetic game objects; summit/routes/vistas; Tier 0+1 reactivity)
Continuous reference for the Owner, Claude Code (Coordinator), and the `gj-design`, `gj-gameplay`, `gj-capture`, and `gj-avatar` Bots. Lives at `/design/Gigantic-Journey-Design-Skills.md` in the repo. Bots re-read Sections 3–5 at the start of every design or UI ticket.

How to use: Section 2 is the reading list (50 sources, three buckets). Section 3 is what they add up to, distilled into rules with a Gigantic Journeys (GJ) application for each. Section 4 is the pre-PR checklist. Section 5 lists decisions still open for the design brainstorm. When a rule and a source disagree, the rule in Section 3 wins until an ADR changes it.

---

## 1. Context that shapes every decision

- GJ is a **camera-first, UGC, real-environment traversal game** on phones: a near-photorealistic 1:12 avatar of you journeys through places you scan. In v1 the only non-photo things on screen are the avatar, one summit beacon, optional route and vista markers, and the HUD. Enemies, coins, platforms, and characters are post-launch DLC. It has three distinct UX modes with different rules: **capture** (AR guidance, hands moving), **create** (avatar and level generation, waiting states), and **play** (landscape, two thumbs, 30 fps minimum on a 2023 mid-tier Android).
- The world is a **photoreal Gaussian splat of a real place**. Every UI and game element sits on top of photography, so contrast, legibility, and "what is game vs what is real" are the central visual problems.
- Platform conventions matter for the app shell only. **In-game HUD is ours**; Apple and Google guidelines govern menus, settings, consent, and store assets.
- Two platform shifts are live: Apple's Liquid Glass becomes mandatory for apps built with Xcode 27 (compatibility flags disabled), and Google's Material 3 Expressive (from Android 16, extended at I/O 2026) is the Android baseline. Both push toward layered, motion-rich, translucent chrome. Both have drawn legibility criticism, which is doubly relevant when the background is a photo of someone's living room.

---

## 2. The 50 resources

### A. Mobile app design and platform guidelines (16)

| # | Resource | Why it matters for GJ |
|---|---|---|
| 1 | Apple Human Interface Guidelines (developer.apple.com/design) — iOS 26/27 | App-shell conventions, Liquid Glass materials, tab bars, sheets, accessibility settings |
| 2 | Apple: Liquid Glass technology overview and WWDC 2025/2026 design sessions | Lensing vs blur, hierarchy over photo backgrounds, the iOS 27 intensity slider and Reduce Transparency behaviors we must respect |
| 3 | Google Material Design 3 (m3.material.io) + Material 3 Expressive | Android baseline, color roles, 8dp spacing, expressive motion physics |
| 4 | Google I/O 2026 "What's new in Material" | Expressive layout scaffold, lists/menus, search app bar |
| 5 | Apple App Store Review Guidelines + Product Page / screenshot specs | UGC (1.2) and privacy (5.1) rules, preview video and screenshot sizes |
| 6 | Google Play Developer Policy + Data safety form guidance | UGC moderation, biometric data disclosure, store assets |
| 7 | Nielsen Norman Group — mobile UX articles and the Liquid Glass usability analysis | Evidence-based warnings on translucency, legibility, predictability |
| 8 | Laws of UX (lawsofux.com) | Fitts, Hick, Doherty (400 ms), Peak-End, Zeigarnik — used throughout Section 3 |
| 9 | Luke Wroblewski — Mobile First, thumb-zone research | Reach maps for one-handed and two-thumb layouts |
| 10 | Steven Hoober — "How Do Users Really Hold Mobile Devices?" | Grip and thumb data behind HUD placement |
| 11 | Growth.Design case studies (growth.design) | Onboarding and paywall teardowns in comic form; the pattern library for our flows |
| 12 | Mobbin (mobbin.com) | Screen-flow reference for capture, avatar creators (e.g., Bitmoji, Ready Player Me), leaderboards |
| 13 | Page Flows / Screenlane | Recorded onboarding and permission-request flows |
| 14 | WCAG 2.2 + Apple/Google accessibility docs | Contrast 4.5:1 text, 3:1 UI; 44pt/48dp targets; Reduce Motion; Dynamic Type |
| 15 | Google's "Camera-first apps" and ARCore UX guidelines; Apple ARKit HIG (AR section) | Coaching overlays, device-motion prompts, reticles, safe-space guidance |
| 16 | Niantic Scaniverse scan-technique docs; Polycam and Luma capture guides | The actual capture behaviors we must coach: steady motion, overlap, 1–3 minute passes, lighting, multiple angles |

### B. UI/UX craft (14)

| # | Resource | Why it matters for GJ |
|---|---|---|
| 17 | Refactoring UI (Wathan & Schoger) | Hierarchy, spacing scales, shadows, color systems without a designer |
| 18 | Don Norman — The Design of Everyday Things | Affordances, feedback, error tolerance; the mental model for "is this a platform or the couch?" |
| 19 | Steve Krug — Don't Make Me Think | Scannability; nothing in capture or create should need reading |
| 20 | Jenifer Tidwell — Designing Interfaces (3rd ed.) | Pattern vocabulary for lists, feeds, wizards, progressive disclosure |
| 21 | Alan Cooper — About Face | Goal-directed design, personas, posture (GJ has "transient" and "sovereign" moments) |
| 22 | Kim Goodwin — Designing for the Digital Age | Scenario-based design for multi-step flows |
| 23 | Butterick's Practical Typography + Google Fonts Knowledge | Type scale, line length, legibility on glass and photo backgrounds |
| 24 | Material Motion + Apple animation guidelines; Disney's 12 principles (Thomas & Johnston) | Motion that explains state changes; squash/stretch for the avatar and UI |
| 25 | Val Head — Designing Interface Animation | Motion system, durations, easing, Reduce Motion fallbacks |
| 26 | Josh Clark — Designing for Touch | Gesture ergonomics, avoiding gesture conflicts (camera vs interaction) |
| 27 | Brad Frost — Atomic Design | Token → component → screen structure for `/design/DESIGN_SYSTEM.md` and Unity UI Toolkit |
| 28 | Design Tokens Community Group spec + Figma Variables docs | Token format Bots implement in USS/UXML |
| 29 | Colorable / Accessible Palette / Leonardo (Adobe) | Generating contrast-safe palettes against arbitrary photo backgrounds |
| 30 | Baymard Institute (mobile checkout research) | Purchase-flow friction data for the IAP sheet |

### C. Mobile game design, game UX, and game feel (20)

| # | Resource | Why it matters for GJ |
|---|---|---|
| 31 | Celia Hodent — The Gamer's Brain (book) and GDC "Gamer's Brain" Parts 1–3 | Perception, memory, attention limits; onboarding by doing; engage-ability audits |
| 32 | Steve Swink — Game Feel | Input latency, response curves, camera, polish; the bible for the controller |
| 33 | Jesse Schell — The Art of Game Design: A Book of Lenses | Lens-based design reviews (we use "lens of the toy," "lens of the player") |
| 34 | GMTK — "Why Does Celeste Feel So Good to Play?" and Maddy Thorson's Celeste movement code notes | Coyote time, jump buffering, corner correction, assist mode |
| 35 | GDC — Super Mario Odyssey / Astro Bot / Sackboy postmortems and movement talks | Readable jump arcs, camera-relative control, "everything reacts" |
| 36 | GDC — "50 Game Camera Mistakes" (John Nesky, Journey) | The camera rulebook for a third-person platformer in tight, real rooms |
| 37 | Mark Brown / GMTK — level design series; "Nintendo's Kishōtenketsu" | Introduce, develop, twist, resolve; feeds the level generator's structure |
| 38 | Anna Anthropy & Naomi Clark — A Game Design Vocabulary | Verbs, objects, scenes; the generator's ontology |
| 39 | Raph Koster — A Theory of Fun | Learning curves, mastery loops; what makes a sixth level worth playing |
| 40 | Game Developer (ex-Gamasutra) — "Designing better controls for the touchscreen experience"; Simogo and Fireproof interviews | Touch has no tactile confirmation; compensate with audio/visual; resolve camera-vs-interaction gesture conflicts |
| 41 | Deconstructor of Fun (deconstructoroffun.com) | Meta-game, economy, and live-ops teardowns of top mobile titles |
| 42 | GameAnalytics / GameRefinery benchmark reports (2026) | Retention benchmarks: D1 ~27% average, D30 1–7% by genre; onboarding can lift retention up to 50% |
| 43 | Mobile Free-to-Play (Will Luton) + "Ethical monetization" GDC talks | Cosmetic-only IAP, no pay-to-win, no dark patterns; matches our two launch SKUs |
| 44 | Game UI Database (gameuidatabase.com) + Interface In Game | HUD, results, leaderboard, and shop screen references across thousands of games |
| 45 | GDC — Fortnite / Rocket League UX talks on HUD minimalism and readability | Diegetic vs screen-space HUD, safe zones, colorblind modes |
| 46 | Unity UI Toolkit docs + Unity mobile performance best practices (URP, Profiler, memory) | Implementation constraints and 30 fps budget |
| 47 | Unity Gaussian splatting renderers (aras-p/UnityGaussianSplatting and successors) + Niantic/Polycam splat docs | What splats can and cannot do visually on mobile; LOD and culling |
| 48 | Niantic Peridot and Pokémon GO AR design postmortems; Meta Hyperscape | Real-world-blended play: occlusion, scale cues, "the real thing is the star" |
| 49 | Ready Player Me, Bitmoji, Avaturn, Meshy/Tripo avatar UX | Avatar-creation flows, likeness confirmation, wardrobe patterns |
| 50 | Roblox and Dreams (Media Molecule) UGC design talks | Browse, rate, moderate, and creator-incentive loops for user-built levels |

---

## 3. Synthesized principles

Each rule ends with **GJ:** the concrete application.

### 3.1 The photo is the star; UI and game elements must read against it
1. Treat every scan as an unknown, high-frequency, full-color background. Never rely on a fixed palette for contrast. Use a **scrim or glass layer under any text or control** and compute contrast at runtime (Leonardo-style) rather than assuming. **GJ:** all HUD and menu text sits on a translucent dark or light scrim auto-picked per scan; minimum 4.5:1 text, 3:1 icons.
2. The few non-photo elements need a **consistent, unmistakable visual language** so nothing competes with the room. **GJ:** the summit beacon, route markers, and vista markers share one restrained treatment (thin light, low saturation, no solid geometry); the avatar is the only rendered solid, set off by a subtle rim light and contact shadow. Real objects stay photoreal and untouched except for Tier 1 reactive displacement.
3. Follow platform materials for the app shell, not for the game. Respect Reduce Transparency, Increase Contrast, and the iOS 27 intensity slider by shipping a **flat, opaque fallback** for every glass surface. **GJ:** design system defines each surface twice: glass and flat.

### 3.2 Hierarchy, type, spacing
4. One primary action per screen; make it the largest, highest-contrast element (Hick's Law). **GJ:** Capture screen = one big record button; Create = one "Generate"; Results = one "Share".
5. Type scale of 5 steps maximum, based on the platform default body size; support Dynamic Type/font scaling in the shell (not in HUD, which uses fixed sizes tuned to 30 fps overlay). Line length 45–75 characters. **GJ:** Body 17pt iOS / 16sp Android; HUD numerals use a tabular-figure display face.
6. Spacing on an 8-point grid with a 4-point half step; touch targets 44pt / 48dp minimum, 56 for anything used while moving. **GJ:** capture and play controls are 56+.

### 3.3 Motion
7. Motion explains state change; nothing animates for decoration alone. Durations 150–300 ms for UI, 400–600 ms for screen transitions; expressive overshoot only on Android-native components. **GJ:** the diorama "shrink" transition (room fills the screen → room becomes a tabletop world) is the one signature hero animation and gets its own budget.
8. Provide Reduce Motion equivalents (cross-fade) for every transition. **GJ:** required in the design-system spec for each component.

### 3.4 Onboarding and first session
9. Teach by doing, never by text walls. First playable moment in **under 3 minutes**, first win in under 5. Retention lift from good onboarding can be as high as 50%; D1 average across mobile games is roughly 27%, so the first session decides the product. **GJ:** onboarding order is *play first, scan second*: a pre-scanned demo room lets the user run and jump within 60 seconds of install, then "now scan yours."
10. Ask for permissions in context with a value-first pre-prompt (camera when tapping Scan, not on launch). Explain biometric consent in one plain sentence plus a "learn more" sheet; consent is a separate explicit step, never bundled.
11. Show progress and time estimates on every wait (Doherty threshold: perceived responsiveness under 400 ms; anything over 10 s needs a determinate indicator and something to look at). **GJ:** reconstruction and avatar generation waits show the splat resolving progressively and a "what's happening" explainer; never a blank spinner.

### 3.5 Capture UX (the mode most apps get wrong)
12. Coach the four things that determine scan quality: steady continuous motion, overlap with previous views, multiple angles and distances, good light. Keep passes to 1–3 minutes; longer degrades results. **GJ:** a live coverage heat-map on the phone, a speed meter that turns amber when moving too fast, blur rejection with a gentle haptic, and a "you missed this corner" arrow before upload.
13. Two capture modes need two coaching scripts: **room walkthrough** (arc at chest height around the space) and **tabletop orbital** (slow circle at two heights around the object). **GJ:** mode is chosen by a single toggle with an illustration, never a settings page.
14. Reject early, kindly. A scan-quality gate before upload saves the user a two-minute wait for a bad result. Frame it as help, not failure: "Too dark here — turn on a lamp?"

### 3.6 Avatar creation UX
15. Likeness confirmation beats sliders. Show the generated head turning slowly next to the source photo, ask "Is this you?", offer *Retake* or *Tweak* (three or four coarse controls: skin tone, hair, glasses, build). **GJ:** no 40-slider editor in v1; the parametric body's height/build comes from the full-body photo and can be nudged with one control.
16. Wardrobe is the monetization surface and the emotional payoff. Default outfit generated to roughly match the photo; store shown *after* the first level, not before.

### 3.7 Game feel and controls
17. The environment must *answer* every contact: Tier 0 material-keyed audio, particles, haptics, and camera shake on every step, landing, grab, and slide; Tier 1 displacement (cushions dent, curtains sway, papers flutter, plants rustle) wherever segmentation finds a soft or hanging object. Touch has no tactile confirmation, so **every input needs audio and visual acknowledgment**, and inputs must be forgiving: coyote time (~100 ms), jump buffering, ledge-grab windows, corner correction. Assist options (slower time, extra jump height) improve retention without shame. **GJ:** movement constants live in one tuning file shared with the level validator.
18. Two-thumb landscape layout: floating virtual stick that appears under the left thumb anywhere in the left third; jump on the right thumb as the largest target; one contextual action button (grab/stomp) that appears only when relevant. Let players reposition and resize controls. Controller support from day one (many platformer players use Backbone-style controllers).
19. Camera is a design feature, not plumbing. Camera-relative movement, collision-aware follow, look-ahead in the direction of travel, no snapping. Real rooms are tight: bias to a slightly higher, wider framing than a typical platformer and fade or dither real geometry that occludes the avatar. Never fight the player for the camera; offer a one-finger drag on the right side for manual adjust that auto-recenters.
20. Readability at 1:12: the avatar is small on screen. Give it a subtle rim light or contact shadow so it pops off the photoreal floor, and keep enemies at least 1.3× avatar height or high-contrast.

### 3.8 HUD
21. Minimal, edge-anchored, safe-zone aware (notches, rounded corners, home indicator). Show only what changes: timer, coins, lives/checkpoint. Everything else appears on pause. Colorblind-safe: never encode state by hue alone. **GJ:** HUD occupies the top 8% of the screen in landscape and nothing else; results screen carries the detail.

### 3.9 Journey design (feeds summit, route, and vista generation)
22. Structure each route as introduce → develop → twist → resolve (kishōtenketsu): a safe first mantle, a section that teaches one move, one "aha" use of the real environment (a bookshelf climb, a gap between couch and table, a Lego turret), then the summit. The summit is visible from the start. **GJ:** the environment spec includes a `beat` field per route segment; the validator checks that beat 1 uses only run, jump, and mantle. Vistas are chosen for view, not difficulty.
23. Real-world play works when the real thing stays legible and the digital things react to it. Enemies patrol *on* real surfaces, coins hover *over* real objects, and the shrink transition makes the scale relationship obvious. Never obscure the room with effects.

### 3.10 UGC, social, and browsing
24. Browse by *place*, not by list. Thumbnails are the room itself; titles are optional. Sort by "Top this week," "New," and "Near your scale" (tabletop vs room). Ratings are one tap; reports are one tap with a reason sheet.
25. Give creators visible credit and feedback (plays, completions, best times) on their own levels — the Roblox/Dreams lesson is that creator stats are the strongest UGC retention loop. Moderation must be fast and visible ("Under review" badge) so the community trusts the feed.

### 3.11 Monetization and ethics
26. Cosmetic-only, no timers, no gacha, no pay-to-win. Show the store after a win, never on a loss. Clear prices, one-tap restore, no fake scarcity. This is both a design position and a store-review risk reducer.

### 3.12 Performance is part of design
27. 30 fps minimum on a 2023 mid-tier Android; 60 fps target on current iPhones. Splat LOD and culling, HUD drawn in a single overlay pass, no full-screen blur in play mode (glass is for the shell only). Design reviews include a Profiler screenshot.

### 3.13 Store assets
28. Hero shot is the **diorama view**: a real room as a tiny world with a tiny you in it. First screenshot must communicate the concept without text. Preview video: 3 seconds of a real room, the shrink transition, 10 seconds of play, publish, friend plays. Localize screenshots for the top 5 markets before launch.

---

## 4. Pre-PR design checklist (Bots run this before opening any UI or gameplay PR)

- [ ] Contrast verified on three test scans (bright room, dark room, cluttered tabletop): text ≥4.5:1, icons ≥3:1.
- [ ] Every glass surface has a flat fallback; tested with Reduce Transparency and Increase Contrast on iOS, and with Material dynamic color off on Android.
- [ ] Touch targets ≥44pt/48dp; play controls ≥56; safe-zone insets respected on notched devices.
- [ ] Reduce Motion equivalent exists for every animation added.
- [ ] One primary action per screen; primary is largest and highest contrast.
- [ ] No text-only instructions in capture, create, or play; illustrations or live overlays instead.
- [ ] Waits >1 s have progress; waits >10 s have determinate progress plus content.
- [ ] Any new movement or camera constant is added to the shared tuning file and the level validator's copy.
- [ ] HUD stays within the top 8% in play; nothing new in the play viewport without an ADR.
- [ ] Colorblind check (deuteranopia simulation) on any new state color.
- [ ] Profiler screenshot attached for any gameplay or UI PR (frame time on the reference Android device).
- [ ] Screenshots or clip attached; `gj-qa-release` visual pass requested.
- [ ] Copy reviewed against the voice guide (Section 5 once locked): short, warm, verbs first, no jargon.

---

## 5. Open decisions for the design brainstorm (to be locked into `/design/DESIGN_SYSTEM.md`)

1. **Non-photo element language**: avatar rim light and contact shadow, summit beacon, route and vista marker treatment, flag-planting moment.
2. **Brand**: wordmark, palette (must include a scrim strategy), iconography, tone of voice.
3. **Signature transition**: the shrink/diorama moment — how it looks and how long it takes.
4. **Avatar presentation**: default wardrobe set, rim light/contact shadow treatment, likeness-confirmation screen.
5. **Play layout**: exact control positions, camera framing defaults, HUD content.
6. **Capture coaching UI**: coverage map style, speed meter, mode toggle illustrations.
7. **Create flow**: how reconstruction and level generation are shown while waiting.
8. **Browse/feed**: card design, sort tabs, creator stats, moderation badges.
9. **Store and results screens**: post-win layout and the two launch SKUs.
10. **Accessibility baseline**: assist options list, colorblind palettes, motion and transparency fallbacks.

---

## 6. Maintenance

- Owner or `gj-design` appends new sources with a one-line "why" and re-numbers only at major versions.
- When a rule changes via ADR, update Section 3 and add the ADR number in brackets.
- Bots record contradictions they hit in the field under a `## Field notes` heading at the bottom; the Owner reviews them at each checkpoint.
