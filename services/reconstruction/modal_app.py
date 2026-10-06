"""Modal entrypoint for the reconstruction pipeline (M1-CAPT-03).

Runs our container pipeline on a scale-to-zero Modal GPU. The Operator supplies a
Modal token (MODAL_TOKEN_ID / MODAL_TOKEN_SECRET in the VM .env.local) and runs,
from the repo root:

    modal run services/reconstruction/modal_app.py \
        --images ./data/mipnerf360/room/images_4 --scan-id smoke --source public

Defaults (spike report 2026-09-26): CUDA COLMAP 4.1 — GPU SIFT extraction, GPU
matching (``--matcher auto``: exhaustive up to 500 images, else sequential with
vocab-tree loop detection), incremental ``mapper``. ``--sfm glomap`` selects the
GLOMAP global mapper (``colmap global_mapper``); ``--matcher exhaustive`` /
``sequential`` / ``vocab_tree`` force a matcher; ``--no-gpu-features`` CPU SIFT.
Training: Splatfacto profile ``scaled-10k-dense`` (``--profile`` for others),
hard splat cap ``--splat-budget`` (2M), cleaned + decimated collision mesh, A10G
(``--gpu L40S`` is ~25% faster, ~20% dearer). Decision + numbers:
research/vendors/reconstruction-spike-report.md.

SfM-only sweep (every matcher x mapper, no training), used to pick the defaults:

    modal run services/reconstruction/modal_app.py \
        --images ./data/mipnerf360/room/images_4 --bench --out ./out/bench

IMAGE LAYERS. The image is built from services/reconstruction/Dockerfile, one
cached Modal layer per ``# modal-layer:`` section (base, torch, gsplat,
nerfstudio, colmap), so editing a late section never rebuilds the gsplat CUDA
compile. The ``reconstruction/`` package is NOT baked in: it is mounted at
container start (``add_local_dir``), so code edits never rebuild the image. The
build context is pinned to this directory (``context_dir``) and no layer COPYs
anything, so nothing elsewhere in the repo (``.env.local``, ``.secrets-local/``)
can enter the image.

Only ``public`` and ``corpus`` sources may run here; ``user`` scans are rejected
locally before upload and again in the container (ADR-0005 / AUTH #030).

Spend: the Modal workspace budget / spend limit (Owner) is the real cumulative cap.
The in-pipeline guard (AUTH #031 $100 / $50-per-day) starts from a fresh ledger on
every run, so it only stops a single run whose estimate would cross a cap.
``cost.json`` prices GPU + CPU + memory the way Modal bills them.
"""

from __future__ import annotations

import io
import json
import os
import tarfile
from pathlib import Path

import modal

_HERE = Path(__file__).parent
_LAYER = "# modal-layer:"
_SKIP = "# modal-skip"

# Reserved resources. CPU/memory are billed as max(reserved, used) per second;
# the hard CPU limit stops a CPU-heavy step from bursting onto the bill (the
# 2026-09-25 smoke run's CPU COLMAP averaged ~20 cores against 8 reserved).
CPU_CORES = 8.0
MEMORY_MIB = 16384
GPU = "A10G"
# Modal GPU list prices, $/hour (`modal billing rates`, 2026-09-26). The gsplat
# layer is compiled for sm_80 / sm_86 / sm_89 only, so these are the usable
# tiers (H100 / B200 / RTX PRO 6000 would need another arch in the Dockerfile).
GPU_RATES = {"A10G": 1.10, "L4": 0.80, "L40S": 1.95, "A100-40GB": 2.10}


def dockerfile_layers(text: str) -> list[list[str]]:
    """Split the Dockerfile into its ``# modal-layer:`` sections.

    Comment and blank lines are dropped (so comment edits never invalidate a
    cached layer); everything from ``# modal-skip`` on is ignored.
    """
    layers: list[list[str]] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith(_SKIP):
            break
        if line.startswith(_LAYER):
            layers.append([])
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if layers:
            layers[-1].append(line)
    return layers


def build_image() -> modal.Image:
    # modal_app.py is re-imported inside the container, where only it (plus the
    # mounts below) exists; the Dockerfile is mounted too so the image
    # definition evaluates identically there. The mount is not an image layer,
    # so it never triggers a rebuild.
    layers = dockerfile_layers((_HERE / "Dockerfile").read_text(encoding="utf-8"))
    base, *rest = layers
    if not base or not base[0].startswith("FROM "):
        raise RuntimeError("Dockerfile's first modal-layer must start with FROM")
    tag = base[0].split()[1]
    img = modal.Image.from_registry(tag, setup_dockerfile_commands=base[1:])
    for commands in rest:
        img = img.dockerfile_commands(commands, context_dir=_HERE)
    return (
        img.workdir("/work")
        .add_local_file(_HERE / "Dockerfile", "/root/Dockerfile")
        .add_local_dir(
            _HERE / "reconstruction",
            "/work/reconstruction",
            ignore=["**/__pycache__", "**/*.pyc"],
        )
    )


image = build_image()
app = modal.App("gj-recon-spike", image=image)

# Open-video corpus (M0-OWNER-01 / M1-PIPE-01): clips live in the private
# gj-corpus volume; frames and reconstructions are written back to it under
# /open-video-recon/<slug>/. The volume must already exist (never created here).
corpus_volume = modal.Volume.from_name("gj-corpus")
CORPUS_MOUNT = "/corpus"
CORPUS_VIDEO_ROOT = "open-video"
CORPUS_RECON_ROOT = "open-video-recon"
CLIP_ID_RE = r"^(rooms|tabletop)/[a-z0-9][a-z0-9-]*$"
# Per-clip hard wall limit on the GPU (bounds the worst-case bill: 30 min x
# (A10G + 8 cores + 16 GiB) ~= $0.80 per clip).
CORPUS_GPU_TIMEOUT_S = 1800
# SfM for video frames: GLOMAP global mapper on sequential matches, 4096 SIFT
# features. The tabletop pilot (196 frames at 3 fps, 8192 features, exhaustive)
# never finished the incremental mapper in 25 min (2+ min global BAs, degenerate
# steps); GLOMAP registered 196/196 in one model. (The Mip-NeRF room default,
# incremental + exhaustive, stays the default for photo sets.)
CORPUS_SFM = "glomap"
CORPUS_MATCHER = "sequential"
CORPUS_MAX_FEATURES = 4096
FRAMES_CPU_CORES = 8.0
FRAMES_MEMORY_MIB = 8192

# Small CPU-only image for video -> frames (ffmpeg decode + OpenCV sharpness).
# Kept apart from the CUDA image so decoding never holds a GPU. The Dockerfile
# is mounted for the same reason as in build_image (module re-import).
frames_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install("opencv-python-headless==4.10.0.84", "numpy==1.26.4")
    .env({"PYTHONPATH": "/work"})
    .workdir("/work")
    .add_local_file(_HERE / "Dockerfile", "/root/Dockerfile")
    .add_local_dir(
        _HERE / "reconstruction",
        "/work/reconstruction",
        ignore=["**/__pycache__", "**/*.pyc"],
    )
)


def _untar(images_tar: bytes, dest: Path) -> int:
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(images_tar)) as tar:
        tar.extractall(dest, filter="data")  # noqa: S202 - archive is authored locally below
    return sum(1 for p in dest.iterdir() if p.is_file())


@app.function(gpu=GPU, cpu=(CPU_CORES, CPU_CORES), memory=MEMORY_MIB, timeout=3600)
def reconstruct(
    images_tar: bytes,
    scan_id: str,
    source: str,
    rate_per_hour_usd: float,
    sfm: str = "colmap",
    matcher: str = "auto",
    gpu_features: bool = True,
    gpu: str = GPU,
    profile: str = "",
    splat_budget: int = 2_000_000,
    cpu_cores: float = CPU_CORES,
) -> tuple[dict, bytes, bytes, bytes]:
    """SfM -> train (+cap, eval) -> compress -> mesh; return (cost sheet, splat, mesh, preview).

    ``gpu`` / ``cpu_cores`` only label and price the cost sheet: the caller
    picks the hardware with ``reconstruct.with_options(gpu=..., cpu=...)``. ``profile`` names a
    ``trainer.PROFILES`` schedule ("" = the default).
    """
    import tempfile

    from reconstruction import (
        CostLedger,
        GsplatTrainer,
        Open3DMesher,
        ReconstructionConfig,
        ScanInput,
        SplatTransformCompressor,
        require_offsite_source,
        run_pipeline,
        select_sfm,
    )
    from reconstruction.cost import ResourceMeter
    from reconstruction.spike import cost_sheet

    scan_source = require_offsite_source(source)  # defence in depth: never a user scan
    # Meter the whole container job (untar included): that is what Modal bills.
    meter = ResourceMeter(cores=cpu_cores, memory_gib=MEMORY_MIB / 1024)
    use_gpu = gpu_features and os.environ.get("GJ_COLMAP_CUDA") == "1"
    sfm_adapter = select_sfm(sfm, use_gpu=use_gpu, matcher=matcher)

    work = Path(tempfile.mkdtemp())
    image_count = _untar(images_tar, work / "images")
    scan = ScanInput(
        scan_id=scan_id,
        image_dir=work / "images",
        image_count=image_count,
        source=scan_source,
    )
    run = run_pipeline(
        scan,
        ReconstructionConfig(sfm=sfm, splat_budget=splat_budget),
        sfm=sfm_adapter,
        trainer=GsplatTrainer(profile=profile or None),
        compressor=SplatTransformCompressor(),
        mesher=Open3DMesher(),
        work_dir=work / "out",
        ledger=CostLedger(),
        gpu_rate_per_hour_usd=rate_per_hour_usd,
        meter=meter,
    )
    sheet = cost_sheet(run)
    sheet["host"] = {"gpu": gpu, "cpu_cores": cpu_cores, "memory_mib": MEMORY_MIB}
    preview = run.model.preview_image if run.model else None
    return (
        sheet,
        run.package.splat.path.read_bytes(),
        run.package.mesh.path.read_bytes(),
        preview.read_bytes() if preview else b"",
    )


@app.function(gpu=GPU, cpu=(CPU_CORES, CPU_CORES), memory=MEMORY_MIB, timeout=3600)
def sfm_bench(images_tar: bytes, source: str, matchers: str, mappers: str) -> dict:
    """SfM-only sweep over matcher x mapper combinations (no training)."""
    import tempfile
    import time

    from reconstruction import ScanInput, require_offsite_source
    from reconstruction.cost import ResourceMeter
    from reconstruction.sfm import benchmark_sfm

    scan_source = require_offsite_source(source)
    meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024).start()
    started = time.monotonic()
    work = Path(tempfile.mkdtemp())
    count = _untar(images_tar, work / "images")
    scan = ScanInput("bench", work / "images", count, scan_source)
    rows = benchmark_sfm(
        scan,
        work / "sfm",
        matchers=tuple(matchers.split(",")),
        mappers=tuple(mappers.split(",")),
        use_gpu=os.environ.get("GJ_COLMAP_CUDA") == "1",
    )
    usage = meter.stop()
    return {
        "rows": rows,
        "wall_s": round(time.monotonic() - started, 1),
        "avg_used_cores": round(usage.used_core_seconds / max(usage.wall_seconds, 1e-9), 2),
        "peak_memory_gib": round(usage.peak_memory_gib, 2),
        "usage_source": usage.source,
    }


@app.function(gpu=GPU, cpu=(CPU_CORES, CPU_CORES), memory=MEMORY_MIB, timeout=3600)
def sfm_export(images_tar: bytes, source: str) -> tuple[bytes, dict]:
    """Default SfM only; return the sparse model as a tar (+ stats) for ``train_bench``."""
    import tempfile

    from reconstruction import ScanInput, require_offsite_source, select_sfm

    scan_source = require_offsite_source(source)
    work = Path(tempfile.mkdtemp())
    count = _untar(images_tar, work / "images")
    scan = ScanInput("bench", work / "images", count, scan_source)
    use_gpu = os.environ.get("GJ_COLMAP_CUDA") == "1"
    poses = select_sfm("colmap", use_gpu=use_gpu).run(scan, work / "out")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        tar.add(poses.sparse_dir, arcname="sparse")
    stats = dict(poses.stats or {})
    stats["registered_images"] = poses.registered_images
    return buf.getvalue(), stats


@app.function(gpu=GPU, cpu=(CPU_CORES, CPU_CORES), memory=MEMORY_MIB, timeout=3600)
def train_bench(
    images_tar: bytes,
    sparse_tar: bytes,
    source: str,
    profile: str,
    splat_budget: int,
    gpu: str,
    rate_per_hour_usd: float,
    growth_limit: bool = True,
) -> dict:
    """Train (+cap, eval) -> compress -> mesh from a fixed SfM model; return timings + cost.

    Training-only sweep (``--train-bench``): every profile trains from the same
    poses, so differences are the trainer's alone. The cost is this container's
    whole job (untar included), priced like ``cost.json``.
    """
    import tempfile
    import time

    from reconstruction import (
        CameraPoses,
        GsplatTrainer,
        Open3DMesher,
        ReconstructionConfig,
        SplatTransformCompressor,
        require_offsite_source,
    )
    from reconstruction.cost import ResourceMeter

    require_offsite_source(source)
    meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024).start()
    started = time.monotonic()
    work = Path(tempfile.mkdtemp())
    count = _untar(images_tar, work / "images")
    with tarfile.open(fileobj=io.BytesIO(sparse_tar)) as tar:
        tar.extractall(work / "out", filter="data")  # noqa: S202 - produced by sfm_export
    poses = CameraPoses("bench", work / "out" / "sparse", count, image_dir=work / "images")
    config = ReconstructionConfig(splat_budget=splat_budget)
    t0 = time.monotonic()
    trainer = GsplatTrainer(profile=profile, growth_limit=growth_limit)
    model = trainer.train(poses, work / "out", config)
    t1 = time.monotonic()
    compressed = SplatTransformCompressor().compress(model, work / "out", config)
    t2 = time.monotonic()
    mesh = Open3DMesher().derive(model, work / "out")
    t3 = time.monotonic()
    usage = meter.stop()
    wall = time.monotonic() - started
    gpu_usd = wall / 3600 * rate_per_hour_usd
    return {
        "profile": profile,
        "gpu": gpu,
        "splat_budget": splat_budget,
        "growth_limit": growth_limit,
        "splat_count": model.splat_count,
        "spz_bytes": compressed.size_bytes,
        "quality": model.metrics,
        "stage_seconds": {
            "setup": round(t0 - started, 2),
            "train": round(t1 - t0, 2),
            "compress": round(t2 - t1, 2),
            "mesh": round(t3 - t2, 2),
        },
        "mesh": {"triangles": mesh.triangle_count, "bytes": mesh.size_bytes, **(mesh.stats or {})},
        "wall_s": round(wall, 2),
        "gpu_usd": round(gpu_usd, 4),
        "cpu_usd": round(usage.cpu_usd(), 4),
        "memory_usd": round(usage.memory_usd(), 4),
        "usd": round(gpu_usd + usage.cpu_usd() + usage.memory_usd(), 4),
        "avg_used_cores": round(usage.used_core_seconds / max(usage.wall_seconds, 1e-9), 2),
        "peak_memory_gib": round(usage.peak_memory_gib, 2),
    }


@app.function(cpu=(4.0, 4.0), memory=8192, timeout=1800)
def mesh_bench(splats: dict[str, bytes], variants: dict[str, dict]) -> dict:
    """Collision-mesh rules sweep on existing splats (CPU only, no GPU).

    Each splat (.spz / .ply) is meshed with every ``MeshFilter`` variant; per
    variant it reports size / triangles / box per splat and the symmetric
    Chamfer distance between the meshes of every pair of splats (the same scene
    from different runs), i.e. how stable the mesh *shape* is run to run.
    """
    import itertools
    import subprocess
    import tempfile

    import numpy as np
    import open3d as o3d
    from reconstruction import Open3DMesher, SplatModel
    from reconstruction.models import read_ply_vertex_count
    from reconstruction.splat_ops import MeshFilter

    work = Path(tempfile.mkdtemp())
    plys = {}
    for name, data in splats.items():
        src = work / name
        src.write_bytes(data)
        ply = src if src.suffix == ".ply" else work / f"{src.stem}.ply"
        if src.suffix != ".ply":
            subprocess.run(["splat-transform", str(src), str(ply)], check=True)
        plys[name] = ply
    result: dict = {}
    for vname, kwargs in variants.items():
        rules = MeshFilter(**kwargs)
        rows, samples = {}, {}
        for name, ply in plys.items():
            out = work / vname / name
            out.mkdir(parents=True)
            model = SplatModel(Path(name).stem, ply, read_ply_vertex_count(ply))
            mesh = Open3DMesher(rules).derive(model, out)
            rows[name] = {"bytes": mesh.size_bytes, "triangles": mesh.triangle_count, **mesh.stats}
            tri = o3d.io.read_triangle_mesh(str(mesh.path))
            samples[name] = tri.sample_points_uniformly(50_000)
        chamfer = {}
        for a, b in itertools.combinations(samples, 2):
            d_ab = np.asarray(samples[a].compute_point_cloud_distance(samples[b]))
            d_ba = np.asarray(samples[b].compute_point_cloud_distance(samples[a]))
            chamfer[f"{a}|{b}"] = {
                "mean": round(float((d_ab.mean() + d_ba.mean()) / 2), 4),
                "p95": round(float(max(np.percentile(d_ab, 95), np.percentile(d_ba, 95))), 4),
            }
        result[vname] = {"rules": kwargs, "meshes": rows, "chamfer": chamfer}
    return result


def _check_clip_id(clip_id: str) -> str:
    """Validate a corpus clip id (``rooms/<slug>`` / ``tabletop/<slug>``); return the slug."""
    import re

    if not re.match(CLIP_ID_RE, clip_id):
        raise ValueError(f"not a corpus clip id: {clip_id!r}")
    return clip_id.split("/", 1)[1]


@app.function(
    image=frames_image,
    cpu=(FRAMES_CPU_CORES, FRAMES_CPU_CORES),
    memory=FRAMES_MEMORY_MIB,
    timeout=1800,
    volumes={CORPUS_MOUNT: corpus_volume},
)
def extract_clip_frames(
    clip_id: str, max_frames: int = 0, long_side: int = 1600, max_fps: float = 0.0
) -> dict:
    """Corpus clip -> sharp frames in the volume (``<recon>/<slug>/frames``); return stats.

    Decodes only the clip's ``recommended_segments`` (ffmpeg, candidates at
    ``oversample`` x the planned rate, downscaled to ``long_side``), keeps the
    sharpest candidate per window (``video_frames.select_sharpest``) and writes
    ``frames.json`` (plan, per-frame clip time + sharpness). CPU only.
    """
    import shutil
    import subprocess
    import tempfile
    import time

    import cv2
    from reconstruction.cost import ResourceMeter
    from reconstruction.video_frames import plan_rate, select_sharpest

    slug = _check_clip_id(clip_id)
    meter = ResourceMeter(cores=FRAMES_CPU_CORES, memory_gib=FRAMES_MEMORY_MIB / 1024).start()
    started = time.monotonic()
    src_dir = Path(CORPUS_MOUNT) / CORPUS_VIDEO_ROOT / clip_id
    meta = json.loads((src_dir / "meta.json").read_text(encoding="utf-8"))
    plan = plan_rate(
        meta, max_frames, long_side=long_side, **({"max_fps": max_fps} if max_fps else {})
    )
    work = Path(tempfile.mkdtemp())
    side = long_side
    scale = f"scale=w='if(gt(iw,ih),{side},-2)':h='if(gt(iw,ih),-2,{side})':flags=area"
    cands: list[list[Path]] = []
    scores: list[list[float]] = []
    for si, seg in enumerate(plan.segments):
        seg_dir = work / f"seg{si:02d}"
        seg_dir.mkdir()
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-nostdin",
                "-ss", f"{seg.start_s:.3f}", "-to", f"{seg.end_s:.3f}",
                "-i", str(src_dir / "source.mp4"),
                "-an", "-vf", f"fps={plan.candidate_fps:.6f},{scale}",
                "-q:v", "2", str(seg_dir / "c%05d.jpg"),
            ],
            check=True,
        )  # fmt: skip
        files = sorted(seg_dir.glob("c*.jpg"))
        seg_scores = []
        for f in files:
            gray = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
            h, w = gray.shape
            k = 800 / max(h, w)
            gray = cv2.resize(gray, (round(w * k), round(h * k)), interpolation=cv2.INTER_AREA)
            seg_scores.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        cands.append(files)
        scores.append(seg_scores)
    picks = select_sharpest(scores, plan.oversample)
    out = Path(CORPUS_MOUNT) / CORPUS_RECON_ROOT / slug
    frames_dir = out / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)
    rows = []
    for n, (si, ci) in enumerate(picks):
        name = f"f{n:05d}.jpg"
        shutil.copyfile(cands[si][ci], frames_dir / name)
        t = plan.segments[si].start_s + (ci + 0.5) / plan.candidate_fps
        sharp = round(scores[si][ci], 1)
        rows.append({"name": name, "segment": si, "clip_s": round(t, 3), "sharpness": sharp})
    usage = meter.stop()
    wall = time.monotonic() - started
    stats = {
        "clip_id": clip_id,
        "plan": plan.as_dict(),
        "candidates": sum(len(c) for c in cands),
        "frames": len(rows),
        "blur_rejected": sum(-(-len(s) // plan.oversample) for s in scores) - len(rows),
        "resolution": _jpeg_size(cv2, frames_dir / rows[0]["name"]) if rows else None,
        "wall_s": round(wall, 1),
        "usd": round(usage.cpu_usd() + usage.memory_usd(), 4),
        "host": {"cpu_cores": FRAMES_CPU_CORES, "memory_mib": FRAMES_MEMORY_MIB},
    }
    (out / "frames.json").write_text(json.dumps({**stats, "frame_list": rows}, indent=2) + "\n")
    corpus_volume.commit()
    return stats


def _jpeg_size(cv2, path: Path) -> list[int]:
    height, width = cv2.imread(str(path)).shape[:2]
    return [width, height]


def _compose_previews(renders: list[Path]) -> tuple[bytes, bytes]:
    """(preview, tile) JPEGs from eval renders (each ground truth | render, side by side).

    preview: up to two views stacked, 1280 px wide (ground truth left, splat right);
    tile: the splat half of the first view, 640 px wide (contact sheet).
    """
    from PIL import Image

    rows = [Image.open(p).convert("RGB") for p in renders[:2]]
    if not rows:
        return b"", b""
    scaled = [r.resize((1280, round(r.height * 1280 / r.width)), Image.LANCZOS) for r in rows]
    sheet = Image.new("RGB", (1280, sum(r.height for r in scaled)))
    y = 0
    for r in scaled:
        sheet.paste(r, (0, y))
        y += r.height
    first = rows[0]
    half = first.crop((first.width // 2, 0, first.width, first.height))
    tile = half.resize((640, round(half.height * 640 / half.width)), Image.LANCZOS)
    out_preview, out_tile = io.BytesIO(), io.BytesIO()
    sheet.save(out_preview, "JPEG", quality=85)
    tile.save(out_tile, "JPEG", quality=85)
    return out_preview.getvalue(), out_tile.getvalue()


@app.function(
    gpu=GPU,
    cpu=(CPU_CORES, CPU_CORES),
    memory=MEMORY_MIB,
    timeout=CORPUS_GPU_TIMEOUT_S,
    volumes={CORPUS_MOUNT: corpus_volume},
)
def reconstruct_clip(
    clip_id: str,
    rate_per_hour_usd: float,
    gpu: str = GPU,
    profile: str = "",
    splat_budget: int = 2_000_000,
    sfm: str = CORPUS_SFM,
    matcher: str = CORPUS_MATCHER,
    max_features: int = CORPUS_MAX_FEATURES,
) -> dict:
    """Reconstruct one corpus clip from its extracted frames; write outputs to the volume.

    Reads ``<recon>/<slug>/frames`` (``extract_clip_frames``), runs the default
    pipeline and writes ``<slug>.spz``, ``splat.ply``, ``collision.obj``,
    ``sparse/`` (COLMAP model), ``renders/`` (held-out ground truth | render),
    ``preview.jpg`` and ``run.json`` next to them. Returns ``run.json`` plus the
    preview / tile JPEG bytes. A failed run still writes ``run.json`` (why).
    """
    import shutil
    import tempfile
    import time
    import traceback

    from reconstruction import (
        CostLedger,
        GsplatTrainer,
        Open3DMesher,
        ReconstructionConfig,
        ScanInput,
        SplatTransformCompressor,
        require_offsite_source,
        run_pipeline,
        select_sfm,
    )
    from reconstruction.cost import ResourceMeter
    from reconstruction.spike import cost_sheet

    slug = _check_clip_id(clip_id)
    scan_source = require_offsite_source("corpus")
    started = time.monotonic()
    # job_meter prices the whole container job (copy-in / copy-out included),
    # meter only the pipeline stages (cost_sheet), like ``reconstruct``.
    job_meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024).start()
    meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024)
    corpus_volume.reload()
    out = Path(CORPUS_MOUNT) / CORPUS_RECON_ROOT / slug
    work = Path(tempfile.mkdtemp())
    shutil.copytree(out / "frames", work / "images")
    frames = json.loads((out / "frames.json").read_text(encoding="utf-8"))
    count = sum(1 for p in (work / "images").iterdir() if p.is_file())
    record: dict = {
        "clip_id": clip_id,
        "slug": slug,
        "gpu": gpu,
        "rate_per_hour_usd": rate_per_hour_usd,
        "frames_used": count,
        "frames": {k: v for k, v in frames.items() if k != "frame_list"},
        "outputs": f"gj-corpus:/{CORPUS_RECON_ROOT}/{slug}/",
        "config": {
            "sfm": sfm,
            "matcher": matcher,
            "max_features": max_features,
            "profile": profile or "default (scaled-10k-dense)",
            "splat_budget": splat_budget,
        },
    }
    preview = tile = b""
    try:
        use_gpu = os.environ.get("GJ_COLMAP_CUDA") == "1"
        run = run_pipeline(
            ScanInput(slug, work / "images", count, scan_source),
            ReconstructionConfig(splat_budget=splat_budget, sfm=sfm),
            sfm=select_sfm(sfm, use_gpu=use_gpu, matcher=matcher, max_features=max_features),
            trainer=GsplatTrainer(profile=profile or None),
            compressor=SplatTransformCompressor(),
            mesher=Open3DMesher(),
            work_dir=work / "out",
            ledger=CostLedger(),
            gpu_rate_per_hour_usd=rate_per_hour_usd,
            meter=meter,
        )
        sheet = cost_sheet(run)
        registered = run.poses.registered_images if run.poses else 0
        record.update(
            status="ok",
            registered_images=registered,
            registration_pct=round(100 * registered / max(count, 1), 1),
            pipeline=sheet,
        )
        shutil.copyfile(run.package.splat.path, out / f"{slug}.{sheet['format']}")
        shutil.copyfile(run.model.ply_path, out / "splat.ply")
        shutil.copyfile(run.package.mesh.path, out / "collision.obj")
        if run.poses:
            if (out / "sparse").exists():
                shutil.rmtree(out / "sparse")
            shutil.copytree(run.poses.sparse_dir, out / "sparse")
        render_dir = run.model.ply_path.parent / "eval_renders"
        renders = sorted(render_dir.glob("*.png")) if render_dir.is_dir() else []
        if renders:
            picks = sorted({renders[len(renders) // 3], renders[(2 * len(renders)) // 3]})
            (out / "renders").mkdir(exist_ok=True)
            for p in picks:
                shutil.copyfile(p, out / "renders" / p.name)
            preview, tile = _compose_previews(picks)
            (out / "preview.jpg").write_bytes(preview)
    except Exception as exc:  # noqa: BLE001 - record why a clip failed, keep the batch going
        record.update(status="fail", error=f"{type(exc).__name__}: {exc}"[:500])
        record["traceback"] = traceback.format_exc()[-2000:]
    wall = time.monotonic() - started
    usage = job_meter.stop()
    cpu_usd, mem_usd = usage.cpu_usd(), usage.memory_usd()
    gpu_usd = wall / 3600 * rate_per_hour_usd
    record["timings_s"] = {"function_wall": round(wall, 1)}
    record["cost_usd"] = {
        "gpu": round(gpu_usd, 4),
        "cpu": round(cpu_usd, 4),
        "memory": round(mem_usd, 4),
        "frames_cpu": frames.get("usd", 0.0),
        "total": round(gpu_usd + cpu_usd + mem_usd + frames.get("usd", 0.0), 4),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    corpus_volume.commit()
    return {**record, "_preview": preview, "_tile": tile}


@app.function(
    gpu=GPU,
    cpu=(CPU_CORES, CPU_CORES),
    memory=MEMORY_MIB,
    timeout=3600,
    volumes={CORPUS_MOUNT: corpus_volume},
)
def retrain_clip(
    clip_id: str,
    profile: str,
    tag: str,
    rate_per_hour_usd: float,
    gpu: str = GPU,
    splat_budget: int = 1_500_000,
) -> dict:
    """Retrain one reconstructed corpus clip from its saved frames + SfM model.

    Reuses ``<recon>/<slug>/frames`` and ``sparse/`` (so the poses and the world
    frame match the first run) and trains with ``profile`` (``trainer.PROFILES``).
    Writes ``splat.ply``, ``renders/`` and ``run.json`` under
    ``<recon>/<slug>/retrain-<tag>/``; the first run's outputs are untouched.
    """
    import re
    import shutil
    import tempfile
    import time

    from reconstruction import (
        CameraPoses,
        GsplatTrainer,
        ReconstructionConfig,
        require_offsite_source,
    )
    from reconstruction.cost import ResourceMeter

    slug = _check_clip_id(clip_id)
    if not re.fullmatch(r"[a-z0-9-]{1,40}", tag):
        raise ValueError(f"bad tag {tag!r}")
    require_offsite_source("corpus")
    started = time.monotonic()
    meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024).start()
    corpus_volume.reload()
    src = Path(CORPUS_MOUNT) / CORPUS_RECON_ROOT / slug
    work = Path(tempfile.mkdtemp())
    shutil.copytree(src / "frames", work / "images")
    shutil.copytree(src / "sparse", work / "out" / "sparse")
    count = sum(1 for p in (work / "images").iterdir() if p.is_file())
    poses = CameraPoses(slug, work / "out" / "sparse", count, image_dir=work / "images")
    model = GsplatTrainer(profile=profile).train(
        poses, work / "out", ReconstructionConfig(splat_budget=splat_budget)
    )
    dest = src / f"retrain-{tag}"
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "renders").mkdir(parents=True)
    shutil.copyfile(model.ply_path, dest / "splat.ply")
    render_dir = model.ply_path.parent / "eval_renders"
    for p in sorted(render_dir.glob("*.png")) if render_dir.is_dir() else []:
        shutil.copyfile(p, dest / "renders" / p.name)
    usage = meter.stop()
    wall = time.monotonic() - started
    gpu_usd = wall / 3600 * rate_per_hour_usd
    record = {
        "clip_id": clip_id,
        "tag": tag,
        "profile": profile,
        "gpu": gpu,
        "splat_budget": splat_budget,
        "splat_count": model.splat_count,
        "quality": model.metrics,
        "wall_s": round(wall, 1),
        "cost_usd": {
            "gpu": round(gpu_usd, 4),
            "cpu": round(usage.cpu_usd(), 4),
            "memory": round(usage.memory_usd(), 4),
            "total": round(gpu_usd + usage.cpu_usd() + usage.memory_usd(), 4),
        },
        "outputs": f"gj-corpus:/{CORPUS_RECON_ROOT}/{slug}/retrain-{tag}/",
    }
    (dest / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    corpus_volume.commit()
    return record


# Owner-consented own-room test captures (AUTH #046): kept apart from the
# open-video corpus under gj-corpus:/owner-capture/<id>/. The operator box
# extracts the frames and blurs every face (framed photos, reflections)
# BEFORE uploading ``frames/``; the video itself never leaves the box. Nothing
# from here is ever committed (metrics + text only); everything under the
# capture folder is deletable on request.
OWNER_CAPTURE_ROOT = "owner-capture"
OWNER_CAPTURE_ID_RE = r"^room-[0-9]{2}$"


def _check_capture_id(capture_id: str) -> str:
    """Validate an Owner capture id (``room-NN``)."""
    import re

    if not re.match(OWNER_CAPTURE_ID_RE, capture_id):
        raise ValueError(f"not an owner capture id: {capture_id!r}")
    return capture_id


@app.function(
    gpu=GPU,
    cpu=(CPU_CORES, CPU_CORES),
    memory=MEMORY_MIB,
    timeout=3600,
    volumes={CORPUS_MOUNT: corpus_volume},
)
def reconstruct_owner_capture(
    capture_id: str,
    rate_per_hour_usd: float,
    gpu: str = GPU,
    profile: str = "quality-30k",
    splat_budget: int = 1_500_000,
    sfm: str = "glomap",
    matcher: str = "exhaustive",
    max_features: int = 8192,
) -> dict:
    """SfM + display-quality training of one Owner capture from its blurred frames.

    Reads ``owner-capture/<id>/frames`` (already face-blurred on the box) and
    writes ``splat.ply``, ``sparse/``, ``renders/`` (held-out ground truth |
    render) and ``run.json`` next to them. The source label is ``corpus``
    (Owner-supplied, consented: AUTH #046); real user scans stay rejected.
    """
    import shutil
    import tempfile
    import time
    import traceback

    from reconstruction import (
        CostLedger,
        GsplatTrainer,
        Open3DMesher,
        ReconstructionConfig,
        ScanInput,
        SplatTransformCompressor,
        require_offsite_source,
        run_pipeline,
        select_sfm,
    )
    from reconstruction.cost import ResourceMeter
    from reconstruction.spike import cost_sheet

    cid = _check_capture_id(capture_id)
    scan_source = require_offsite_source("corpus")
    started = time.monotonic()
    job_meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024).start()
    meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024)
    corpus_volume.reload()
    out = Path(CORPUS_MOUNT) / OWNER_CAPTURE_ROOT / cid
    work = Path(tempfile.mkdtemp())
    shutil.copytree(out / "frames", work / "images")
    count = sum(1 for p in (work / "images").iterdir() if p.is_file())
    record: dict = {
        "capture_id": cid,
        "gpu": gpu,
        "rate_per_hour_usd": rate_per_hour_usd,
        "frames_used": count,
        "outputs": f"gj-corpus:/{OWNER_CAPTURE_ROOT}/{cid}/",
        "config": {
            "sfm": sfm,
            "matcher": matcher,
            "max_features": max_features,
            "profile": profile,
            "splat_budget": splat_budget,
        },
    }
    try:
        use_gpu = os.environ.get("GJ_COLMAP_CUDA") == "1"
        run = run_pipeline(
            ScanInput(cid, work / "images", count, scan_source),
            ReconstructionConfig(splat_budget=splat_budget, sfm=sfm),
            sfm=select_sfm(sfm, use_gpu=use_gpu, matcher=matcher, max_features=max_features),
            trainer=GsplatTrainer(profile=profile),
            compressor=SplatTransformCompressor(),
            mesher=Open3DMesher(),
            work_dir=work / "out",
            ledger=CostLedger(),
            gpu_rate_per_hour_usd=rate_per_hour_usd,
            meter=meter,
        )
        registered = run.poses.registered_images if run.poses else 0
        record.update(
            status="ok",
            registered_images=registered,
            registration_pct=round(100 * registered / max(count, 1), 1),
            pipeline=cost_sheet(run),
        )
        shutil.copyfile(run.model.ply_path, out / "splat.ply")
        if run.poses:
            if (out / "sparse").exists():
                shutil.rmtree(out / "sparse")
            shutil.copytree(run.poses.sparse_dir, out / "sparse")
        render_dir = run.model.ply_path.parent / "eval_renders"
        if (out / "renders").exists():
            shutil.rmtree(out / "renders")
        (out / "renders").mkdir()
        for p in sorted(render_dir.glob("*.png")) if render_dir.is_dir() else []:
            shutil.copyfile(p, out / "renders" / p.name)
    except Exception as exc:  # noqa: BLE001 - record why the run failed
        record.update(status="fail", error=f"{type(exc).__name__}: {exc}"[:500])
        record["traceback"] = traceback.format_exc()[-2000:]
    wall = time.monotonic() - started
    usage = job_meter.stop()
    gpu_usd = wall / 3600 * rate_per_hour_usd
    record["timings_s"] = {"function_wall": round(wall, 1)}
    record["cost_usd"] = {
        "gpu": round(gpu_usd, 4),
        "cpu": round(usage.cpu_usd(), 4),
        "memory": round(usage.memory_usd(), 4),
        "total": round(gpu_usd + usage.cpu_usd() + usage.memory_usd(), 4),
    }
    (out / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    corpus_volume.commit()
    return record


@app.function(
    gpu=GPU,
    cpu=(CPU_CORES, CPU_CORES),
    memory=MEMORY_MIB,
    timeout=3600,
    volumes={CORPUS_MOUNT: corpus_volume},
)
def retrain_owner_capture(
    capture_id: str,
    profile: str,
    tag: str,
    rate_per_hour_usd: float,
    gpu: str = GPU,
    splat_budget: int = 400_000,
    score: tuple[str, ...] = (),
) -> dict:
    """Retrain one Owner capture from its saved (blurred) frames + SfM model (AUTH #046).

    Like :func:`retrain_clip` but under ``owner-capture/<id>/``: reuses ``frames/`` and
    ``sparse/`` so the poses, world frame and held-out views match the first run, and
    writes ``splat.ply``, ``renders/`` and ``run.json`` under ``retrain-<tag>/``. Each
    ``score`` entry is a PLY path relative to the capture folder (e.g. ``splat.ply``, the
    first full model, or ``shipped-v1-400k.ply``, the package that shipped); it is scored on
    the same held-out views by the same renderer (``ns_finish --score-ply``) and its renders
    land in ``retrain-<tag>/renders-<name>/``.
    """
    import re
    import shutil
    import tempfile
    import time

    from reconstruction import (
        CameraPoses,
        GsplatTrainer,
        ReconstructionConfig,
        require_offsite_source,
    )
    from reconstruction.cost import ResourceMeter

    cid = _check_capture_id(capture_id)
    if not re.fullmatch(r"[a-z0-9-]{1,40}", tag):
        raise ValueError(f"bad tag {tag!r}")
    require_offsite_source("corpus")
    started = time.monotonic()
    meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024).start()
    corpus_volume.reload()
    src = Path(CORPUS_MOUNT) / OWNER_CAPTURE_ROOT / cid
    scored: list[tuple[str, Path]] = []
    for rel in score:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}\.ply", rel):
            raise ValueError(f"bad score path {rel!r}")
        scored.append((re.sub(r"[^a-z0-9-]", "-", rel[:-4].lower())[:40], src / rel))
    work = Path(tempfile.mkdtemp())
    shutil.copytree(src / "frames", work / "images")
    shutil.copytree(src / "sparse", work / "out" / "sparse")
    count = sum(1 for p in (work / "images").iterdir() if p.is_file())
    poses = CameraPoses(cid, work / "out" / "sparse", count, image_dir=work / "images")
    model = GsplatTrainer(profile=profile, score_plys=tuple(scored)).train(
        poses, work / "out", ReconstructionConfig(splat_budget=splat_budget)
    )
    dest = src / f"retrain-{tag}"
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "renders").mkdir(parents=True)
    shutil.copyfile(model.ply_path, dest / "splat.ply")
    gs_dir = model.ply_path.parent
    for sub, target in [("eval_renders", "renders")] + [
        (f"eval_renders-{name}", f"renders-{name}") for name, _ in scored
    ]:
        if (gs_dir / sub).is_dir():
            (dest / target).mkdir(exist_ok=True)
            for p in sorted((gs_dir / sub).glob("*.png")):
                shutil.copyfile(p, dest / target / p.name)
    usage = meter.stop()
    wall = time.monotonic() - started
    gpu_usd = wall / 3600 * rate_per_hour_usd
    record = {
        "capture_id": cid,
        "tag": tag,
        "profile": profile,
        "gpu": gpu,
        "splat_budget": splat_budget,
        "splat_count": model.splat_count,
        "quality": model.metrics,
        "wall_s": round(wall, 1),
        "cost_usd": {
            "gpu": round(gpu_usd, 4),
            "cpu": round(usage.cpu_usd(), 4),
            "memory": round(usage.memory_usd(), 4),
            "total": round(gpu_usd + usage.cpu_usd() + usage.memory_usd(), 4),
        },
        "outputs": f"gj-corpus:/{OWNER_CAPTURE_ROOT}/{cid}/retrain-{tag}/",
    }
    (dest / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    corpus_volume.commit()
    return record


@app.local_entrypoint()
def owner_retrain(
    capture: str,
    profiles: str,
    gpu: str = "L40S",
    splat_budget: int = 400_000,
    score: str = "",
    tag_suffix: str = "400k",
) -> None:
    """Retrain an Owner capture once per comma-separated profile, in parallel.

    ``--score a.ply,b.ply`` (paths relative to the capture folder) are scored on the first
    profile's container only. Tag = ``<profile>-<tag_suffix>``.
    """
    if gpu not in GPU_RATES:
        raise SystemExit(f"--gpu must be one of {sorted(GPU_RATES)}, got {gpu!r}")
    _check_capture_id(capture)
    names = [p for p in profiles.split(",") if p]
    extra = tuple(p for p in score.split(",") if p)
    jobs = [
        (
            capture,
            p,
            f"{p}-{tag_suffix}",
            GPU_RATES[gpu],
            gpu,
            splat_budget,
            extra if i == 0 else (),
        )
        for i, p in enumerate(names)
    ]
    fn = retrain_owner_capture.with_options(gpu=gpu)
    for record in fn.starmap(jobs, return_exceptions=True):
        print(json.dumps(record, indent=2, default=str))


@app.local_entrypoint()
def owner_capture(capture: str, gpu: str = "L40S", profile: str = "quality-30k") -> None:
    """Reconstruct one Owner capture already uploaded (blurred) to the volume."""
    if gpu not in GPU_RATES:
        raise SystemExit(f"--gpu must be one of {sorted(GPU_RATES)}, got {gpu!r}")
    _check_capture_id(capture)
    fn = reconstruct_owner_capture.with_options(gpu=gpu)
    record = fn.remote(capture, GPU_RATES[gpu], gpu, profile)
    print(json.dumps(record, indent=2, default=str))


@app.local_entrypoint()
def retrain(clip: str, profiles: str, gpu: str = "L40S", splat_budget: int = 1_500_000) -> None:
    """Retrain ``clip`` once per comma-separated ``profiles`` (in parallel); tag = profile."""
    if gpu not in GPU_RATES:
        raise SystemExit(f"--gpu must be one of {sorted(GPU_RATES)}, got {gpu!r}")
    names = [p for p in profiles.split(",") if p]
    jobs = [(clip, p, p, GPU_RATES[gpu], gpu, splat_budget) for p in names]
    fn = retrain_clip.with_options(gpu=gpu)
    for record in fn.starmap(jobs, return_exceptions=True):
        print(json.dumps(record, indent=2, default=str))


def _tar_images(images: str, source: str) -> bytes:
    # Local import: modal puts this file's directory on sys.path. Validate before
    # any upload so a user scan never leaves the machine.
    from reconstruction import require_offsite_source

    require_offsite_source(source)
    src = Path(images)
    if not src.is_dir():
        raise SystemExit(f"--images {images!r} is not a directory")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for p in sorted(src.iterdir()):
            if p.is_file():
                tar.add(p, arcname=p.name)
    return buf.getvalue()


# Pre-flight estimate for one corpus clip: the benchmark room (311 frames,
# ~1.6 MP) cost ~$0.19 on A10G; scale by frame count with a 1.5x margin.
BENCH_FRAMES = 311
BENCH_USD_A10G = 0.19
CLIP_CAP_USD = 2.0


def _run_corpus(
    clips_arg: str,
    gpu: str,
    rate: float,
    profile: str,
    splat_budget: int,
    max_frames: int,
    skip_extract: bool,
    max_fps: float,
    budget: float,
    spent: float,
    out_dir: Path,
    previews: str,
    sfm_opts: tuple[str, str, int] = (CORPUS_SFM, CORPUS_MATCHER, CORPUS_MAX_FEATURES),
) -> None:
    """Corpus mode: frames (CPU) then reconstruction (GPU, in parallel) per clip."""
    manifest = json.loads((_HERE / "corpus" / "open_video_corpus.json").read_text("utf-8"))
    known = [c["id"] for c in manifest["clips"]]
    clips = known if clips_arg == "all" else [c for c in clips_arg.split(",") if c]
    unknown = sorted(set(clips) - set(known))
    if unknown:
        raise SystemExit(f"not in open_video_corpus.json: {unknown}")
    frames: dict[str, dict] = {}
    if not skip_extract:
        for clip, res in zip(
            clips,
            extract_clip_frames.starmap(
                [(c, max_frames, 1600, max_fps) for c in clips], return_exceptions=True
            ),
            strict=True,
        ):
            if isinstance(res, BaseException):
                print(f"[frames] {clip}: FAILED {res!r}")
                continue
            frames[clip] = res
            spent += res["usd"]
            print(f"[frames] {clip}: {res['frames']} frames ({res['candidates']} candidates, "
                  f"{res['wall_s']} s, ${res['usd']:.3f})")  # fmt: skip
    else:
        frames = {c: {"frames": BENCH_FRAMES} for c in clips}
    gpu_scale = rate / GPU_RATES["A10G"]
    todo, projected = [], spent
    for clip in clips:
        if clip not in frames:
            continue
        est = 1.5 * BENCH_USD_A10G * gpu_scale * frames[clip]["frames"] / BENCH_FRAMES
        if est > CLIP_CAP_USD:
            print(f"[plan] {clip}: projected ${est:.2f} > ${CLIP_CAP_USD}; skipped (subsample)")
            continue
        todo.append(clip)
        projected += est
    print(f"[plan] {len(todo)} clips on {gpu}; projected job ${projected:.2f} (cap ${budget})")
    if projected > budget:
        raise SystemExit(f"projected ${projected:.2f} would exceed the ${budget} job cap; stopping")
    prev_dir = Path(previews) if previews else None
    if prev_dir:
        prev_dir.mkdir(parents=True, exist_ok=True)
    fn = reconstruct_clip.with_options(gpu=gpu)
    jobs = [(c, rate, gpu, profile, splat_budget, *sfm_opts) for c in todo]
    results = []
    for clip, res in zip(todo, fn.starmap(jobs, return_exceptions=True), strict=True):
        slug = clip.split("/", 1)[1]
        if isinstance(res, BaseException):
            res = {"clip_id": clip, "slug": slug, "status": "fail", "error": repr(res)[:500]}
        preview, tile = res.pop("_preview", b""), res.pop("_tile", b"")
        clip_dir = out_dir / slug
        clip_dir.mkdir(parents=True, exist_ok=True)
        (clip_dir / "run.json").write_text(json.dumps(res, indent=2) + "\n")
        if tile:
            (clip_dir / "tile.jpg").write_bytes(tile)
        if preview and prev_dir:
            (prev_dir / f"{slug}.jpg").write_bytes(preview)
        cost = res.get("cost_usd", {}).get("total", 0.0)
        spent += cost - res.get("cost_usd", {}).get("frames_cpu", 0.0)
        print(f"[recon] {clip}: {res.get('status')} reg={res.get('registration_pct')}% "
              f"psnr={res.get('pipeline', {}).get('quality', {}).get('psnr')} ${cost:.3f} "
              f"(job so far ${spent:.2f}) {res.get('error', '')}")  # fmt: skip
        results.append(res)
    summary = {"gpu": gpu, "job_usd_measured": round(spent, 4), "clips": results}
    (out_dir / "corpus-summary.json").write_text(json.dumps(summary, indent=2) + "\n")


@app.local_entrypoint()
def main(
    images: str = "",
    scan_id: str = "spike",
    source: str = "public",
    sfm: str = "colmap",
    matcher: str = "auto",
    gpu_features: bool = True,
    gpu: str = GPU,
    cpu: float = CPU_CORES,
    rate: float = 0.0,
    profile: str = "",
    splat_budget: int = 2_000_000,
    out: str = "./out",
    bench: bool = False,
    matchers: str = "exhaustive,sequential,vocab_tree",
    mappers: str = "colmap,glomap",
    train_bench_profiles: str = "",
    repeat: int = 1,
    sparse_cache: str = "",
    growth_limit: bool = True,
    mesh_splats: str = "",
    mesh_variants: str = "",
    corpus: str = "",
    max_frames: int = 0,
    max_fps: float = 0.0,
    skip_extract: bool = False,
    budget: float = 18.0,
    spent: float = 0.0,
    previews: str = "",
    corpus_sfm: str = CORPUS_SFM,
    corpus_matcher: str = CORPUS_MATCHER,
    max_features: int = CORPUS_MAX_FEATURES,
) -> None:
    """Tar a local image dir, run on Modal, save the outputs + cost sheet.

    ``--gpu`` picks the Modal GPU (``GPU_RATES``); ``--rate`` overrides its $/h
    (0 = list price); ``--cpu`` the reserved (= hard-limited) CPU cores.
    ``--profile`` a ``trainer.PROFILES`` schedule ("" = default);
    ``--splat-budget`` the hard splat cap.

    ``--bench`` runs the SfM-only matcher x mapper sweep instead (writes
    ``<out>/sfm-bench.json``); ``--matchers`` / ``--mappers`` pick the grid.

    ``--train-bench-profiles a,b,...`` runs the training-only sweep: SfM once
    (cached as ``--sparse-cache`` if given), then every profile ``--repeat``
    times in parallel on ``--gpu`` (writes ``<out>/train-bench.json``).
    ``--no-growth-limit`` trains uncapped so only the post-train prune enforces
    ``--splat-budget`` (cap stress test).

    ``--mesh-splats a.spz,b.spz`` runs the collision-mesh sweep on existing
    splats instead (CPU only; ``--mesh-variants`` = JSON ``{name: MeshFilter
    kwargs}``, default the current rules; writes ``<out>/mesh-bench.json``).

    ``--corpus all`` (or ``rooms/<slug>,tabletop/<slug>,...``) reconstructs
    open-video corpus clips from the gj-corpus volume instead (no local
    media): frames per clip on CPU (``--max-frames``, 0 = 300 / 400 for long
    clips; ``--max-fps``, 0 = 2; ``--skip-extract`` reuses them), then every clip in parallel on
    ``--gpu``. Stops before any GPU work if the projected job total (plus
    ``--spent`` already spent) would cross ``--budget``. Outputs stay in the
    volume under /open-video-recon/<slug>/; ``<out>/<slug>/run.json`` and
    ``--previews <dir>/<slug>.jpg`` are copied locally. SfM for video frames:
    ``--corpus-sfm`` (glomap) / ``--corpus-matcher`` (sequential) /
    ``--max-features`` (4096).
    """
    from reconstruction import SFM_CHOICES, require_offsite_source
    from reconstruction.sfm import MATCHER_CHOICES
    from reconstruction.trainer import PROFILES

    require_offsite_source(source)
    if gpu not in GPU_RATES:
        raise SystemExit(f"--gpu must be one of {sorted(GPU_RATES)}, got {gpu!r}")
    rate = rate or GPU_RATES[gpu]
    names = [p for p in train_bench_profiles.split(",") if p]
    for name in [*names, *([profile] if profile else [])]:
        if name not in PROFILES:
            raise SystemExit(f"unknown profile {name!r}; one of {sorted(PROFILES)}")
    if sfm not in SFM_CHOICES:
        raise SystemExit(f"--sfm must be one of {SFM_CHOICES}, got {sfm!r}")
    if matcher not in MATCHER_CHOICES:
        raise SystemExit(f"--matcher must be one of {MATCHER_CHOICES}, got {matcher!r}")
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if corpus:
        _run_corpus(
            corpus, gpu, rate, profile, splat_budget, max_frames, skip_extract, max_fps,
            budget, spent, out_dir, previews, (corpus_sfm, corpus_matcher, max_features),
        )  # fmt: skip
        return
    if mesh_splats:
        files = [Path(p) for p in mesh_splats.split(",") if p]
        splats = {f"{i}-{f.name}": f.read_bytes() for i, f in enumerate(files)}
        variants = json.loads(mesh_variants) if mesh_variants else {"default": {}}
        result = mesh_bench.remote(splats, variants)
        (out_dir / "mesh-bench.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return
    payload = _tar_images(images, source)

    if bench:
        result = sfm_bench.remote(payload, source, matchers, mappers)
        (out_dir / "sfm-bench.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return

    if names:
        cache = Path(sparse_cache) if sparse_cache else None
        if cache and cache.exists():
            sparse_tar, sfm_stats = cache.read_bytes(), {"cached": str(cache)}
        else:
            sparse_tar, sfm_stats = sfm_export.remote(payload, source)
            if cache:
                cache.write_bytes(sparse_tar)
        jobs = [
            (payload, sparse_tar, source, name, splat_budget, gpu, rate, growth_limit)
            for name in names
            for _ in range(repeat)
        ]
        rows = list(train_bench.with_options(gpu=gpu).starmap(jobs))
        result = {"gpu": gpu, "rate_per_hour_usd": rate, "sfm": sfm_stats, "rows": rows}
        (out_dir / "train-bench.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return

    fn = reconstruct.with_options(gpu=gpu, cpu=(cpu, cpu))
    sheet, splat_bytes, mesh_bytes, preview = fn.remote(
        payload, scan_id, source, rate, sfm, matcher, gpu_features, gpu, profile, splat_budget, cpu
    )
    (out_dir / f"{scan_id}.{sheet['format']}").write_bytes(splat_bytes)
    (out_dir / f"{scan_id}.obj").write_bytes(mesh_bytes)
    if preview:
        ext = ".png" if preview.startswith(b"\x89PNG") else ".jpg"
        (out_dir / f"{scan_id}-eval-view{ext}").write_bytes(preview)
    (out_dir / "cost.json").write_text(json.dumps(sheet, indent=2) + "\n")
    print(json.dumps(sheet, indent=2))
