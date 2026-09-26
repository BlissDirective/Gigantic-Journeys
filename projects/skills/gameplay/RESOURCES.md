# gj-gameplay — Resources

The annotated research list for the gameplay hat. Research focus is from kit §3.3: climbing and parkour systems (Assassin's Creed, Zelda BotW/TotK, Mirror's Edge), character controller feel (Celeste, Mario Odyssey, Astro Bot), Unity 6 URP mobile performance, splat rendering integration, procedural animation, and audio middleware on mobile. Motion matching and animation tech are added as their own group because Bible §2 and §12–§13 depend on them. Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26: HTTP 200 plus a page-title check. YouTube titles were checked through oEmbed. Vendor and asset links are references, not approvals. Any purchase, licence or new package needs an AUTH plus a pin and licence record (SECURITY_CHECKLIST §7; the only approved paid asset is Motion Warping: Climb & Interact, AUTH #001). Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first: `design/MOVEMENT_BIBLE.md` (all sections, especially §2, §3, §8–§13); `ADRs/0004-movement-architecture.md`; `SPEC.md` §3.5, §3.6, §3.11, §6, §11; DESIGN_SYSTEM decisions 1, 5 and 10; Design Skills §3.7, §3.12 and §4; `config/movement.json`.

## A. Character controller feel and platformer craft

1. **Creating First Person Movement for MIRROR'S EDGE (DICE, GDC Vault)** — <https://www.gdcvault.com/play/1012171/Creating-First-Person-Movement-for> · *talk* — Vaults, wall-runs and grabs driven by context; the reference for contextual traversal verbs.
2. **Feel the World: The DualSense Experience Behind ASTRO BOT (GDC Vault)** — <https://www.gdcvault.com/play/1035347/Feel-the-World-The-DualSense> · *talk* — Team Asobi's haptic and feedback tooling, the model for Bible §9's per-event feedback table.
3. **"It's okay to make a small game" — Astro Bot director Nicolas Doucet (Game Developer)** — <https://www.gamedeveloper.com/design/-it-s-okay-to-make-a-small-game-astro-bot-director-nicolas-doucet-says-tiny-ideas-contain-huge-potential> · *doc* — Prototype-first, small-idea design; supports the M0 verb slice before content.
4. **Unity Scripting API — Application.targetFrameRate** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Application-targetFrameRate.html> · *doc* — Locking 30/60 fps on iOS; the 30 fps floor in SPEC §6.
5. **Unity Splines package** — <https://docs.unity3d.com/Packages/com.unity.splines@2.6/manual/index.html> · *doc* — Authoring pole/cable paths and camera rails in Tier 2 tests.
6. **Unity Cinemachine source** — <https://github.com/Unity-Technologies/com.unity.cinemachine> · *repo* — Source for the deoccluder and damping maths when the camera needs custom behaviour.
7. **Why Does Celeste Feel So Good to Play? (Game Maker's Toolkit)** — <https://www.youtube.com/watch?v=yorTG9at90g> · *talk* — Named in Bible §15: acceleration curves, coyote time, buffering, corner correction; the forgiveness GJ encodes in `jump.coyoteMs`/`bufferMs`.
8. **Celeste & TowerFall physics (Maddy Thorson)** — <https://maddythorson.medium.com/celeste-and-towerfall-physics-d24bd2ae0fc5> · *doc* — Named in Bible §15: simple, deterministic actor/solid collision that makes platforming precise.
9. **Math for Game Programmers: Building a Better Jump (Kyle Pittman, GDC Vault)** — <https://www.gdcvault.com/play/1023559/Math-for-Game-Programmers-Building> · *talk* — Designing jumps from height and distance rather than raw velocity, exactly how Bible §10 specifies jumps in A.
10. **Juice it or lose it (Jonasson and Purho)** — <https://www.youtube.com/watch?v=Fy0aCDmgnxg> · *talk* — How feedback layers (particles, shake, sound) change perceived feel; context for Tier 0.
11. **The art of screenshake (Jan Willem Nijman)** — <https://www.youtube.com/watch?v=AJdEqssNZ-U> · *talk* — Restraint and timing for camera shake, used only on hard landings and flag plants (Bible §9).
12. **Platformer Toolkit (Game Maker's Toolkit)** — <https://gmtk.itch.io/platformer-toolkit> · *doc* — Interactive demo of acceleration, jump curves and assists for tuning experiments.
13. **GDC Vault — 50 Camera Mistakes (John Nesky)** — <https://gdcvault.com/play/1020460/50-Camera> · *talk* — Named in Bible §15: the camera failure catalogue behind Bible §8's rules.
14. **50 Game Camera Mistakes (YouTube mirror)** — <https://www.youtube.com/watch?v=C7307qRmlMI> · *talk* — Free mirror of the same talk for quick reference.
15. **Scroll Back: The Theory and Practice of Cameras in Side-Scrollers (Itay Keren)** — <https://www.gamedeveloper.com/design/scroll-back-the-theory-and-practice-of-cameras-in-side-scrollers> · *doc* — Camera-window and look-ahead techniques; the look-ahead 0.8A rule in Bible §8.
16. **Unity Cinemachine manual** — <https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/index.html> · *doc* — Collision-aware follow, deoccluders and damping for the Bible §8 camera.

## B. Parkour and climbing systems

17. **Scaling New Heights — Jusant's climbing system (Don't Nod)** — <https://dont-nod.com/en/scaling-new-heights-learn-more-about-jusants-innovative-climbing-system/> · *postmortem* — A climbing-first game's grip/stamina design notes; a contrast to GJ's stamina-free Tier 0.
18. **Unlocking the catharsis of climbing in Jusant (Game Developer)** — <https://www.gamedeveloper.com/design/unlocking-the-catharsis-of-climbing-in-meditative-puzzler-jusant> · *postmortem* — Why deliberate, weighty climbing reads as satisfying; the Bible §0 feel bar.
19. **The Challenging Climb To Make Jusant (Game Informer)** — <https://gameinformer.com/2023/11/29/the-challenging-climb-to-make-jusant> · *postmortem* — Prototyping pains of a climbing system: many iterations before it felt right.
20. **GDC Vault — Animation Bootcamp: Animating The 3rd Assassin** — <https://www.gdcvault.com/play/1031894/Animation-Bootcamp-Animating-The-3rd> · *talk* — Assassin's Creed III climbing and free-running: anticipation over reaction, the Bible §0 "weight and hesitation" bar.
21. **Wolfire — GDC13 Animation Bootcamp summary (Assassin's Creed)** — <https://www.wolfire.com/blog/2013/04/GDC13-Summary-Animation-Bootcamp-Part-4-6/> · *doc* — Written summary: IK hand/foot placement plus a procedural body layer for jumps and landings.
22. **GDC Vault — Change and Constant: Breaking Conventions with Zelda: Breath of the Wild** — <https://gdcvault.com/play/1024562/Change-and-Constant-Breaking-Conventions> · *talk* — "Climb anything" and its level-design consequences; relevant because every scanned surface is climbable by class.
23. **UpRoom Games — Procedural climbing devlog** — <https://www.uproomgames.com/dev-log/procedural-climbing> · *postmortem* — IK + spring procedural climbing by a small team, close to Bible §6.3–6.5 procedural climbs.
24. **Kinemation — Motion Warping for Unity docs** — <https://kinemation.gitbook.io/motion-warping-for-unity> · *doc* — Docs for the one approved paid asset (AUTH #001): warp providers, mantle/vault components.
25. **Kinemation — Mantle component** — <https://kinemation.gitbook.io/motion-warping-for-unity/components/mantle-component> · *doc* — Min/max height and edge-space checks that must be fed from movement.json, not hand-typed.
26. **Motion Warping: Climb & Interact (Unity Asset Store)** — <https://assetstore.unity.com/packages/tools/animation/motion-warping-climb-interact-270046> · *vendor guide* — The AUTH #001 purchase; record version and licence per SECURITY_CHECKLIST §7.4 (M1-MOVE-01 AT-3).
27. **Unreal Engine — Motion Warping documentation** — <https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-warping-in-unreal-engine> · *doc* — Named in Bible §15: the canonical explanation of warp windows and targets.
28. **Unity Manual — Animator.MatchTarget** — <https://docs.unity3d.com/ScriptReference/Animator.MatchTarget.html> · *doc* — Built-in target matching; the fallback if the warp asset fails ("root-motion scaling + IK", Bible §2).

## C. Motion matching, inertialization and animation tech

29. **Unity Manual — How Root Motion works** — <https://docs.unity3d.com/6000.0/Documentation/Manual/RootMotion.html> · *doc* — Root-motion extraction that warping and the "root-motion scaling + IK" fallback depend on.
30. **Unity Manual — Animator Controllers** — <https://docs.unity3d.com/6000.0/Documentation/Manual/class-AnimatorController.html> · *doc* — The blend-tree baseline M1-MOVE-01 benchmarks motion matching against.
31. **GDC Vault — Motion Matching: The Future of Games Animation...Today (Kristjan Zadziuk)** — <https://www.gdcvault.com/play/1023478/Animation-Bootcamp-Motion-Matching-The> · *talk* — Clip-capture planning (dance cards) for a matching DB; guides the ~110-clip list in Bible §11.
32. **GDC Vault — Character Control with Neural Networks and Machine Learning (Daniel Holden)** — <https://www.gdcvault.com/play/1025389/Character-Control-with-Neural-Networks> · *talk* — Terrain-aware learned locomotion; background, not a v1 path.
33. **Unity Manual — Mecanim performance and optimization** — <https://docs.unity3d.com/6000.0/Documentation/Manual/MecanimPeformanceandOptimization.html> · *doc* — Animator costs to keep the ≤ 4 ms animation budget (Bible §2).
34. **Kinemation on GitHub** — <https://github.com/Kinemation> · *repo* — Public samples from the Motion Warping vendor.
35. **GDC Vault — Motion Matching and The Road to Next-Gen Animation (Simon Clavet)** — <https://gdcvault.com/play/1023280/Motion-Matching-and-The-Road> · *talk* — Named in Bible §15: the origin of motion matching (Ubisoft, GDC 2016).
36. **GDC Vault — Inertialization: High-Performance Animation Transitions in Gears of War (David Bollo)** — <https://gdcvault.com/play/1025165/Inertialization-High-Performance-Animation-Transitions> · *talk* — Named in Bible §15: the blending method that covers the every-3rd-frame search gap (Bible §2).
37. **Learned Motion Matching (Holden et al.)** — <https://theorangeduck.com/page/learned-motion-matching> · *paper* — Named in Bible §15: compressing the motion DB; relevant to the ≤ 60 MB budget.
38. **Code vs Data Driven Displacement (Daniel Holden)** — <https://theorangeduck.com/page/code-vs-data-driven-displacement> · *doc* — How character motion and animation displacement interact; key for responsiveness vs realism.
39. **Spring-It-On: The Game Developer's Spring-Roll-Call (Daniel Holden)** — <https://theorangeduck.com/page/spring-roll-call> · *doc* — Critically damped springs and inertialization math for camera and blending.
40. **Dead Blending (Daniel Holden)** — <https://theorangeduck.com/page/dead-blending> · *doc* — An alternative to inertialization for transitions; worth benchmarking in M1-MOVE-01.
41. **Motion Matching implementation for Unity (JLPM22)** — <https://github.com/JLPM22/MotionMatching> · *repo* — The open MIT matcher named in Bible §2 for the M1-MOVE-01 spike.
42. **Orange Duck Motion Matching sample code** — <https://github.com/orangeduck/Motion-Matching> · *repo* — Reference implementation with feature normalization and inertialization.
43. **Phase-Functioned Neural Networks for Character Control** — <https://theorangeduck.com/page/phase-functioned-neural-networks-character-control> · *paper* — Learned locomotion on rough terrain; background for foot placement on uneven splat meshes.
44. **Unity Animation Rigging manual** — <https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/index.html> · *doc* — The procedural layer (foot/hand IK, look-at) in Bible §2; pinned 1.4.1 in Packages/manifest.json.
45. **Unity Manual — Playables API** — <https://docs.unity3d.com/Manual/Playables.html> · *doc* — Low-level animation graph a custom motion matcher plugs into.
46. **Unity Manual — Humanoid avatars and retargeting** — <https://docs.unity3d.com/Manual/AvatarCreationandSetup.html> · *doc* — Humanoid mapping that lets one clip set drive the whole roster (SPEC §3.2).
47. **Mixamo** — <https://www.mixamo.com/> · *vendor guide* — Free clip source for the Bible §11 whitelist (~110 clips).
48. **Cascadeur** — <https://cascadeur.com/> · *vendor guide* — Physics-assisted cleanup of Owner and Move.ai captures (Bible §12 step 3).
49. **Rokoko Vision** — <https://www.rokoko.com/products/vision> · *vendor guide* — Single-camera capture for the Owner reaction clips (Bible §7).
50. **Move.ai** — <https://www.move.ai/> · *vendor guide* — iPhone mocap trial for hero clips (Bible §7); paid tiers are deferred to V2 (AUTH #001).
51. **Blender manual — Animation and rigging** — <https://docs.blender.org/manual/en/latest/animation/index.html> · *doc* — Retarget and foot-slide fixes in Bible §12 step 2.

## D. Unity 6 URP mobile performance

52. **Apple — ProcessInfo.ThermalState** — <https://developer.apple.com/documentation/foundation/processinfo/thermalstate> · *doc* — Thermal state to drive quality drops before the frame rate falls below 30 fps.
53. **Unity Manual — Optimize performance for iOS** — <https://docs.unity3d.com/6000.0/Documentation/Manual/iphone-performance.html> · *doc* — iOS-specific CPU/GPU/thermal guidance for the SPEC §6 device targets.
54. **Unity Manual — Optimize the size of the iOS Player** — <https://docs.unity3d.com/6000.0/Documentation/Manual/iphone-playerSizeOptimization.html> · *doc* — Keeping the app lean under the motion DB and audio budgets.
55. **Unity Manual — Optimizing code for managed memory** — <https://docs.unity3d.com/6000.0/Documentation/Manual/performance-garbage-collection-best-practices.html> · *doc* — No per-frame allocations in intent/query code; GC spikes show up as hitches.
56. **Unity Manual — Best practice guides** — <https://docs.unity3d.com/6000.0/Documentation/Manual/best-practice-guides.html> · *doc* — Index of Unity's official optimization guides.
57. **Unity Manual — URP asset reference** — <https://docs.unity3d.com/6000.0/Documentation/Manual/urp/universalrp-asset.html> · *doc* — Quality tiers (shadows, render scale) for the device matrix.
58. **Unity Manual — Profiler markers reference** — <https://docs.unity3d.com/6000.0/Documentation/Manual/profiler-markers.html> · *doc* — Reading the built-in markers when attributing frame time.
59. **Unity Profiling Core API** — <https://docs.unity3d.com/Packages/com.unity.profiling.core@1.0/manual/index.html> · *doc* — Custom ProfilerMarkers per movement layer so the overlay can show per-layer ms.
60. **Unity Manual — Custom scripting symbols** — <https://docs.unity3d.com/6000.0/Documentation/Manual/custom-scripting-symbols.html> · *doc* — How the `GJ_DEBUG` define strips the overlay from release builds (M0-UNITY-04 AT-1).
61. **Unity Manual — Scripting symbol reference** — <https://docs.unity3d.com/6000.0/Documentation/Manual/scripting-symbol-reference.html> · *doc* — Built-in platform defines (UNITY_IOS, DEVELOPMENT_BUILD) to combine with GJ_DEBUG.
62. **Unity Scripting API — ScriptableObject** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/ScriptableObject.html> · *doc* — Typed runtime container for movement.json values (never hand-edited, Bible §10).
63. **Unity Test Framework 1.6 manual** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.6/manual/index.html> · *doc* — EditMode/PlayMode tests that back the `unity tests gate` required check.
64. **Unity Input System source** — <https://github.com/Unity-Technologies/InputSystem> · *repo* — Source and samples for touch and gamepad handling.
65. **Unity — Optimize performance for mobile, XR and web games (Unity 6 edition)** — <https://unity.com/resources/mobile-xr-web-game-performance-optimization-unity-6> · *vendor guide* — Unity's mobile performance e-book for the SPEC §6 targets.
66. **Unity 6 Manual — Introduction to URP** — <https://docs.unity3d.com/6000.0/Documentation/Manual/urp/urp-introduction.html> · *doc* — The pinned URP version (17.0.4) and its renderer features.
67. **Unity Manual — Profiler overview** — <https://docs.unity3d.com/Manual/Profiler.html> · *doc* — Evidence source for the animation ≤ 4 ms and frame-time readouts (advisory, SPEC §11).
68. **Unity Manual — Profiling on a target device** — <https://docs.unity3d.com/Manual/profiler-profiling-applications.html> · *doc* — Connecting the Profiler to an iPhone build.
69. **Unity Memory Profiler package** — <https://docs.unity3d.com/Packages/com.unity.memoryprofiler@1.1/manual/index.html> · *doc* — Checking the motion DB and audio bank against memory budgets.
70. **Unity Manual — Frame Timing Manager** — <https://docs.unity3d.com/Manual/frame-timing-manager.html> · *doc* — CPU/GPU frame times for the debug overlay (M0-UNITY-04 AT-1).
71. **Unity Manual — Adaptive Performance (iOS/Apple)** — <https://docs.unity3d.com/Packages/com.unity.adaptiveperformance@5.1/manual/index.html> · *doc* — Thermal and quality-tier scaling toward 30 fps on older iPhones (SPEC §6).
72. **Unity Burst manual** — <https://docs.unity3d.com/Packages/com.unity.burst@1.8/manual/index.html> · *doc* — Burst AOT (enabled on iOS, M3-UNITY-01) for the motion-matching search job.
73. **Unity Job System manual** — <https://docs.unity3d.com/Manual/job-system.html> · *doc* — Running the every-3rd-frame search off the main thread (Bible §2).
74. **Unity Input System manual** — <https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/index.html> · *doc* — Touch stick + gamepad feeding one intent layer (M0-UNITY-03 AT-5).
75. **Unity Input System — On-screen controls** — <https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/OnScreen.html> · *doc* — On-screen stick and button components for the two-thumb layout.
76. **Unity Manual — Assembly definitions** — <https://docs.unity3d.com/Manual/assembly-definition-files.html> · *doc* — The five movement assemblies plus GJ.Movement.Shared (M0-UNITY-03 AT-1, REVIEW_RUBRIC E1).
77. **Unity Manual — Physics queries (Physics.CapsuleCast etc.)** — <https://docs.unity3d.com/ScriptReference/Physics.CapsuleCast.html> · *doc* — Traversal-query casts against the collision mesh (Bible §2 layer 2).
78. **Unity Manual — CharacterController** — <https://docs.unity3d.com/Manual/class-CharacterController.html> · *doc* — Step offset and slope limits; compare with a custom kinematic controller.
79. **Kinematic Character Controller (Unity Asset Store)** — <https://assetstore.unity.com/packages/tools/physics/kinematic-character-controller-99131> · *repo* — Open kinematic controller with deterministic collision handling, a strong reference design.
80. **Apple — Metal developer tools** — <https://developer.apple.com/metal/tools/> · *doc* — GPU frame capture and counters for splat + character cost on device.
81. **Apple — Game Controller framework** — <https://developer.apple.com/documentation/gamecontroller> · *doc* — Backbone-style controllers on iOS (controller support from day one, SPEC §3.5).

## E. Splat rendering integration in gameplay

82. **aras-p/UnityGaussianSplatting** — <https://github.com/aras-p/UnityGaussianSplatting> · *repo* — The MIT renderer the player runs over; depth and occlusion interplay with the character.
83. **UnityGaussianSplatting issue #226 (Metal sort)** — <https://github.com/aras-p/UnityGaussianSplatting/issues/226> · *doc* — The iOS sort bug; gameplay profiling must assume the render fix is still open (M1-UNITY-01).
84. **scier/MetalSplatter** — <https://github.com/scier/MetalSplatter> · *repo* — Native Metal fallback (Option B) that changes how the character pass composites.
85. **Unity URP — Render Graph system** — <https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/render-graph.html> · *doc* — Where character, splat and dither-fade passes are ordered.
86. **Unity UniversalRenderingExamples (custom renderer features)** — <https://github.com/Unity-Technologies/UniversalRenderingExamples> · *repo* — Implementing the always-on-top beacon/sparkle with depth-fade (Bible §8).
87. **Unity URP — Decal Renderer Feature** — <https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/renderer-feature-decal.html> · *doc* — Candidate for the contact shadow that grounds the 1:12 character (Design Skills rule 20).
88. **Dither transparency / screen-door fade (Unity Shader Graph Dither node)** — <https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/Dither-Node.html> · *doc* — Dither-fade of occluding geometry within 1.5A of the lens (Bible §8).

## F. Procedural animation and IK

89. **Damped Transform constraint (Animation Rigging)** — <https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/constraints/DampedTransform.html> · *doc* — Secondary motion (backpack, hair) that sells weight at 1:12 scale.
90. **An Indie Approach to Procedural Animation (David Rosen, GDC 2014)** — <https://www.gdcvault.com/play/1020583/Animation-Bootcamp-An-Indie-Approach> · *talk* — Springs and few keyframes for convincing procedural motion; model for the stud/free/pole climb cycles.
91. **Foot IK on uneven terrain (Unity Animation Rigging two-bone IK constraint)** — <https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/constraints/TwoBoneIKConstraint.html> · *doc* — The constraint for foot IK on bumpy splat-derived meshes.
92. **Multi-Aim constraint (look-at)** — <https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/constraints/MultiAimConstraint.html> · *doc* — Look-at for summit beam, vistas and ledges (Bible §2, §7).

## G. Audio on mobile (Tier 0 and the AUTH #022 sound system)

93. **Unity Scripting API — Handheld.Vibrate** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Handheld.Vibrate.html> · *doc* — The built-in (coarse) vibration fallback; Core Haptics is needed for light/medium/heavy.
94. **Unity Manual — Audio overview** — <https://docs.unity3d.com/Manual/AudioOverview.html> · *doc* — Built-in audio (mixer groups, spatializer) available with no middleware spend.
95. **Unity Manual — Audio Mixer** — <https://docs.unity3d.com/Manual/AudioMixer.html> · *doc* — Category buses and ducking (movement/world/tools/UI/music) per M1-GAME-04 AT-3.
96. **Unity Manual — Audio Reverb Zone** — <https://docs.unity3d.com/Manual/class-AudioReverbZone.html> · *doc* — Parametric reverb that scale-aware acoustics can drive from room volume (M1-GAME-04 AT-2).
97. **Unity Manual — Audio clip import settings** — <https://docs.unity3d.com/Manual/class-AudioClip.html> · *doc* — Compression and load types for the mobile memory/polyphony budget (M1-GAME-04 AT-4).
98. **FMOD for Unity documentation** — <https://www.fmod.com/docs/2.03/unity/welcome.html> · *doc* — Middleware option; its licence tiers mean adoption is an AUTH.
99. **Audiokinetic Wwise documentation library (incl. Unity integration)** — <https://www.audiokinetic.com/en/public-library/> · *doc* — The other middleware option; also AUTH-gated if licensed.
100. **Steam Audio Unity integration** — <https://valvesoftware.github.io/steam-audio/doc/unity/index.html> · *doc* — Free geometry-aware reverb and spatialization; candidate for room-derived acoustics.
101. **Resonance Audio (archived)** — <https://github.com/resonance-audio/resonance-audio> · *repo* — Open spatializer with room models; check maintenance status before use.
102. **Freesound (CC0 filter)** — <https://freesound.org/> · *vendor guide* — CC0 source for the material × event bank; record provenance per clip (M1-GAME-04 AT-4).
103. **Apple — Core Haptics** — <https://developer.apple.com/documentation/corehaptics> · *doc* — Light/medium/heavy haptic patterns mapped to Bible §9 events.
104. **Apple HIG — Playing haptics** — <https://developer.apple.com/design/human-interface-guidelines/playing-haptics> · *doc* — Restraint rules for haptics and the settings toggle (DESIGN_SYSTEM decision 10).
