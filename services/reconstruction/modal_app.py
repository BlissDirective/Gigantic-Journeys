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


@app.local_entrypoint()
def main(
    images: str,
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
