# gj-capture — Resources

The annotated research list for the capture hat. Research focus is from kit §3.1: Gaussian splatting on mobile, ARKit capture best practice, consumer scan-app UX, photogrammetry capture guidance, splat compression and LOD, and Unity splat renderers. It also covers the self-host pipeline tools locked in ADR-0005 (AUTH #030, #032). Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26: HTTP 200 plus a page-title match, and arXiv titles were checked against the abstract page. Vendors listed here are references only. Adopting any of them (a GPU host, storage, a bridge) is an AUTH (`agents/grok/README.md` §6). The code licence of every pipeline component must be MIT/BSD/Apache-2.0 (SECURITY_CHECKLIST §7.3). Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first: `SPEC.md` §3.1, §3.9; `ADRs/0005-*`; `services/reconstruction/README.md`; `research/vendors/reconstruction-cost-and-trainer-analysis.md`; `research/vendors/reconstruction-spike-report.md`; `design/proposals/capture-ux-coaching-v1.md`; `design/proposals/ios-splat-render-v1.md`; `design/DESIGN_SYSTEM.md` decision 6.

## A. Gaussian splatting foundations and training

1. **3D Gaussian Splatting for Real-Time Radiance Field Rendering** — <https://arxiv.org/abs/2308.04079> · *paper* — The original 3DGS paper; defines the representation every GJ environment package carries.
2. **3DGS project page (INRIA)** — <https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/> · *doc* — Reference results and datasets; note the INRIA code licence is non-commercial and is excluded from GJ.
3. **gsplat: An Open-Source Library for Gaussian Splatting** — <https://arxiv.org/abs/2409.06765> · *paper* — The Apache-2.0 trainer GJ chose first (ADR-0005 addendum 4, AUTH #032).
4. **gsplat repository** — <https://github.com/nerfstudio-project/gsplat> · *repo* — Source for the pinned gsplat 1.4.0 build in services/reconstruction/Dockerfile.
5. **gsplat documentation** — <https://docs.gsplat.studio/> · *doc* — Strategy (default vs MCMC), densification and rasterization options for tuning training.
6. **Nerfstudio: A Modular Framework for Neural Radiance Field Development** — <https://arxiv.org/abs/2302.04264> · *paper* — Framework behind Splatfacto, the trainer entry point used in the spike.
7. **Nerfstudio repository** — <https://github.com/nerfstudio-project/nerfstudio> · *repo* — Pinned nerfstudio 1.1.5 in the reconstruction image; issues track Splatfacto regressions.
8. **Nerfstudio documentation — Splatfacto** — <https://docs.nerf.studio/nerfology/methods/splat.html> · *doc* — Splatfacto configuration and export used by the reconstruction service.
9. **3D Gaussian Splatting as Markov Chain Monte Carlo** — <https://arxiv.org/abs/2404.09591> · *paper* — The MCMC strategy that caps splat count to a fixed budget (the ~1–2.5M room target).
10. **Taming 3DGS: High-Quality Radiance Fields with Limited Resources** — <https://arxiv.org/abs/2406.15643> · *paper* — Budget-controlled densification; another way to hit a fixed splat count.
11. **Scaffold-GS: Structured 3D Gaussians for View-Adaptive Rendering** — <https://arxiv.org/abs/2312.00109> · *paper* — Anchor-based structure that cuts redundant splats in indoor scenes.
12. **Brush (Gaussian splatting in Rust/WebGPU)** — <https://github.com/ArthurBrussee/brush> · *repo* — The second, pluggable trainer named in ADR-0005; runs without CUDA.
13. **Mip-Splatting: Alias-free 3D Gaussian Splatting** — <https://arxiv.org/abs/2311.16493> · *paper* — Anti-aliasing across zoom levels; relevant because players view rooms at 1:12 from very close.
14. **2D Gaussian Splatting for Geometrically Accurate Radiance Fields** — <https://arxiv.org/abs/2403.17888> · *paper* — Surface-aligned splats give better geometry, a route to cleaner collision meshes.
15. **SuGaR: Surface-Aligned Gaussian Splatting for Mesh Reconstruction** — <https://arxiv.org/abs/2311.12775> · *paper* — Mesh extraction from splats; studied but excluded for licence reasons (spike report §2).
16. **Gaussian Opacity Fields** — <https://arxiv.org/abs/2404.10772> · *paper* — High-quality mesh extraction from Gaussians; candidate for collision-mesh quality work.
17. **PGSR: Planar-based Gaussian Splatting for Surface Reconstruction** — <https://arxiv.org/abs/2406.06521> · *paper* — Planar priors suit indoor rooms (walls, tabletops) for geometry quality.
18. **Mip-NeRF 360: Unbounded Anti-Aliased Neural Radiance Fields** — <https://arxiv.org/abs/2111.12077> · *paper* — Source of the public `room` scene used for the self-host spike baseline.
19. **Mip-NeRF 360 dataset page** — <https://jonbarron.info/mipnerf360/> · *doc* — Download and licence notes for the public benchmark data in data/mipnerf360/.
20. **A Survey on 3D Gaussian Splatting** — <https://arxiv.org/abs/2401.03890> · *paper* — Map of the field for picking follow-up techniques.
21. **awesome-3D-gaussian-splatting** — <https://github.com/MrNeRF/awesome-3D-gaussian-splatting> · *repo* — Curated, frequently updated paper list; the fastest way to find 2026 work.

## B. Structure-from-motion and poses

22. **COLMAP documentation** — <https://colmap.github.io/> · *doc* — SfM/MVS front end (COLMAP 4.1.1 CUDA in the reconstruction image).
23. **COLMAP repository** — <https://github.com/colmap/colmap> · *repo* — Release notes for the pinned version and the built-in `global_mapper`.
24. **Structure-from-Motion Revisited (Schönberger and Frahm, CVPR 2016)** — <https://openaccess.thecvf.com/content_cvpr_2016/html/Schonberger_Structure-From-Motion_Revisited_CVPR_2016_paper.html> · *paper* — The incremental SfM design behind the spike's winning configuration (A: GPU COLMAP incremental).
25. **Global Structure-from-Motion Revisited (GLOMAP)** — <https://arxiv.org/abs/2407.20219> · *paper* — Global SfM; measured slower and pricier than incremental on the spike room (B), kept selectable.
26. **GLOMAP repository (deprecated)** — <https://github.com/colmap/glomap> · *repo* — Standalone repo now marked deprecated. GLOMAP lives on inside COLMAP as `colmap global_mapper`, which the image uses.
27. **hloc — Hierarchical Localization toolbox** — <https://github.com/cvg/Hierarchical-Localization> · *repo* — Learned features/matching for hard indoor scenes where SIFT fails on low texture.
28. **LightGlue: Local Feature Matching at Light Speed** — <https://arxiv.org/abs/2306.13643> · *paper* — Fast learned matching; an option if texture-poor walls break registration.
29. **DUSt3R: Geometric 3D Vision Made Easy** — <https://arxiv.org/abs/2312.14132> · *paper* — Pose-free reconstruction; fallback idea when ARKit poses are weak.
30. **Grounding Image Matching in 3D with MASt3R** — <https://arxiv.org/abs/2406.09756> · *paper* — Dense matching with metric scale; relevant to low-texture capture.
31. **InstantSplat: Sparse-view Gaussian Splatting in Seconds** — <https://arxiv.org/abs/2403.20309> · *paper* — Pose-free splatting from few views; a research option for short captures.
32. **Deblurring 3D Gaussian Splatting** — <https://arxiv.org/abs/2401.00834> · *paper* — Robustness to motion blur, the most common handheld capture defect.
33. **BAD-Gaussians: Bundle Adjusted Deblur Gaussian Splatting** — <https://arxiv.org/abs/2403.11831> · *paper* — Jointly fixes blur and poses; relevant when the blur-ratio gate lets marginal frames through.

## C. ARKit capture, poses and depth

34. **ARKit documentation** — <https://developer.apple.com/documentation/arkit> · *doc* — Session, tracking state and frame APIs behind the capture bundle (SPEC §3.1).
35. **ARKit — ARFrame** — <https://developer.apple.com/documentation/arkit/arframe> · *doc* — Per-frame camera transform, intrinsics and timestamps written into the upload contract.
36. **ARKit — ARCamera.TrackingState** — <https://developer.apple.com/documentation/arkit/arcamera/trackingstate> · *doc* — Tracking-continuity signal for the readiness score and relocalize flow.
37. **ARKit — ARDepthData (scene depth)** — <https://developer.apple.com/documentation/arkit/ardepthdata> · *doc* — Optional LiDAR depth in the bundle when the device has it.
38. **ARKit — ARMeshAnchor** — <https://developer.apple.com/documentation/arkit/armeshanchor> · *doc* — On-device LiDAR mesh; a possible coverage-map source for the readiness score.
39. **Apple sample — Displaying a point cloud using scene depth** — <https://developer.apple.com/documentation/arkit/displaying-a-point-cloud-using-scene-depth> · *doc* — Working sample for accumulating depth into a live coverage visual.
40. **WWDC20 — Explore ARKit 4** — <https://developer.apple.com/videos/play/wwdc2020/10611/> · *talk* — Introduces the scene-depth API and its confidence maps.
41. **ARKit — ARWorldTrackingConfiguration** — <https://developer.apple.com/documentation/arkit/arworldtrackingconfiguration> · *doc* — World alignment (gravity) for the up vector used in summit designation.
42. **ARKit — ARLightEstimate** — <https://developer.apple.com/documentation/arkit/arlightestimate> · *doc* — Ambient intensity as a cheap light signal for the "Too dark here" card.
43. **Apple sample — Capturing depth using the LiDAR camera** — <https://developer.apple.com/documentation/avfoundation/capturing-depth-using-the-lidar-camera> · *doc* — Depth capture patterns and formats.
44. **Apple — Object Capture (RealityKit) overview** — <https://developer.apple.com/documentation/realitykit/realitykit-object-capture> · *doc* — Apple's own capture guidance for orbital object scans, close to the tabletop mode.
45. **Apple — Capturing photographs for RealityKit Object Capture** — <https://developer.apple.com/documentation/realitykit/capturing-photographs-for-realitykit-object-capture> · *doc* — Overlap, lighting and angle guidance usable in the tabletop coaching script.
46. **WWDC23 — Meet Object Capture for iOS** — <https://developer.apple.com/videos/play/wwdc2023/10191/> · *talk* — Guided capture UI patterns (coverage feedback, reorientation) from Apple.
47. **Unity AR Foundation manual** — <https://docs.unity3d.com/Packages/com.unity.xr.arfoundation@6.0/manual/index.html> · *doc* — How the Unity app reaches ARKit poses, depth and camera frames.
48. **Unity ARKit XR Plugin manual** — <https://docs.unity3d.com/Packages/com.unity.xr.arkit@6.0/manual/index.html> · *doc* — iOS-specific ARKit features and build settings for the capture scene.
49. **AR Foundation samples** — <https://github.com/Unity-Technologies/arfoundation-samples> · *repo* — Working Unity samples for camera frames, depth and meshing.
50. **ARCore documentation** — <https://developers.google.com/ar> · *doc* — Android parity reference only (Android is not a v1 target, SPEC §11).

## D. Capture UX and photogrammetry guidance

51. **Polycam — capture tips** — <https://learn.poly.cam/> · *vendor guide* — Consumer capture coaching patterns (orbit heights, overlap) to benchmark GJ's scripts against.
52. **Scaniverse (Niantic Spatial)** — <https://scaniverse.com/> · *vendor guide* — Origin of the SPZ format and a reference for iPhone splat capture with on-device preview.
53. **Niantic SPZ format repository** — <https://github.com/nianticlabs/spz> · *repo* — The compressed splat format (.spz, MIT) the pipeline emits and aras-p reads.
54. **KIRI Engine** — <https://www.kiriengine.app/> · *vendor guide* — The conditional corpus-only bridge named in ADR-0005; usable only under written no-train + DPA + residency terms.
55. **RealityScan (Epic)** — <https://www.realityscan.com/> · *vendor guide* — Mobile photogrammetry coaching with live coverage feedback, a close analogue to decision 6.
56. **Agisoft Metashape user manual** — <https://www.agisoft.com/downloads/user-manuals/> · *doc* — Professional photogrammetry capture rules (overlap, avoid reflective surfaces).
57. **RealityCapture — capturing guidelines** — <https://dev.epicgames.com/documentation/en-us/realityscan/> · *doc* — Overlap and lighting rules that translate into the readiness signals.
58. **Laplacian variance blur detection (PyImageSearch)** — <https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv/> · *doc* — Simple, cheap blur metric for the blur-ratio signal.
59. **OpenCV documentation** — <https://docs.opencv.org/4.x/> · *doc* — Image metrics (blur, exposure) for prototyping readiness signals server-side.
60. **Apple Human Interface Guidelines — Augmented reality** — <https://developer.apple.com/design/human-interface-guidelines/augmented-reality> · *doc* — Coaching and onboarding rules for AR sessions; pairs with Design Skills §3.5.
61. **ARKit — ARCoachingOverlayView** — <https://developer.apple.com/documentation/arkit/arcoachingoverlayview> · *doc* — Apple's built-in relocalization coaching; reference for the tracking-loss path.

## E. Splat compression, LOD and streaming

62. **PlayCanvas splat-transform** — <https://github.com/playcanvas/splat-transform> · *repo* — The MIT CLI (v3.6.4 pinned) that writes .spz/.sog in the pipeline.
63. **PlayCanvas — SOGS compression blog** — <https://blog.playcanvas.com/playcanvas-adopts-sogs-for-20x-3dgs-compression/> · *doc* — Source of the ~20x SOG compression figure in the cost analysis.
64. **Compact 3D Scene Representation via Self-Organizing Gaussian Grids (SOGS)** — <https://arxiv.org/abs/2312.13299> · *paper* — The sorted-grid compression behind SOG.
65. **Compact 3D Gaussian Representation for Radiance Field** — <https://arxiv.org/abs/2311.13681> · *paper* — Learned masking and codebooks to cut splat count and size.
66. **LightGaussian: Unbounded 3D Gaussian Compression with 15x Reduction** — <https://arxiv.org/abs/2311.17245> · *paper* — Pruning and distillation to hit the ≤150 MB package target.
67. **EAGLES: Efficient Accelerated 3D Gaussians with Lightweight EncodingS** — <https://arxiv.org/abs/2312.04564> · *paper* — Quantized attributes for smaller, faster splats on mobile.
68. **HAC: Hash-grid Assisted Context for 3D Gaussian Splatting Compression** — <https://arxiv.org/abs/2403.14530> · *paper* — State-of-the-art compression ratios to watch.
69. **Octree-GS: Towards Consistent Real-time Rendering with LOD-Structured 3D Gaussians** — <https://arxiv.org/abs/2403.17898> · *paper* — LOD structure; aras-p has no LOD, so GJ must author one (M1-UNITY-01 AT-4).
70. **A Hierarchical 3D Gaussian Representation for Real-Time Rendering of Very Large Datasets** — <https://arxiv.org/abs/2406.12080> · *paper* — Hierarchical LOD and chunking for larger scenes.
71. **FlashGS: Efficient 3D Gaussian Splatting for Large-scale and High-resolution Rendering** — <https://arxiv.org/abs/2408.07967> · *paper* — Rasterizer efficiency ideas relevant to mobile frame budgets.
72. **3DGS.zip: A survey on 3D Gaussian Splatting Compression Methods** — <https://arxiv.org/abs/2407.09510> · *paper* — Comparative benchmark for choosing a compression path.
73. **Khronos — KHR_gaussian_splatting glTF discussion** — <https://github.com/KhronosGroup/glTF/pull/2490> · *doc* — Emerging standard for splats in glTF; keeps the package format vendor-neutral.

## F. Rendering splats in Unity and on iOS

74. **aras-p/UnityGaussianSplatting** — <https://github.com/aras-p/UnityGaussianSplatting> · *repo* — The MIT Unity renderer (URP render graph) at the centre of M0-UNITY-02 and M1-UNITY-01.
75. **UnityGaussianSplatting issue #226 (Metal sort)** — <https://github.com/aras-p/UnityGaussianSplatting/issues/226> · *doc* — The Metal radix-sort glitch that makes iOS rendering the #1 program risk.
76. **scier/MetalSplatter** — <https://github.com/scier/MetalSplatter> · *repo* — MIT native Metal splat renderer on iPhone; Option B for M1-UNITY-01.
77. **rayanht/msplat** — <https://github.com/rayanht/msplat> · *repo* — Tile-local bitonic sort (Apache-2.0); Option A technique for fixing the Metal sort.
78. **Unity Manual — Native plug-ins for iOS** — <https://docs.unity3d.com/Manual/PluginsForIOS.html> · *doc* — How a MetalSplatter wrapper would be packaged as a Unity plugin.
79. **Unity Manual — Low-level native plug-in rendering extensions** — <https://docs.unity3d.com/Manual/NativePluginInterface.html> · *doc* — Render-event callbacks and texture handoff for a native Metal plugin.
80. **Unity URP — Render Graph system** — <https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/render-graph.html> · *doc* — The URP path GaussianSplatURPFeature uses (Compatibility Mode off).
81. **Apple Metal documentation** — <https://developer.apple.com/documentation/metal> · *doc* — Compute and threadgroup memory limits that shape the sort implementation.
82. **Apple — Metal feature set tables** — <https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf> · *doc* — Per-GPU-family limits (threadgroup memory, SIMD width) for older-iPhone tiers.
83. **Apple — Optimizing GPU performance (Xcode)** — <https://developer.apple.com/documentation/xcode/optimizing-gpu-performance> · *doc* — GPU counters and profiling workflow for the splat pass on device.
84. **Apple — Capturing a Metal workload in Xcode** — <https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-in-xcode> · *doc* — Frame capture to debug depth-sort glitches like issue #226 on a real iPhone.
85. **Onesweep: A Faster Least Significant Digit Radix Sort for GPUs** — <https://arxiv.org/abs/2206.01784> · *paper* — The radix-sort family behind the failing Metal path; context for why it breaks.
86. **Mobile-GS: Real-time Gaussian Splatting for Mobile Devices** — <https://arxiv.org/abs/2603.11531> · *paper* — Mobile-first real-time splatting. Check it against the Mobile-GS headroom claim in research/vendors/reconstruction-cost-and-trainer-analysis.md before relying on it.
87. **SuperSplat editor (PlayCanvas)** — <https://github.com/playcanvas/supersplat> · *repo* — Browser tool to inspect and clean splats from corpus runs without writing code.
88. **Spark (World Labs) — web splat renderer** — <https://github.com/sparkjsdev/spark> · *repo* — Another open renderer with sorting and LOD strategies worth comparing.

## G. Collision mesh and geometry

89. **Open3D documentation** — <https://www.open3d.org/docs/release/> · *doc* — Poisson reconstruction and mesh cleanup used for the collision mesh.
90. **Open3D — Surface reconstruction tutorial** — <https://www.open3d.org/docs/release/tutorial/geometry/surface_reconstruction.html> · *doc* — Poisson depth and density trimming that set mesh size (spike: depth 9).
91. **Screened Poisson Surface Reconstruction (Kazhdan and Hoppe)** — <https://www.cs.jhu.edu/~misha/MyPapers/ToG13.pdf> · *paper* — The algorithm behind the Open3D mesh step.
92. **PyMeshLab** — <https://github.com/cnr-isti-vclab/PyMeshLab> · *repo* — Decimation and cleanup filters used in the pipeline.
93. **TSDF fusion (Open3D pipelines)** — <https://www.open3d.org/docs/release/tutorial/pipelines/rgbd_integration.html> · *doc* — Depth-fusion alternative when LiDAR depth is present.
94. **Unity Manual — MeshCollider** — <https://docs.unity3d.com/Manual/class-MeshCollider.html> · *doc* — Runtime collider limits (cooking, convexity) that the exported mesh must respect.

## H. Pipeline infrastructure and privacy

95. **Modal documentation** — <https://modal.com/docs> · *vendor guide* — The serverless GPU host used for the spike (AUTH #033); image layers, GPU types, billing.
96. **Modal — pricing** — <https://modal.com/pricing> · *vendor guide* — Per-second GPU, CPU and memory rates behind cost.json (spike report §0).
97. **NVIDIA CUDA container images** — <https://hub.docker.com/r/nvidia/cuda> · *doc* — Base image family (cuda 12.4.1 cudnn devel) of the reconstruction Dockerfile.
98. **Inngest documentation** — <https://www.inngest.com/docs> · *doc* — Durable steps that submit, poll and store reconstruction jobs (M1-CAPT-02, M1-PIPE-01).
99. **Cloudflare R2 pricing** — <https://developers.cloudflare.com/r2/pricing/> · *vendor guide* — Zero-egress storage, named as the biggest delivery cost lever in the cost analysis.
100. **Backblaze B2 pricing** — <https://www.backblaze.com/cloud-storage/pricing> · *vendor guide* — The alternative zero-egress option in the cost analysis.
101. **ExifTool** — <https://exiftool.org/> · *doc* — Reference tool for verifying that GPS/EXIF/XMP and QuickTime location atoms are gone (SECURITY_CHECKLIST §4).
102. **ExifTool — QuickTime tags** — <https://exiftool.org/TagNames/QuickTime.html> · *doc* — Where MOV/MP4 location atoms live, for strip_metadata.py tests (M0-CAPT-01 AT-3).
103. **Pillow documentation** — <https://pillow.readthedocs.io/en/stable/> · *doc* — Python image I/O for re-encoding JPEG without metadata.
104. **pillow-heif** — <https://github.com/bigcat88/pillow_heif> · *repo* — HEIC read/write for stripping iPhone photos.
105. **Apple — AVAssetWriter** — <https://developer.apple.com/documentation/avfoundation/avassetwriter> · *doc* — On-device video writing that avoids location metadata at the source.
106. **ScanNet++: A High-Fidelity Dataset of 3D Indoor Scenes** — <https://arxiv.org/abs/2308.11417> · *paper* — Public indoor benchmark with DSLR + iPhone captures, usable before the Owner corpus exists (public data only, SECURITY_CHECKLIST §6.5).
