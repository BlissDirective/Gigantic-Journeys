# Reconstruction — API/cloud alternatives to Luma (buy side)

**Decision-support · observed 2026-09-17 · Coordinator research pass.** Server-side "POST a phone scan → get a 3D reconstruction" alternatives to Luma (whose reconstruction API is deprecated). Sourced; not legal advice. Data is **imagery of private homes** — data terms are a hard gate.

## Bottom line
Few vendors actually expose a reconstruction **API** (most are consumer apps or on-device SDKs). Of those that do:
- **#1 (conditional) — KIRI Engine API:** the only turnkey API matching the Luma workflow *and* returning our ideal output (splat **.ply** + optional mesh) from photos **or video**, ~$1/scan. **Catch:** weak/unclear data terms — only viable with a written no-train + DPA + deletion commitment.
- **Privacy-first — self-hosted RealityScan/RealityCapture (Epic)** or the open-source splat stack (see `reconstruction-selfhost.md`): data never leaves our infra.
- **Managed-with-DPA fallback — Autodesk APS Reality Capture API:** real enterprise DPA + explicit delete, but mesh-only, photos-only, and likely >10-min room times.

## Comparison
| Option | Real reconstruction API? | Output | Data terms (no-train / DPA / delete) | Price/scan | Room + Unity fit |
|---|---|---|---|---|---|
| **KIRI Engine API** | **Yes** — REST, upload photos *or* video → poll → download | **Splat (.ply) + optional mesh** (obj/fbx/glb/usdz/…) | **Weak/unclear:** silent on training; broad content license; **HK entity**; no DPA found | **~$1/scan** ($500 min prepay, 10 free) | **Best fit;** splat+mesh; room + tabletop |
| **Autodesk APS Reality Capture API** | **Yes** — REST (photoscene → process → retrieve → **delete**) | **Mesh + point cloud** (OBJ/FBX/…); **no splat** | **Strong:** enterprise DPA, explicit delete, no training claims | ~1 credit/50 photos (~$1–2/room) | **Mesh-only; photos-only** (no ARKit video/depth); ~15 min may exceed 10-min target |
| **Polycam Content-Management API (beta)** | **No** — manages/exports *existing* app captures; no create/upload endpoint | Splat + mesh (existing captures only) | Business/Enterprise: training **off by default** + opt-out; ToS still lets them license UGC "including training AI"; no DPA stated | Enterprise sales-gated | Great splats, but API can't do the server reconstruction step |
| **Niantic Scaniverse / NSDK** | **No open API** — cloud recon tied to their app; devs get an **on-device** Unity scanning framework | Splat (SPZ/PLY/GLB) + mesh | Data to Niantic; SDK license; no per-scan DPA | SDK licensing | Excellent SPZ splats + Unity, but not a server API |
| **RealityScan/RealityCapture (Epic)** | **Self-host** (desktop/CLI, Linux via Wine, Remote-Command REST/gRPC) | **Mesh only** (no splat) | **Strongest — data never leaves our infra**; no processor, no DPA needed | **Free** under $1M/yr rev (else $1,250/seat) | Superb mesh; we run a GPU worker (fits the Operator's long-running-ops role) |
| Matterport API | Yes, but pano/Pro-camera, proprietary, subscription | Proprietary twin; mesh via add-on; no splat | Enterprise | Expensive, sales-led | Misfit for tabletop — not recommended |

KIRI API facts: `POST https://api.kiriengine.app/api/v1/open/3dgs/image` (Bearer), 20–300 images, `isMesh` flag for mesh export, separate `/3dgs-scan/video-upload`; polls a task id. Operator: **KIRI Innovation (Hongkong) Limited**; User Agreement §7 grants a broad "irrevocable, perpetual … royalty-free … right to use/reproduce/publish/distribute" contributions; Privacy Policy (2024-08-26) is **silent on training, retention, deletion, DPA**.

## Recommendation
- **If buying:** **KIRI Engine API is #1 only conditional on** a written **no-train guarantee + DPA + retention/deletion controls + data-residency** answer (HK/China vs US/EU). Without those, **do not send real customer home scans** under its consumer terms — disqualified. **Autodesk APS** is the clean managed fallback if mesh-only + photos-only + slower times are acceptable (it has a genuine DPA and delete).
- **Strategic pick:** given the private-home data and the lock-in lesson from Luma, the **privacy-first self-host path** (`reconstruction-selfhost.md`) is the stronger long-term direction; a managed API (Autodesk/KIRI-with-terms) can **bridge early M1 validation** while the self-host pipeline is spiked.

## iOS/Unity reality check (any splat path)
On-device splat rendering works in URP (aras-p `UnityGaussianSplatting`; `denisislamov/GaussPlatUnity` for Unity 6 URP mobile, SPZ/PLY) but only ~**200–500K splats @ 30 fps** on iPhone. To hit ≤150 MB + smooth playback: cap/compress splats (SPZ/decimate), or **ship the mesh for gameplay/collision** and use splats selectively. **Meshes are the safe iPhone runtime.**

## Confirm before committing
- **KIRI:** written no-train + DPA + auto-deletion + data residency; commercial-use rights; status/download endpoints + real processing-time SLA (≤10 min); whether the video endpoint ingests ARKit video/depth/pose; per-scan cost at volume + credit expiry.
- **Autodesk APS:** cloud-credit cost per room job; real end-to-end time for 30–80 indoor photos; export formats (glTF/OBJ); DPA scope.
- **General:** get a sample room `.ply/.spz` from any splat vendor and measure splat count / file size / iPhone fps vs the ≤150 MB / 30 fps budget.

## Sources (observed 2026-09-17)
- KIRI API — https://docs.kiriengine.app · https://www.kiriengine.app/api · SDK — https://github.com/Kiri-Innovation/KIRI-ENGINE-SDK-API · agreement — https://www.kiriengine.app/user-agreement
- Autodesk APS Reality Capture — https://aps.autodesk.com/en/docs/reality-capture/v1/developers_guide/overview/ · Trust Center — https://www.autodesk.com/trust/overview
- Polycam API — https://learn.poly.cam/ (developer/API) · Niantic Scaniverse/NSDK — https://scaniverse.com/ · https://lightship.dev/
- RealityScan/RealityCapture — https://www.realityscan.com/ · Luma deprecation — https://lumalabs.ai/llm-info · https://github.com/lumalabs/lumaapi-python
