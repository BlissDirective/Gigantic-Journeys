# gj-design — Resources

The annotated research list for the design hat. Research focus is from kit §3.6: mobile game UX, AR capture guidance UX, onboarding conversion, accessibility, design systems for Unity UI Toolkit, and App Store and Play visual asset requirements. Motion and glass/flat surfaces get their own group because DESIGN_SYSTEM decisions 3 and 10 and Design Skills rules 3, 7, 8 and 27 gate them. Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26 (HTTP 200 plus a page-title check). The six w3.org pages sit behind a bot challenge on the checking box, so they were verified by fetching the page content instead. Vendor and tool links are references, not approvals. Any paid tool, account or asset licence needs an AUTH (`agents/grok/README.md` §6). v1 is iOS-only (AUTH #003), so the Android/Material entries are baseline references for when Android ships. Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first: `design/DESIGN_SYSTEM.md` (decisions 1–10, §12 contrast table); `design/Gigantic-Journey-Design-Skills.md` §3–§4 (and its 50-resource list in §2, which this list extends rather than repeats wholesale); `design/proposals/decision-*-options.md`; `design/MOVEMENT_BIBLE.md` §3, §8, §10; `governance/REVIEW_RUBRIC.md` G1–G8; tickets M0-DSGN-01/02.

## A. Platform guidelines and store asset requirements

1. **Apple HIG — Feedback** — <https://developer.apple.com/design/human-interface-guidelines/feedback> · *doc* — Every input needs acknowledgment (rule 17): visual, audio and haptic feedback patterns.
2. **Apple HIG — Buttons** — <https://developer.apple.com/design/human-interface-guidelines/buttons> · *doc* — Button hierarchy for "one primary action per screen" (rule 4).
3. **Apple Human Interface Guidelines** — <https://developer.apple.com/design/human-interface-guidelines> · *doc* — The iOS shell conventions the design system follows (Design Skills rule 3).
4. **Apple HIG — Designing for games** — <https://developer.apple.com/design/human-interface-guidelines/designing-for-games> · *doc* — Apple's game-specific guidance on controls, HUD and settings.
5. **Apple HIG — Game controls** — <https://developer.apple.com/design/human-interface-guidelines/game-controls> · *doc* — Touch control sizing and placement for the locked play layout (DESIGN_SYSTEM decision 5).
6. **Apple HIG — Materials** — <https://developer.apple.com/design/human-interface-guidelines/materials> · *doc* — Glass/material rules and the flat fallback requirement (rule 3, decision 2).
7. **Apple — Liquid Glass technology overview** — <https://developer.apple.com/documentation/technologyoverviews/liquid-glass> · *doc* — The current iOS glass material the shell's glass surfaces reference.
8. **Apple WWDC25 — Meet Liquid Glass** — <https://developer.apple.com/videos/play/wwdc2025/219/> · *talk* — How glass lenses content and when it hurts legibility over busy backgrounds like scans.
9. **Apple WWDC25 — Get to know the new design system** — <https://developer.apple.com/videos/play/wwdc2025/356/> · *talk* — Hierarchy and grouping with the new materials.
10. **Apple HIG — Color** — <https://developer.apple.com/design/human-interface-guidelines/color> · *doc* — System color behaviour, Increase Contrast and dark mode.
11. **Apple HIG — Typography** — <https://developer.apple.com/design/human-interface-guidelines/typography> · *doc* — Dynamic Type sizes behind the 17 pt body and the ≤ 5-step scale (rule 5).
12. **Apple HIG — Layout** — <https://developer.apple.com/design/human-interface-guidelines/layout> · *doc* — Safe areas, the Dynamic Island and rounded corners (decision 5 insets).
13. **Apple HIG — Motion** — <https://developer.apple.com/design/human-interface-guidelines/motion> · *doc* — Purposeful motion and Reduce Motion (rules 7, 8).
14. **Apple HIG — Onboarding** — <https://developer.apple.com/design/human-interface-guidelines/onboarding> · *doc* — Teach by doing; supports "play first, scan second" (rule 9).
15. **Apple HIG — Privacy** — <https://developer.apple.com/design/human-interface-guidelines/privacy> · *doc* — Permission requests in context with a value-first pre-prompt (rule 10).
16. **Apple HIG — Augmented reality** — <https://developer.apple.com/design/human-interface-guidelines/augmented-reality> · *doc* — Coaching, device-motion prompts and feedback during AR capture (decision 6).
17. **Apple HIG — Loading** — <https://developer.apple.com/design/human-interface-guidelines/loading> · *doc* — Progress and content while waiting (rule 11, decision 7).
18. **Apple HIG — Live Activities** — <https://developer.apple.com/design/human-interface-guidelines/live-activities> · *doc* — The background-continuation surface decision 7 specifies for reconstruction waits.
19. **Apple HIG — In-app purchase** — <https://developer.apple.com/design/human-interface-guidelines/in-app-purchase> · *doc* — Clear prices and restore, matching decision 9 and rule 26.
20. **Apple HIG — App icons** — <https://developer.apple.com/design/human-interface-guidelines/app-icons> · *doc* — Icon sizes and layers for the locked beam-over-room icon (decision 2).
21. **Apple HIG — Playing haptics** — <https://developer.apple.com/design/human-interface-guidelines/playing-haptics> · *doc* — Haptic restraint for capture ticks and transition beats (decisions 3, 6).
22. **Apple Design Resources (templates and kits)** — <https://developer.apple.com/design/resources/> · *vendor guide* — Official Figma/Sketch templates for mockups (M0-DSGN-01).
23. **App Store Connect — Screenshot specifications** — <https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications> · *doc* — Exact screenshot sizes per device class for the store listing.
24. **App Store Connect — App preview specifications** — <https://developer.apple.com/help/app-store-connect/reference/app-preview-specifications> · *doc* — Preview video length, resolution and format for the rule 28 storyboard.
25. **Apple — Creating your product page** — <https://developer.apple.com/app-store/product-page/> · *doc* — How screenshots, preview and text work together; first screenshot must sell the concept (rule 28).
26. **Apple — App previews** — <https://developer.apple.com/app-store/app-previews/> · *doc* — Guidance on preview content: real in-app footage only.
27. **Apple — Custom product pages** — <https://developer.apple.com/app-store/custom-product-pages/> · *doc* — Variant pages (room vs tabletop) for later marketing tests.
28. **Apple — Marketing resources and identity guidelines** — <https://developer.apple.com/app-store/marketing/guidelines/> · *doc* — Rules for badges and device frames in store art.
29. **Apple App Review Guidelines** — <https://developer.apple.com/app-store/review/guidelines/> · *doc* — 1.2 UGC and 5.1 privacy rules that constrain browse, report and consent screens.
30. **Google Play — Preview assets (store listing graphics)** — <https://support.google.com/googleplay/android-developer/answer/9866151> · *doc* — Play listing specs; Android isn't a v1 release target (AUTH #003), so keep for later.
31. **Material Design 3** — <https://m3.material.io/> · *doc* — Android baseline and a clear reference for colour roles and tokens.

## B. Mobile game UX, onboarding and conversion

32. **NN/g — Mobile-app permission requests** — <https://www.nngroup.com/articles/permission-requests/> · *doc* — Value-first, in-context permission priming (rule 10) for camera access at Scan.
33. **NN/g — Designing empty states** — <https://www.nngroup.com/articles/empty-state-interface-design/> · *doc* — First-run browse and "no environments yet" states that teach the next action.
34. **Laws of UX** — <https://lawsofux.com/> · *doc* — Fitts, Hick and Doherty, which Design Skills §3 applies throughout.
35. **Nielsen Norman Group — Mobile and tablet design** — <https://www.nngroup.com/topic/mobile-and-tablet-design/> · *doc* — Evidence-based mobile usability research.
36. **NN/g — Liquid Glass usability analysis** — <https://www.nngroup.com/articles/liquid-glass/> · *doc* — Legibility risks of translucency; why every glass surface has a flat twin.
37. **NN/g — Glassmorphism: definition and best practices** — <https://www.nngroup.com/articles/glassmorphism/> · *doc* — Contrast and blur guidance for glass over photos.
38. **NN/g — Mobile onboarding: tutorials vs contextual help** — <https://www.nngroup.com/articles/mobile-app-onboarding/> · *doc* — Why contextual teaching beats up-front tutorials (rule 9).
39. **NN/g — Progress indicators** — <https://www.nngroup.com/articles/progress-indicators/> · *doc* — Determinate vs indeterminate progress; backs decision 7's four-stage bar.
40. **NN/g — Response times: the 3 important limits** — <https://www.nngroup.com/articles/response-times-3-important-limits/> · *doc* — The 0.1 s / 1 s / 10 s thresholds behind rule 11.
41. **How Do Users Really Hold Mobile Devices? (Steven Hoober, UXmatters)** — <https://www.uxmatters.com/mt/archives/2013/02/how-do-users-really-hold-mobile-devices.php> · *paper* — Grip data behind thumb placement in the two-thumb layout.
42. **Growth.Design case studies** — <https://growth.design/case-studies> · *doc* — Onboarding and paywall teardowns; patterns and anti-patterns for create and store flows.
43. **Mobbin** — <https://mobbin.com/> · *vendor guide* — Screen-flow references for capture, leaderboards and store screens.
44. **Game UI Database** — <https://www.gameuidatabase.com/> · *doc* — Searchable game HUD/menu screenshots for HUD and results references.
45. **Celia Hodent — The Gamer's Brain (site)** — <https://celiahodent.com/> · *doc* — Game UX from cognitive science: perception, attention, onboarding.
46. **GDC Vault — Game UX talks** — <https://gdcvault.com/browse/gdc-24?categories=Ux> · *talk* — Current game UX talks for HUD and onboarding research.
47. **GameAnalytics — Mobile gaming benchmarks** — <https://gameanalytics.com/reports> · *doc* — D1/D7 retention benchmarks that give context for the onboarding targets (rule 9).
48. **Deconstructor of Fun** — <https://www.deconstructoroffun.com/> · *doc* — Mobile game design and monetization analysis; reference for ethical store placement.
49. **Luke Wroblewski — Designing for large screen smartphones** — <https://www.lukew.com/ff/entry.asp?1927> · *doc* — Thumb-zone reach for one-handed and two-thumb use.

## C. AR capture guidance UX

50. **Apple ARKit — ARCoachingOverlayView** — <https://developer.apple.com/documentation/arkit/arcoachingoverlayview> · *doc* — Apple's built-in AR coaching; compare against the custom coverage wash (decision 6).
51. **Apple ARKit — Managing session life cycle and tracking quality** — <https://developer.apple.com/documentation/arkit/managing-session-life-cycle-and-tracking-quality> · *doc* — Tracking-state reasons (excessive motion, low light) that drive the speed arc and dark-room card.
52. **Apple RealityKit — Capturing photographs for Object Capture** — <https://developer.apple.com/documentation/realitykit/capturing-photographs-for-realitykit-object-capture> · *doc* — Apple's capture technique guide (overlap, angles, light): the behaviours GJ coaches.
53. **Apple — Scanning objects using Object Capture (guided capture sample)** — <https://developer.apple.com/documentation/realitykit/scanning-objects-using-object-capture> · *doc* — Apple's guided-capture UI with coverage feedback, the closest reference to decision 6.
54. **Apple RoomPlan** — <https://developer.apple.com/documentation/roomplan> · *doc* — Apple's room-scan coaching UX, a direct comparison for the room walkthrough script.
55. **Google ARCore — Design guidelines** — <https://developers.google.com/ar/design> · *doc* — Environment scanning, motion prompts and reticles.
56. **Polycam — Learning center** — <https://learn.poly.cam/> · *doc* — Real-world capture guidance consumers already know.
57. **Scaniverse** — <https://scaniverse.com/> · *vendor guide* — Niantic's splat capture app; reference UX for splat scanning.
58. **KIRI Engine** — <https://www.kiriengine.app/> · *vendor guide* — Consumer photogrammetry/splat app; its capture guidance is a benchmark for tabletop orbital.
59. **Luma AI** — <https://lumalabs.ai/> · *vendor guide* — Capture guidance from a well-known splat app (Luma was dropped as a backend, ADR-0005).

## D. Accessibility and contrast over photo backgrounds

60. **Material 3 — Accessibility: color contrast** — <https://m3.material.io/foundations/designing/color-contrast> · *doc* — Contrast pairing by colour role, a model for derived muted-text tokens (DESIGN_SYSTEM §12).
61. **WCAG 2.2** — <https://www.w3.org/TR/WCAG22/> · *doc* — The contrast and target thresholds in REVIEW_RUBRIC G2/G4 and rule 1.
62. **Understanding SC 1.4.3 Contrast (Minimum)** — <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html> · *doc* — 4.5:1 text, 3:1 large text: the math behind the §12 measurements.
63. **Understanding SC 1.4.11 Non-text Contrast** — <https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html> · *doc* — 3:1 for icons and controls on scans.
64. **Understanding SC 2.5.8 Target Size (Minimum)** — <https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html> · *doc* — Target-size rationale; GJ uses the stricter 44 pt / 56 pt (rule 6).
65. **Understanding SC 2.3.1 Three Flashes or Below Threshold** — <https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html> · *doc* — The "nothing flashes above 3 Hz" rule in decision 10.
66. **Adobe Leonardo** — <https://leonardocolor.io/> · *vendor guide* — Contrast-based colour generation named in rule 1 ("Leonardo-style").
67. **APCA contrast calculator** — <https://apcacontrast.com/> · *doc* — Perceptual contrast model worth comparing with WCAG 2 on scan backgrounds.
68. **WebAIM — Contrast checker** — <https://webaim.org/resources/contrastchecker/> · *doc* — Quick verification of token pairs.
69. **Coblis — Color blindness simulator** — <https://www.color-blindness.com/coblis-color-blindness-simulator/> · *doc* — Deuteranopia/protanopia/tritanopia checks for every state color (decision 10).
70. **Apple HIG — Accessibility** — <https://developer.apple.com/design/human-interface-guidelines/accessibility> · *doc* — VoiceOver, Dynamic Type and display accommodations.
71. **Apple — UIAccessibility.isReduceMotionEnabled** — <https://developer.apple.com/documentation/uikit/uiaccessibility/isreducemotionenabled> · *doc* — The system flag the Reduce Motion variants read.
72. **Apple — UIAccessibility.isReduceTransparencyEnabled** — <https://developer.apple.com/documentation/uikit/uiaccessibility/isreducetransparencyenabled> · *doc* — The flag that swaps glass for flat (decision 10).
73. **Apple — UIAccessibility.isDarkerSystemColorsEnabled (Increase Contrast)** — <https://developer.apple.com/documentation/uikit/uiaccessibility/isdarkersystemcolorsenabled> · *doc* — Increase Contrast raises scrim opacity to 90 % (decision 10).
74. **Game Accessibility Guidelines** — <https://gameaccessibilityguidelines.com/> · *doc* — Game-specific accessibility checklist (remapping, captions, visual twins for audio).
75. **Xbox Accessibility Guidelines** — <https://learn.microsoft.com/en-us/gaming/accessibility/guidelines> · *doc* — Detailed, testable game accessibility guidance.
76. **Can I Play That?** — <https://caniplaythat.com/> · *doc* — Accessibility reviews by disabled players; what real users call out.
77. **AbleGamers — Accessible Player Experiences** — <https://accessible.games/accessible-player-experiences/> · *doc* — Design patterns for accessible play (assist modes, input flexibility).
78. **Unity Scripting API — AccessibilityHierarchy** — <https://docs.unity3d.com/ScriptReference/Accessibility.AccessibilityHierarchy.html> · *doc* — Unity 6's screen-reader API for VoiceOver labels on shell screens and HUD elements.

## E. Design tokens and Unity UI Toolkit

79. **Design Tokens Community Group — Format specification** — <https://www.designtokens.org/tr/drafts/format/> · *doc* — The DTCG format M0-DSGN-02 requires for design/tokens/tokens.json.
80. **W3C Design Tokens Community Group** — <https://www.w3.org/community/design-tokens/> · *doc* — Home of the DTCG spec and its status.
81. **Style Dictionary** — <https://styledictionary.com/> · *doc* — The standard token transformer; a reference for the export_uss.py pipeline.
82. **Tokens Studio** — <https://tokens.studio/> · *vendor guide* — Figma plugin that syncs DTCG tokens with mockups.
83. **Figma — Guide to variables** — <https://help.figma.com/hc/en-us/articles/15339657135383-Guide-to-variables-in-Figma> · *doc* — Figma variables that mirror tokens in the M0-DSGN-01 mockups.
84. **Material 3 — Design tokens** — <https://m3.material.io/foundations/design-tokens> · *doc* — A mature token taxonomy (reference, system, component) to model naming on.
85. **Unity Manual — UI Toolkit** — <https://docs.unity3d.com/Manual/UIElements.html> · *doc* — The UI framework for all GJ screens (UXML + USS).
86. **Unity Manual — USS custom properties (variables)** — <https://docs.unity3d.com/Manual/UIE-USS-CustomProperties.html> · *doc* — How tokens become USS variables in Tokens.uss (M0-DSGN-02 AT-2).
87. **Unity Manual — USS properties reference** — <https://docs.unity3d.com/Manual/UIE-USS-Properties-Reference.html> · *doc* — What USS can and can't express (no backdrop blur), which shapes the glass implementation.
88. **Unity Manual — Theme Style Sheets** — <https://docs.unity3d.com/Manual/UIE-tss.html> · *doc* — Swapping scrim themes (charcoal vs cream) and glass/flat variants at runtime.
89. **Unity Manual — UI Builder** — <https://docs.unity3d.com/Manual/UIBuilder.html> · *doc* — Visual authoring of UXML with live token preview.
90. **Unity Manual — USS transitions** — <https://docs.unity3d.com/Manual/UIE-Transitions.html> · *doc* — 150–300 ms UI motion in USS, plus Reduce Motion cross-fades.
91. **Unity Manual — Runtime data binding** — <https://docs.unity3d.com/Manual/UIE-runtime-binding.html> · *doc* — Binding the HUD timer and vista count without per-frame allocations.
92. **Unity Scripting API — Screen.safeArea** — <https://docs.unity3d.com/ScriptReference/Screen-safeArea.html> · *doc* — Applying the 16 pt insets from rounded corners and the Dynamic Island (decision 5).
93. **Unity — User interface design and implementation in Unity (e-book)** — <https://unity.com/resources/user-interface-design-and-implementation-in-unity> · *vendor guide* — Unity's guide to UI Toolkit architecture and styling at scale.
94. **Unity — UI Toolkit runtime demo (Unity Royale)** — <https://github.com/Unity-Technologies/UIToolkitUnityRoyaleRuntimeDemo> · *repo* — Official runtime game-UI sample built with UI Toolkit (HUD, menus, styling).
95. **Unity — UI Toolkit manual code examples** — <https://github.com/Unity-Technologies/ui-toolkit-manual-code-examples> · *repo* — Official code for the manual pages (custom controls, binding, USS).
96. **Unity Localization package** — <https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/index.html> · *doc* — String tables for localizing copy and store screenshots for the top 5 markets (rule 28).
97. **Unity Manual — UI Toolkit performance considerations** — <https://docs.unity3d.com/Manual/UIE-performance-consideration-runtime.html> · *doc* — Keeping the HUD a single overlay pass within budget (rule 27, REVIEW_RUBRIC D5).

## F. Motion, glass and flat surfaces, and the signature transition

98. **Material 3 — Motion overview** — <https://m3.material.io/styles/motion/overview> · *doc* — Easing and duration systems to encode as motion tokens (150–300 / 400–600 ms).
99. **Material 3 — Easing and duration** — <https://m3.material.io/styles/motion/easing-and-duration> · *doc* — A token-ready set of curves and durations.
100. **Apple WWDC — Design with motion (WWDC23)** — <https://developer.apple.com/videos/play/wwdc2023/10158/> · *talk* — Motion that explains state change (rule 7).
101. **Val Head — Designing Interface Animation (A List Apart excerpt)** — <https://alistapart.com/article/designing-interface-animation/> · *doc* — Purposeful UI animation and accessibility.
102. **Josh W. Comeau — Springs and bounces in native CSS** — <https://www.joshwcomeau.com/animation/linear-timing-function/> · *doc* — Clear explanation of spring-like easing for motion tokens.
