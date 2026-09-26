# gj-scenegraph — Resources

The annotated research list for the scene-graph hat. Research focus is from kit §3.2: indoor scene understanding, affordance detection, 3D Gaussian segmentation (Gaussian Grouping lineage), reachability and route search, VR-GS / DecoupledGaussian and recent scene-level physics papers, and climbing and parkour system design. Mesh cleanup and the Tier 1 displacement pipeline are added. Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26: HTTP 200 plus a page-title match, and arXiv titles were checked against the abstract page. Research code is a reference, not a dependency: check every repo's licence before reuse. INRIA-derived code is excluded (ADR-0005), and copyleft tools (CGAL, TetGen) need a licence decision (SECURITY_CHECKLIST §7.3). Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first: `SPEC.md` §3.3–§3.4, §3.6, §5; Movement Bible §1, §3–§6, §10, §14; `design/proposals/journey-route-generation-v1.md`; `services/traversal/movement.py`; `config/movement.json`.

## A. Indoor scene understanding and semantic labeling

1. **ScanNet: Richly-annotated 3D Reconstructions of Indoor Scenes** — <https://arxiv.org/abs/1702.04405> · *paper* — The standard indoor benchmark; its class taxonomy informs material/semantic labels (M1-SCEN-02).
2. **ScanNet++: A High-Fidelity Dataset of 3D Indoor Scenes** — <https://arxiv.org/abs/2308.11417> · *paper* — High-fidelity indoor scans with semantics; closest public data to GJ room captures.
3. **Matterport3D: Learning from RGB-D Data in Indoor Environments** — <https://arxiv.org/abs/1709.06158> · *paper* — Room-scale indoor dataset with region and object labels.
4. **Replica dataset (Meta)** — <https://github.com/facebookresearch/Replica-Dataset> · *repo* — Photoreal indoor reconstructions with semantic meshes for offline classifier tests.
5. **ARKitScenes: A Diverse Real-World Dataset for 3D Indoor Scene Understanding Using Mobile RGB-D Data** — <https://arxiv.org/abs/2111.08897> · *paper* — iPhone/iPad LiDAR captures, the same sensor path GJ uses.
6. **Segment Anything** — <https://arxiv.org/abs/2304.02643> · *paper* — Promptable 2D masks; the usual front end for lifting segments onto splats.
7. **SAM 2: Segment Anything in Images and Videos** — <https://arxiv.org/abs/2408.00714> · *paper* — Video-consistent masks across capture frames, useful for multi-view label fusion.
8. **Segment Anything repository** — <https://github.com/facebookresearch/segment-anything> · *repo* — Apache-2.0 reference implementation (licence check per SECURITY_CHECKLIST §7.3).
9. **Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection** — <https://arxiv.org/abs/2303.05499> · *paper* — Open-vocabulary detection for labels like "cushion", "curtain", "lamp".
10. **DINOv2: Learning Robust Visual Features without Supervision** — <https://arxiv.org/abs/2304.07193> · *paper* — Strong generic features for material and surface classification.
11. **Learning Transferable Visual Models From Natural Language Supervision (CLIP)** — <https://arxiv.org/abs/2103.00020> · *paper* — Zero-shot labels for the semantic/material vision pass.
12. **OpenScene: 3D Scene Understanding with Open Vocabularies** — <https://arxiv.org/abs/2211.15654> · *paper* — Open-vocabulary 3D labels without per-class training.
13. **ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning** — <https://arxiv.org/abs/2309.16650> · *paper* — Object-level 3D scene graphs; a template for scene_graph.json structure.
14. **3D Scene Graph: A Structure for Unified Semantics, 3D Space, and Camera** — <https://arxiv.org/abs/1910.02527> · *paper* — The layered scene-graph idea (building → room → object) behind the GJ schema.
15. **Hydra: A Real-time Spatial Perception System for 3D Scene Graph Construction** — <https://arxiv.org/abs/2201.13360> · *paper* — Real-time scene-graph construction with places and traversability layers.
16. **Materials in Context (MINC) database** — <https://arxiv.org/abs/1412.0623> · *paper* — Material recognition in the wild; maps to the Bible §9 material list.
17. **OpenSurfaces: A Richly Annotated Catalog of Surface Appearance** — <http://opensurfaces.cs.cornell.edu/> · *doc* — Material-annotated indoor surfaces for training or checking material labels.
18. **Mask3D: Mask Transformer for 3D Semantic Instance Segmentation** — <https://arxiv.org/abs/2210.03105> · *paper* — Instance segmentation on point clouds for object-level labels.
19. **Point Transformer V3** — <https://arxiv.org/abs/2312.10035> · *paper* — State-of-the-art point-cloud backbone for surface classification.
20. **Connecting the Dots: Floorplan Reconstruction Using Two-Level Queries (RoomFormer)** — <https://arxiv.org/abs/2211.15658> · *paper* — Room-layout extraction; helps ceiling cap and wall detection.
21. **OpenMask3D: Open-Vocabulary 3D Instance Segmentation** — <https://arxiv.org/abs/2306.13631> · *paper* — Open-vocabulary object instances on indoor scans without per-class training.
22. **SAM3D: Segment Anything in 3D Scenes** — <https://arxiv.org/abs/2306.03908> · *paper* — Lifts SAM masks to 3D point clouds; a training-free labeling baseline.
23. **In-Place Scene Labelling and Understanding with Implicit Scene Representation (Semantic-NeRF)** — <https://arxiv.org/abs/2103.15875> · *paper* — Multi-view label fusion that denoises per-frame labels, useful for noisy vision-pass output.
24. **Panoptic Lifting for 3D Scene Understanding with Neural Fields** — <https://arxiv.org/abs/2212.09802> · *paper* — Consistent 3D panoptic labels from 2D predictions.
25. **LERF: Language Embedded Radiance Fields** — <https://arxiv.org/abs/2303.09553> · *paper* — Language queries over a reconstruction, ancestor of LangSplat.

## B. 3D Gaussian segmentation (Gaussian Grouping lineage)

26. **Gaussian Grouping: Segment and Edit Anything in 3D Scenes** — <https://arxiv.org/abs/2312.00732> · *paper* — The lineage root named in the kit: identity-encoded Gaussians for object segmentation.
27. **Gaussian Grouping repository** — <https://github.com/lkeab/gaussian-grouping> · *repo* — Reference code; check licence before any reuse (INRIA-derived code is excluded).
28. **Segment Any 3D Gaussians (SAGA)** — <https://arxiv.org/abs/2312.00860> · *paper* — Fast promptable segmentation of splats via learned affinity features.
29. **LangSplat: 3D Language Gaussian Splatting** — <https://arxiv.org/abs/2312.16084> · *paper* — Language-queryable splats ("find the curtain") for semantic labels.
30. **Feature 3DGS: Supercharging 3D Gaussian Splatting to Enable Distilled Feature Fields** — <https://arxiv.org/abs/2312.03203> · *paper* — Distils 2D foundation features into splats for labeling.
31. **GaussianEditor: Swift and Controllable 3D Editing with Gaussian Splatting** — <https://arxiv.org/abs/2311.14521> · *paper* — Semantic tracing of Gaussians; relevant to object isolation for Tier 1.
32. **OmniSeg3D: Omniversal 3D Segmentation via Hierarchical Contrastive Learning** — <https://arxiv.org/abs/2311.11666> · *paper* — Hierarchical segmentation (object vs part) for cushion vs couch.
33. **Click-Gaussian: Interactive Segmentation to Any 3D Gaussians** — <https://arxiv.org/abs/2407.11793> · *paper* — Fast interactive segmentation; useful for building labeled fixtures.
34. **FlashSplat: 2D to 3D Gaussian Splatting Segmentation Solved Optimally** — <https://arxiv.org/abs/2409.08270> · *paper* — Training-free, optimal lifting of 2D masks to splats; cheap per-scan cost.
35. **awesome-3D-gaussian-splatting (segmentation and physics sections)** — <https://github.com/MrNeRF/awesome-3D-gaussian-splatting> · *repo* — Curated list; track new segmentation and physics papers.
36. **GARField: Group Anything with Radiance Fields** — <https://arxiv.org/abs/2401.09419> · *paper* — Scale-aware grouping (cushion vs couch vs room) that maps to object hierarchy in the scene graph.
37. **Gaga: Group Any Gaussians via 3D-aware Memory Bank** — <https://arxiv.org/abs/2404.07977> · *paper* — Consistent Gaussian grouping from inconsistent 2D masks.
38. **Contrastive Gaussian Clustering: Weakly Supervised 3D Scene Segmentation** — <https://arxiv.org/abs/2404.12784> · *paper* — Segmentation from weak labels, relevant to cheap per-scan labeling.

## C. Mesh cleanup and geometry processing

39. **Open3D documentation** — <https://www.open3d.org/docs/release/> · *doc* — Mesh I/O, cleanup and cluster filtering used downstream of reconstruction.
40. **Open3D — Mesh (cleanup, clustering) tutorial** — <https://www.open3d.org/docs/release/tutorial/geometry/mesh.html> · *doc* — cluster_connected_triangles and degenerate removal for floater removal (M1-SCEN-01).
41. **Open3D — RANSAC plane segmentation (point cloud)** — <https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html> · *doc* — Plane detection for floors, tabletops, walls and the ceiling cap.
42. **PyMeshLab** — <https://github.com/cnr-isti-vclab/PyMeshLab> · *repo* — Hole closing, decimation and repair filters.
43. **MeshLab filters documentation** — <https://www.meshlab.net/> · *doc* — Reference for close-holes and remeshing filter parameters.
44. **trimesh** — <https://github.com/mikedh/trimesh> · *repo* — Watertightness checks, ray casts and measurements in Python tests.
45. **libigl tutorial** — <https://libigl.github.io/tutorial/> · *doc* — Geometry-processing primitives (curvature, winding numbers) for classification features.
46. **Robust Inside-Outside Segmentation using Generalized Winding Numbers** — <https://igl.ethz.ch/projects/winding-number/> · *paper* — Robust inside/outside for filling and capping imperfect scan meshes.
47. **Manifold (robust mesh boolean)** — <https://github.com/elalish/manifold> · *repo* — Guaranteed-manifold booleans for capping and patching.
48. **CGAL — Polygon Mesh Processing** — <https://doc.cgal.org/latest/Polygon_mesh_processing/index.html> · *doc* — Hole filling and repair algorithms (check GPL/commercial licensing before use).
49. **Principal curvature and normal estimation (PCL docs)** — <https://pointclouds.org/documentation/tutorials/normal_estimation.html> · *doc* — Normals and curvature features for surface classes like textured-vertical.
50. **DBSCAN (scikit-learn)** — <https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html> · *doc* — Density clustering to find and drop floaters before meshing.
51. **JSON Schema 2020-12** — <https://json-schema.org/draft/2020-12> · *doc* — The dialect M1-DATA-01 requires for scene_graph, traversal_graph and environment_spec.
52. **jsonschema (Python)** — <https://python-jsonschema.readthedocs.io/en/stable/> · *doc* — Validates fixtures against the frozen schemas in tests (M1-DATA-01 AT-2).

## D. Affordances and traversability

53. **Affordance (Gibson) — The Ecological Approach to Visual Perception (summary)** — <https://en.wikipedia.org/wiki/Affordance> · *doc* — The concept behind the affordance library: surfaces define possible actions.
54. **Where2Act: From Pixels to Actions for Articulated 3D Objects** — <https://arxiv.org/abs/2101.02692> · *paper* — Learned per-point affordances; inspiration for per-surface verb scores.
55. **3D AffordanceNet: A Benchmark for Visual Object Affordance Understanding** — <https://arxiv.org/abs/2103.16397> · *paper* — Benchmark for affordance labels on 3D shapes.
56. **Recast Navigation** — <https://github.com/recastnavigation/recastnavigation> · *repo* — Industry navmesh generation (voxelize, walkable slope/step/height); a model for walkable-surface extraction.
57. **Unity AI Navigation package** — <https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/index.html> · *doc* — NavMesh baking with agent height/step/slope; comparison for the traversal graph.
58. **Unity AI Navigation — Off-mesh links** — <https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshLink.html> · *doc* — How engines represent jump/climb edges between walkable regions, like traversal-graph edges.

## E. Reachability, route search and procedural level design

59. **Red Blob Games — Introduction to A*** — <https://www.redblobgames.com/pathfinding/a-star/introduction.html> · *doc* — Clear reference for A*/Dijkstra used in the reachability search.
60. **Red Blob Games — Pathfinding for tower defense (flow fields)** — <https://www.redblobgames.com/pathfinding/tower-defense/> · *doc* — Breadth-first flood fill from spawn, the basis for the reachable set in summit designation.
61. **Amit's A* pages (Stanford)** — <http://theory.stanford.edu/~amitp/GameProgramming/> · *doc* — Heuristics and tie-breaking; deterministic tie-breaking keeps validator output stable (REVIEW_RUBRIC A6).
62. **Yen's k-shortest paths (NetworkX shortest_simple_paths)** — <https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.simple_paths.shortest_simple_paths.html> · *doc* — Enumerating distinct candidate routes before difficulty shaping.
63. **NetworkX documentation** — <https://networkx.org/documentation/stable/> · *doc* — Graph library for prototyping the traversal graph and route search in Python.
64. **Hypothesis (property-based testing)** — <https://hypothesis.readthedocs.io/> · *doc* — Property tests required by M1-SCEN-05 AT-2 (gap just over/under the 85 % margin).
65. **Procedural Content Generation in Games (Shaker, Togelius, Nelson)** — <https://www.pcgbook.com/> · *doc* — Free textbook; constructive vs search-based generation and playability checks.
66. **Rational Level Design (Dan Taylor) — Ten Principles of Good Level Design** — <https://www.gamedeveloper.com/design/ten-principles-of-good-level-design-part-1-> · *doc* — Wayfinding and difficulty pacing principles for route shaping.
67. **Viewshed analysis (GRASS r.viewshed)** — <https://grass.osgeo.org/grass-stable/manuals/r.viewshed.html> · *doc* — Visibility computation for vista scoring (how much of the place and summit is visible).
68. **A* search algorithm (Wikipedia)** — <https://en.wikipedia.org/wiki/A*_search_algorithm> · *doc* — Admissibility and consistency conditions the deterministic validator relies on; cites Hart, Nilsson and Raphael (1968).
69. **Kishōtenketsu (Wikipedia)** — <https://en.wikipedia.org/wiki/Kish%C5%8Dtenketsu> · *doc* — The four-act structure behind the introduce → develop → twist → resolve beats (Design Skills rule 22).
70. **The Level Design Book** — <https://book.leveldesignbook.com/> · *doc* — Open reference on layout, flow and pacing for shaping routes.
71. **The Level Design Book — Metrics** — <https://book.leveldesignbook.com/process/blockout/metrics> · *doc* — Designing to player metrics (jump height, reach), the same idea as movement.json-driven validation.
72. **The Level Design Book — Layout** — <https://book.leveldesignbook.com/process/layout> · *doc* — Loops, landmarks and sightlines; informs vista spread and summit visibility.
73. **Viewshed analysis (Wikipedia)** — <https://en.wikipedia.org/wiki/Viewshed_analysis> · *doc* — Background on visibility analysis for vista scoring.

## F. Physics on segmented objects (Tier 2 research)

74. **VR-GS: A Physical Dynamics-Aware Interactive Gaussian Splatting System in Virtual Reality** — <https://arxiv.org/abs/2401.16663> · *paper* — Named in the kit: segmentation + tet embedding + XPBD for interactive splats.
75. **DecoupledGaussian: Object-Scene Decoupling for Physics-Based Interaction** — <https://arxiv.org/abs/2503.05484> · *paper* — Named in the kit: separate objects from the scene and inpaint the hole (SPEC §5 R5).
76. **PhysGaussian: Physics-Integrated 3D Gaussians for Generative Dynamics** — <https://arxiv.org/abs/2311.12198> · *paper* — MPM on Gaussians; the physics-on-splats baseline.
77. **PhysDreamer: Physics-Based Interaction with 3D Objects via Video Generation** — <https://arxiv.org/abs/2404.13026> · *paper* — Learns material parameters for soft objects like plants and cloth.
78. **Reconstruction and Simulation of Elastic Objects with Spring-Mass 3D Gaussians (Spring-Gaus)** — <https://arxiv.org/abs/2403.09434> · *paper* — Spring-mass Gaussians, a cheaper sim model for cushions.
79. **Gaussian Splashing: Unified Particles for Versatile Motion Synthesis and Rendering** — <https://arxiv.org/abs/2401.15318> · *paper* — Particle-based dynamics on splats including fluids and solids.
80. **XPBD: Position-Based Simulation of Compliant Constrained Dynamics** — <https://matthias-research.github.io/pages/publications/XPBD.pdf> · *paper* — The solver named in SPEC §5; stable and fast enough to consider for mobile.
81. **Ten Minute Physics (Matthias Müller)** — <https://matthias-research.github.io/pages/tenMinutePhysics/index.html> · *doc* — Practical PBD/XPBD tutorials with code for cloth and soft bodies.
82. **Detailed Rigid Body Simulation with Extended Position Based Dynamics** — <https://matthias-research.github.io/pages/publications/PBDBodies.pdf> · *paper* — XPBD rigid bodies for small loose objects (SPEC §5 class 3).
83. **TetGen** — <https://wias-berlin.de/software/tetgen/> · *doc* — Tetrahedral meshing for tet-embedded Gaussians (check AGPL/commercial licence).
84. **fTetWild: Fast Tetrahedral Meshing in the Wild** — <https://github.com/wildmeshing/fTetWild> · *repo* — Robust tet meshing of messy scan geometry (MPL-2.0).
85. **InFusion: Inpainting 3D Gaussians via Learning Depth Completion from Diffusion Prior** — <https://arxiv.org/abs/2404.11613> · *paper* — Filling holes left by moved objects (SPEC §5 R5).
86. **Unity Burst compiler manual** — <https://docs.unity3d.com/Packages/com.unity.burst@1.8/manual/index.html> · *doc* — How a mobile XPBD prototype would hit the R3 ≤ 6 ms/frame budget.
87. **Feature Splatting: Language-Driven Physics-Based Scene Synthesis and Editing** — <https://arxiv.org/abs/2404.01223> · *paper* — Language-selected objects simulated in splats; a segmentation-to-physics bridge.
88. **GIC: Gaussian-Informed Continuum for Physical Property Identification and Simulation** — <https://arxiv.org/abs/2406.14927> · *paper* — Estimates physical properties from video, relevant to per-class sim parameters.
89. **OmniPhysGS: 3D Constitutive Gaussians for General Physics-Based Dynamics Generation** — <https://arxiv.org/abs/2501.18982> · *paper* — Multi-material constitutive models on Gaussians (2025 state of the art).
90. **PhysTwin: Physics-Informed Reconstruction and Simulation of Deformable Objects from Videos** — <https://arxiv.org/abs/2503.17973> · *paper* — Spring-mass digital twins of deformables at interactive rates.
91. **Physically Embodied Gaussian Splatting: A Realtime Correctable World Model for Robotics** — <https://arxiv.org/abs/2406.10788> · *paper* — Real-time particle physics coupled to Gaussians; a runtime-cost reference for R3.
92. **Physical Property Understanding from Language-Embedded Feature Fields (NeRF2Physics)** — <https://arxiv.org/abs/2404.04242> · *paper* — Infers mass/stiffness per object from vision-language features.

## G. Tier 1 reactivity (shader displacement, no physics)

93. **Unity URP — Writing custom shaders** — <https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/writing-custom-shaders-urp.html> · *doc* — Vertex/splat displacement for dent, sway and flutter (M3-GAME-01).
94. **Unity Shader Graph manual** — <https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/index.html> · *doc* — Authoring displacement parameters per material class.
95. **GPU Gems 3 — GPU-Generated Procedural Wind Animations for Trees** — <https://developer.nvidia.com/gpugems/gpugems3/part-i-geometry/chapter-6-gpu-generated-procedural-wind-animations-trees> · *doc* — Classic procedural sway; the model for plants and curtains.
96. **GPU Gems — Effective Water Simulation from Physical Models** — <https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-1-effective-water-simulation-physical-models> · *doc* — Sum-of-sines deformation techniques for cheap periodic motion.

## H. Climbing and parkour system design

97. **The Legend of Zelda: Breath of the Wild — Change and Constant (GDC Vault)** — <https://gdcvault.com/play/1024562/Change-and-Constant-Breaking-Conventions> · *talk* — "Climb anything" design and its consequences for level readability.
98. **Robot Parkour Learning** — <https://arxiv.org/abs/2309.05665> · *paper* — Learned parkour skills (climb, leap, crawl) with obstacle-parameterized difficulty; a reference for grading verbs by geometry.
99. **Extreme Parkour with Legged Robots** — <https://arxiv.org/abs/2309.14341> · *paper* — Direction and gap-aware parkour; shows how reach limits define feasible transitions.
100. **ANYmal Parkour: Learning Agile Navigation for Quadrupedal Robots** — <https://arxiv.org/abs/2306.14874> · *paper* — Combines a skill library with a navigation planner, the same split as affordance library + route search.
101. **GDC Vault — Animation Bootcamp: Animating The 3rd Assassin (Jonathan Cooper)** — <https://www.gdcvault.com/play/1031894/Animation-Bootcamp-Animating-The-3rd> · *talk* — Assassin's Creed III climbing and tree-running: surface types (unclimbable, anchors, V-trees) map directly to surface classes.
102. **Wolfire — GDC13 Animation Bootcamp summary (Assassin's Creed)** — <https://www.wolfire.com/blog/2013/04/GDC13-Summary-Animation-Bootcamp-Part-4-6/> · *doc* — Written summary of the AC3 talk, including IK hand/foot placement on climb holds.
103. **UpRoom Games — Procedural climbing devlog** — <https://www.uproomgames.com/dev-log/procedural-climbing> · *postmortem* — An indie procedural climbing system built on IK and springs; close to the Bible §6.3–6.5 procedural climbs.
