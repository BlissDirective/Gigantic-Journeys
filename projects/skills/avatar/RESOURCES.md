# gj-avatar — Resources

The annotated research list for the avatar hat. Research focus is from kit §3: image-to-3D avatar pipelines, parametric body models, auto-rigging, likeness preservation, uncanny valley at small scale, texture baking for mobile, and biometric privacy requirements (BIPA). Since AUTH #020 / ADR-0006, v1 ships a curated roster with **no biometric processing**, so groups A–D (authoring, rig standard, retopo/bake, shading) serve v1. Groups E–G (image-to-3D, likeness, biometric law) serve the V2 custom-avatar track (`research/rnd/README.md`) and the one v1 item that remains, the 13+ gate. Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26: HTTP 200 plus a page-title check, and arXiv titles were checked against the abstract page. Statute links point to Justia or state-AG mirrors because the state legislature sites timed out from the check host. **Licences are the real constraint:** SMPL/SMPL-X, BFM, DECA/EMOCA/MICA weights, PIFuHD/ECON, PanoHead and InsightFace models are non-commercial and must not ship. Vendor and tool links are references, not approvals: any purchase needs a spend AUTH (AUTH #024 approved $0). Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first: `ADRs/0006-v1-avatar-curated-character-roster.md`; SPEC §3.2, §3.8, §7; DESIGN_SYSTEM decision 4; `design/proposals/character-roster-v1.md`; `research/vendors/character-roster-sourcing.md`; `research/rnd/README.md`; SECURITY_CHECKLIST §5–§7.

## A. v1 character authoring: open bases, licensed tools and the clean-IP gate

1. **MakeHuman (MakeHuman Community)** — <https://static.makehumancommunity.org/makehuman.html> · *vendor guide* — The CC0-asset base for the primary open-base track (AUTH #024; research/vendors/character-roster-sourcing.md §3).
2. **MakeHuman source (GitHub)** — <https://github.com/makehumancommunity/makehuman> · *repo* — The app is AGPL but exported models are CC0; read the licence split before building tools around it.
3. **MPFB2 — MakeHuman plugin for Blender** — <https://github.com/makehumancommunity/mpfb2> · *repo* — Generates MakeHuman bases directly in Blender, where the uplift, retopo and rigging happen.
4. **Human Generator (Blender add-on)** — <https://www.humgen3d.com/> · *vendor guide* — The other open-base candidate named in AUTH #024; paid one-time, so buying it needs a spend AUTH.
5. **MB-Lab (Blender parametric humans)** — <https://github.com/animate1978/MB-Lab> · *repo* — Parametric base option in the sourcing doc; verify the current fork's asset licence before use.
6. **Reallusion Character Creator 4** — <https://www.reallusion.com/character-creator/> · *vendor guide* — The contingency licence track (CC4 + Mixamo); its own spend AUTH if used (SPEC §3.2).
7. **Mixamo** — <https://www.mixamo.com/> · *vendor guide* — Free auto-rigger and characters for pipeline bring-up, and the source of the Bible §11 clips.
8. **Daz 3D Interactive License info** — <https://www.daz3d.com/interactive-license-info> · *doc* — Why Daz is case-by-case: game embedding needs per-asset Interactive Licenses (sourcing doc §2).
9. **MetaHuman (Epic)** — <https://www.metahuman.com/> · *vendor guide* — Rejected for v1: the licence restricts use to Unreal Engine, so it cannot ship in a Unity build.
10. **Blender Manual** — <https://docs.blender.org/manual/en/latest/> · *doc* — The in-house authoring tool for the open-base track (sculpt, retopo, bake, rig, export).
11. **Blender Python API** — <https://docs.blender.org/api/current/> · *doc* — Scripted, repeatable export and pre-checks (bone names, scale, sockets) before Unity import.
12. **Blender Manual — Command line arguments** — <https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html> · *doc* — Headless Blender for batch exports in CI or on the QA VM.
13. **glTF 2.0 (Khronos, spec and samples)** — <https://github.com/KhronosGroup/glTF> · *doc* — Interchange format option alongside FBX; defines skins, morph targets and PBR materials.
14. **VRM specification** — <https://vrm.dev/en/> · *doc* — An existing humanoid avatar standard (bone list, expressions) useful as a checklist when writing the GJ rig contract.
15. **UniVRM (Unity VRM importer)** — <https://github.com/vrm-c/UniVRM> · *repo* — Shows how a humanoid standard maps onto Unity Humanoid; reference only.

## B. The rig standard, retargeting and rig validation

16. **Unity Manual — Humanoid Avatar** — <https://docs.unity3d.com/Manual/AvatarCreationandSetup.html> · *doc* — The Unity Humanoid mapping every character must satisfy (SPEC §3.2 rig standard).
17. **Unity Manual — Avatar Mapping tab** — <https://docs.unity3d.com/Manual/class-Avatar.html> · *doc* — Required vs optional bones and T-pose enforcement, the core of the rig-conformance gate.
18. **Unity Manual — Retargeting Humanoid animations** — <https://docs.unity3d.com/Manual/Retargeting.html> · *doc* — Why one clip set can drive all eight characters with no per-character fixes (M2-AVAT-01 AT-1).
19. **Unity Manual — Model import Rig tab** — <https://docs.unity3d.com/Manual/FBXImporter-Rig.html> · *doc* — Import settings (Humanoid, avatar definition, skin weights) to lock in an AssetPostprocessor.
20. **Unity Scripting API — AssetPostprocessor** — <https://docs.unity3d.com/ScriptReference/AssetPostprocessor.html> · *doc* — Hook for an automated import-time rig-conformance check.
21. **Unity Scripting API — Avatar.isHuman** — <https://docs.unity3d.com/ScriptReference/Avatar-isHuman.html> · *doc* — A basic gate assertion: the imported avatar is a valid humanoid.
22. **Unity Scripting API — HumanTrait** — <https://docs.unity3d.com/ScriptReference/HumanTrait.html> · *doc* — Enumerates humanoid bones and required flags so the gate can check bone coverage.
23. **Unity Scripting API — AvatarBuilder** — <https://docs.unity3d.com/ScriptReference/AvatarBuilder.html> · *doc* — Building avatars from a description in code, for consistent mapping across the roster.
24. **Unity Scripting API — Animator.GetBoneTransform** — <https://docs.unity3d.com/ScriptReference/Animator.GetBoneTransform.html> · *doc* — Measuring eye height and scale against 1A in an EditMode test.
25. **Unity Manual — Skinned Mesh Renderer** — <https://docs.unity3d.com/Manual/class-SkinnedMeshRenderer.html> · *doc* — Bone influences and update cost for mobile skinning budgets.
26. **Unity Manual — Blend shapes** — <https://docs.unity3d.com/Manual/BlendShapes.html> · *doc* — The small reactive-idle blendshape set (SPEC §3.2: no full FACS).
27. **Unity Animation Rigging — Two Bone IK** — <https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/constraints/TwoBoneIKConstraint.html> · *doc* — The foot and hand IK targets the rig standard must expose (Bible §2 procedural layer).
28. **Blender Manual — Rigify** — <https://docs.blender.org/manual/en/4.1/addons/rigging/rigify/index.html> · *doc* — Blender's rig generator; export a clean deform skeleton, not the control rig.
29. **Blender Manual — Armatures** — <https://docs.blender.org/manual/en/latest/animation/armatures/index.html> · *doc* — Bone naming, roll and rest pose for a consistent export.
30. **Blender Manual — Weight Paint** — <https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/index.html> · *doc* — Painting and fixing skin weights so outfits and the body deform together on the shared rig.
31. **Robust Skin Weights Transfer via Weight Inpainting (code)** — <https://github.com/rin-23/RobustSkinWeightsTransferCode> · *repo* — Better weight transfer for outfits on rig-clean silhouettes (cosmetic clip test).
32. **RigNet: Neural Rigging for Articulated Characters** — <https://arxiv.org/abs/2005.00559> · *paper* — Learned auto-rigging; background for the V2 per-user rig step.
33. **Automatic Rigging and Animation of 3D Characters (Pinocchio, Baran and Popović)** — <https://people.csail.mit.edu/ibaran/papers/2007-SIGGRAPH-Pinocchio.pdf> · *paper* — The classic skeleton-embedding + heat-weights method most auto-riggers descend from.
34. **Make-It-Animatable: An Efficient Framework for Authoring Animation-Ready 3D Characters** — <https://arxiv.org/abs/2411.18197> · *paper* — Fast learned rigging of arbitrary humanoid meshes; relevant to V2 generated avatars.

## C. Retopology, LODs and texture baking for mobile

35. **Blender Manual — Object modifiers** — <https://docs.blender.org/manual/en/latest/modeling/modifiers/index.html> · *doc* — Index of the modifiers (decimate, shrinkwrap, remesh, data transfer) used in the retopo and outfit pipeline.
36. **Blender Manual — Decimate modifier** — <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/decimate.html> · *doc* — Quick LOD generation for the per-character poly budget.
37. **Blender Manual — Shrinkwrap modifier** — <https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/shrinkwrap.html> · *doc* — Projects retopo meshes onto the sculpt during manual retopology.
38. **Blender Manual — Remesh modifier** — <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/remesh.html> · *doc* — Voxel/quad remeshing before retopo on generated or sculpted bases.
39. **Blender Manual — Render baking (Cycles)** — <https://docs.blender.org/manual/en/latest/render/cycles/baking.html> · *doc* — Baking normal, AO and diffuse maps from high to low poly.
40. **Instant Meshes** — <https://github.com/wjakob/instant-meshes> · *repo* — Free field-aligned quad remesher; a fast first pass at retopology.
41. **QuadriFlow: A Scalable and Robust Method for Quadrangulation** — <https://github.com/hjwdzh/QuadriFlow> · *repo* — The quad remesher built into Blender; know its limits on faces and hands.
42. **Exoside Quad Remesher** — <https://exoside.com/> · *vendor guide* — Commercial auto-retopo often used on characters; a paid tool needs an AUTH.
43. **meshoptimizer** — <https://github.com/zeux/meshoptimizer> · *repo* — MIT mesh simplification and vertex-cache optimization for LODs.
44. **Polycount wiki — Normal map** — <http://wiki.polycount.com/wiki/Normal_map> · *doc* — Tangent space, cages and seams: the common baking mistakes.
45. **Polycount wiki — Texture atlas** — <http://wiki.polycount.com/wiki/Texture_atlas> · *doc* — Atlasing to keep material count and draw calls down on mobile.
46. **Marmoset Toolbag** — <https://marmoset.co/toolbag/> · *vendor guide* — Industry baking and look-dev tool; paid, so an AUTH if adopted.
47. **Unity Manual — LOD Group** — <https://docs.unity3d.com/Manual/class-LODGroup.html> · *doc* — Swapping character LODs by screen size; the 1:12 avatar is small on screen most of the time.
48. **Unity Manual — Texture compression formats** — <https://docs.unity3d.com/Manual/class-TextureImporterOverride.html> · *doc* — ASTC block sizes for iOS character textures.
49. **ARM ASTC Encoder** — <https://github.com/ARM-software/astc-encoder> · *repo* — The reference ASTC compressor; understand quality vs block size.
50. **Unity Manual — Graphics performance fundamentals** — <https://docs.unity3d.com/Manual/OptimizingGraphicsPerformance.html> · *doc* — Draw calls, overdraw and skinning costs that set the mobile character budget.
51. **Unity Manual — Optimize performance for iOS** — <https://docs.unity3d.com/6000.0/Documentation/Manual/iphone-performance.html> · *doc* — iOS-specific guidance so the character keeps the 30 fps floor with Tier 0/1 on.

## D. Character shading in URP (grounded semi-photoreal)

52. **Unity URP — Lit shader** — <https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/lit-shader.html> · *doc* — The baseline PBR material the unified character shader builds on.
53. **Unity Shader Graph manual** — <https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/index.html> · *doc* — Authoring the unified character shader, including rim light.
54. **Shader Graph — Fresnel Effect node** — <https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/Fresnel-Effect-Node.html> · *doc* — The standard building block for the warm rim light (DESIGN_SYSTEM decision 1, Design Skills rule 20).
55. **Unity Manual — Light Probes** — <https://docs.unity3d.com/Manual/LightProbes.html> · *doc* — Lighting a dynamic character from probes; the environment probe from the splat feeds this idea.
56. **Unity Manual — Reflection probes** — <https://docs.unity3d.com/Manual/ReflectionProbes.html> · *doc* — Specular environment lighting so materials sit in the captured room.
57. **Unity URP — Adaptive Probe Volumes** — <https://docs.unity3d.com/6000.0/Documentation/Manual/urp/probevolumes.html> · *doc* — Per-pixel probe lighting in Unity 6 URP; weigh cost vs benefit for one character.
58. **Unity URP — Decal Renderer Feature** — <https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/renderer-feature-decal.html> · *doc* — A candidate for the contact shadow under the character.
59. **Real Shading in Unreal Engine 4 (Karis, SIGGRAPH 2013 notes)** — <https://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf> · *paper* — The PBR model most real-time skin/cloth shading assumes.
60. **SIGGRAPH Physically Based Shading course archive** — <https://blog.selfshadow.com/publications/> · *doc* — Course notes on skin, hair and cloth shading for the realism+ tier.
61. **Advances in Real-Time Rendering, SIGGRAPH 2011 (incl. Penner, Pre-Integrated Skin Shading)** — <https://advances.realtimerendering.com/s2011/index.html> · *talk* — A cheap mobile-friendly skin approximation for the realism+ material tier.

## E. Image-to-3D and parametric human models (V2 custom-avatar track)

62. **SMPL body model** — <https://smpl.is.tue.mpg.de/> · *doc* — The most-cited parametric body; weights are non-commercial, so it is reference only (research/rnd/README.md).
63. **Expressive Body Capture: 3D Hands, Face, and Body from a Single Image (SMPL-X)** — <https://arxiv.org/abs/1904.05866> · *paper* — Body + hands + face model; non-commercial licence, background only.
64. **FLAME: Learning a model of facial shape and expression from 4D scans** — <https://flame.is.tue.mpg.de/> · *doc* — FLAME-2023-Open geometry is CC-BY and a candidate V2 base; textures are not (research/rnd/README.md).
65. **ICT-FaceKit** — <https://github.com/ICT-VGL/ICT-FaceKit> · *repo* — MIT face model named as the commercial-clean synthetic data base for V2.
66. **STAR: Sparse Trained Articulated Human Body Regressor** — <https://arxiv.org/abs/2008.08535> · *paper* — A compact SMPL successor; check licence before any use.
67. **GHUM & GHUML: Generative 3D Human Shape and Articulated Pose Models** — <https://github.com/google-research/google-research/tree/master/ghum> · *repo* — Google's body model; licence and fit for V2 to be checked.
68. **PIFu: Pixel-Aligned Implicit Function for High-Resolution Clothed Human Digitization** — <https://arxiv.org/abs/1905.05172> · *paper* — Single-image clothed human reconstruction; the lineage of image-to-body pipelines.
69. **PIFuHD: Multi-Level Pixel-Aligned Implicit Function for High-Resolution 3D Human Digitization** — <https://arxiv.org/abs/2004.00452> · *paper* — Higher-detail PIFu; non-commercial weights (research/rnd/README.md).
70. **ECON: Explicit Clothed humans Optimized via Normal integration** — <https://arxiv.org/abs/2212.07422> · *paper* — Robust clothed-body recovery from one image; non-commercial.
71. **Learning an Animatable Detailed 3D Face Model from In-The-Wild Images (DECA)** — <https://arxiv.org/abs/2012.04012> · *paper* — Photo → FLAME face with detail; its weights are non-commercial (research/rnd/README.md).
72. **Towards Metrical Reconstruction of Human Faces (MICA)** — <https://arxiv.org/abs/2204.06607> · *paper* — Metric-scale face shape; relevant to correct head size at 1A.
73. **PanoHead: Geometry-Aware 3D Full-Head Synthesis in 360°** — <https://arxiv.org/abs/2303.13071> · *paper* — Full-head generation incl. the back of the head, the hard part of selfie capture.
74. **Humans in 4D: Reconstructing and Tracking Humans with Transformers** — <https://arxiv.org/abs/2305.20091> · *paper* — HMR 2.0 body shape from video; relevant to the V2 360° body capture.
75. **SMPLer-X: Scaling Up Expressive Human Pose and Shape Estimation** — <https://arxiv.org/abs/2309.17448> · *paper* — State-of-the-art body+face+hands estimation; check licence.
76. **GaussianAvatars: Photorealistic Head Avatars with Rigged 3D Gaussians** — <https://arxiv.org/abs/2312.02069> · *paper* — Splat-based rigged heads, a possible V2 fit with the splat renderer.
77. **LHM: Large Animatable Human Reconstruction Model from a Single Image in Seconds** — <https://arxiv.org/abs/2503.10625> · *paper* — Feed-forward animatable human from one photo; the kind of model the V2 track would train.
78. **InstantMesh: Efficient 3D Mesh Generation from a Single Image with Sparse-view Large Reconstruction Models** — <https://arxiv.org/abs/2404.07191> · *paper* — General image-to-mesh; background for "generate a base once" (proposal §5 path B).
79. **Microsoft TRELLIS** — <https://github.com/microsoft/TRELLIS> · *repo* — Open image-to-3D asset generation; check licence and resemblance risk before any use.
80. **Tencent Hunyuan3D-2** — <https://github.com/Tencent/Hunyuan3D-2> · *repo* — Open image-to-3D; its licence has territory and use limits, so read it before use.
81. **Meshy** — <https://www.meshy.ai/> · *vendor guide* — Dropped: its ToS bans identifiable-person photos and it trains by default (AUTH #019; research/vendors/meshy.md).
82. **Tripo** — <https://www.tripo3d.ai/> · *vendor guide* — The other original head vendor candidate, dropped with Meshy.
83. **Avatar SDK (itSeez3D)** — <https://avatarsdk.com/> · *vendor guide* — The on-prem vendor chosen by AUTH #019 and deferred to V2 by AUTH #020.

## F. Likeness preservation and the uncanny valley at small scale

84. **The Uncanny Valley: The Original Essay by Masahiro Mori (IEEE Spectrum)** — <https://spectrum.ieee.org/the-uncanny-valley> · *paper* — The source essay; why v1 faces are deliberately short of hyperreal (SPEC §3.2).
85. **A review of empirical evidence on different uncanny valley hypotheses (Kätsyri et al.)** — <https://www.frontiersin.org/articles/10.3389/fpsyg.2015.00390/full> · *paper* — Evidence that feature mismatch (realistic skin + odd eyes) drives eeriness.
86. **To Stylize or not to Stylize? The Effect of Shape and Material Stylization (Zell et al.)** — <https://dl.acm.org/doi/10.1145/2816795.2818126> · *paper* — Material realism vs shape stylization; guides "grounded semi-photoreal".
87. **Render me real? Investigating the effect of render style on the perception of animated virtual humans (McDonnell et al.)** — <https://dl.acm.org/doi/10.1145/2185520.2185587> · *paper* — Render style vs appeal and trust for animated humans.
88. **ArcFace: Additive Angular Margin Loss for Deep Face Recognition** — <https://arxiv.org/abs/1801.07698> · *paper* — The usual identity metric; InsightFace weights are non-commercial, so V2 needs a clean recogniser (research/rnd/README.md).
89. **InsightFace** — <https://github.com/deepinsight/insightface> · *repo* — Reference face-analysis toolkit; its model licences exclude commercial use without a deal.
90. **NIST Face Recognition Technology Evaluation (FRTE)** — <https://pages.nist.gov/frvt/html/frvt11.html> · *doc* — How identity-similarity is measured rigorously, background for the V2 blind test.
91. **Apple HIG — Accessibility** — <https://developer.apple.com/design/human-interface-guidelines/accessibility> · *doc* — Selection-screen accessibility (VoiceOver, Dynamic Type) for picking a character.

## G. Biometric privacy law and store policy (V2 gate; the 13+ gate is v1)

92. **Illinois Biometric Information Privacy Act (740 ILCS 14)** — <https://law.justia.com/codes/illinois/chapter-740/act-740-ilcs-14/> · *doc* — BIPA text: written consent, retention schedule and destruction duties behind SECURITY_CHECKLIST §5.
93. **Texas Capture or Use of Biometric Identifier Act (Bus. & Com. Code §503.001)** — <https://law.justia.com/codes/texas/business-and-commerce-code/title-11/subtitle-a/chapter-503/section-503-001/> · *doc* — CUBI text named in SECURITY_CHECKLIST §5.5.
94. **Washington My Health My Data Act (WA Attorney General guidance)** — <https://www.atg.wa.gov/protecting-washingtonians-personal-health-data-and-privacy> · *doc* — MHMDA, which treats biometric data as consumer health data.
95. **FTC warns about misuses of biometric information (2023 policy statement)** — <https://www.ftc.gov/news-events/news/press-releases/2023/05/ftc-warns-about-misuses-biometric-information-harm-consumers> · *doc* — FTC expectations on biometric collection, testing and disclosure.
96. **FTC — Everalbum case (facial recognition, algorithm deletion)** — <https://www.ftc.gov/legal-library/browse/cases-proceedings/192-3172-everalbum-inc-matter> · *postmortem* — Consequence of training on user faces without consent: models ordered deleted.
97. **Texas AG — $1.4B Meta settlement under CUBI (2024)** — <https://www.texasattorneygeneral.gov/news/releases/attorney-general-ken-paxton-secures-14-billion-settlement-meta-over-its-unauthorized-capture> · *postmortem* — Scale of CUBI exposure for face templates collected without consent.
98. **GDPR Article 9 — special categories of personal data** — <https://gdpr-info.eu/art-9-gdpr/> · *doc* — Biometric data for identification needs explicit consent in the EU.
99. **ICO — Biometric data guidance** — <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/biometric-data-guidance-biometric-recognition/> · *doc* — UK guidance on when biometric data is special-category.
100. **California CCPA (Attorney General)** — <https://oag.ca.gov/privacy/ccpa> · *doc* — Sensitive personal information rights, including biometrics.
101. **FTC — COPPA Rule** — <https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa> · *doc* — Why the 13+ age gate (SECURITY_CHECKLIST §5.6) stays a v1 requirement.
102. **Apple App Review Guidelines** — <https://developer.apple.com/app-store/review/guidelines/> · *doc* — §5.1 privacy and face-data rules that any V2 capture must clear.
103. **Apple — App privacy details** — <https://developer.apple.com/app-store/app-privacy-details/> · *doc* — Privacy label declarations; v1 declares no biometric collection.
104. **Apple ARKit — Tracking and visualizing faces** — <https://developer.apple.com/documentation/arkit/tracking-and-visualizing-faces> · *doc* — The face-data API whose use Apple restricts; only relevant if V2 capture uses TrueDepth.
