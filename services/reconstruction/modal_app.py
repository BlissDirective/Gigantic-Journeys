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
``sequential`` / ``vocab_tree`` force a matcher; ``--no-gpu-features`` CPU SIFT. Decision + numbers:
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
) -> tuple[dict, bytes, bytes, bytes]:
    """SfM -> train (+eval) -> compress -> mesh; return (cost sheet, splat, mesh, preview)."""
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
    meter = ResourceMeter(cores=CPU_CORES, memory_gib=MEMORY_MIB / 1024)
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
        ReconstructionConfig(sfm=sfm),
        sfm=sfm_adapter,
        trainer=GsplatTrainer(),
        compressor=SplatTransformCompressor(),
        mesher=Open3DMesher(),
        work_dir=work / "out",
        ledger=CostLedger(),
        gpu_rate_per_hour_usd=rate_per_hour_usd,
        meter=meter,
    )
    sheet = cost_sheet(run)
    sheet["host"] = {"gpu": GPU, "cpu_cores": CPU_CORES, "memory_mib": MEMORY_MIB}
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
    rate: float = 1.10,
    out: str = "./out",
    bench: bool = False,
    matchers: str = "exhaustive,sequential,vocab_tree",
    mappers: str = "colmap,glomap",
) -> None:
    """Tar a local image dir, run on Modal, save the outputs + cost sheet.

    ``--bench`` runs the SfM-only matcher x mapper sweep instead (writes
    ``<out>/sfm-bench.json``); ``--matchers`` / ``--mappers`` pick the grid.
    """
    from reconstruction import SFM_CHOICES, require_offsite_source
    from reconstruction.sfm import MATCHER_CHOICES

    require_offsite_source(source)
    if sfm not in SFM_CHOICES:
        raise SystemExit(f"--sfm must be one of {SFM_CHOICES}, got {sfm!r}")
    if matcher not in MATCHER_CHOICES:
        raise SystemExit(f"--matcher must be one of {MATCHER_CHOICES}, got {matcher!r}")
    payload = _tar_images(images, source)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if bench:
        result = sfm_bench.remote(payload, source, matchers, mappers)
        (out_dir / "sfm-bench.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return

    sheet, splat_bytes, mesh_bytes, preview = reconstruct.remote(
        payload, scan_id, source, rate, sfm, matcher, gpu_features
    )
    (out_dir / f"{scan_id}.{sheet['format']}").write_bytes(splat_bytes)
    (out_dir / f"{scan_id}.obj").write_bytes(mesh_bytes)
    if preview:
        (out_dir / f"{scan_id}-eval-view.jpg").write_bytes(preview)
    (out_dir / "cost.json").write_text(json.dumps(sheet, indent=2) + "\n")
    print(json.dumps(sheet, indent=2))
