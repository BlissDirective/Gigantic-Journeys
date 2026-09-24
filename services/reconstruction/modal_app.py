"""Modal entrypoint for the reconstruction spike (M1-CAPT-03).

Runs our container pipeline on a scale-to-zero Modal GPU. The Operator supplies a
Modal token (MODAL_TOKEN_ID / MODAL_TOKEN_SECRET in the VM .env.local) and runs,
from the repo root:

    modal run services/reconstruction/modal_app.py \
        --images ./data/mipnerf360/room/images_4 --scan-id smoke \
        --source public --sfm colmap --rate 1.10

The image is built from services/reconstruction/Dockerfile, so the COLMAP + gsplat +
Open3D stack matches the pinned container. The build context is pinned to this
directory (``context_dir``): Modal uploads only the Dockerfile COPY sources found
under it (``reconstruction/``), so nothing elsewhere in the repo (``.env.local``,
``.secrets-local/``) can enter the image build.

Only ``public`` and ``corpus`` sources may run here; ``user`` scans are rejected
locally before upload and again in the container (ADR-0005 / AUTH #030).

Spend: the Modal workspace budget / spend limit (Owner) is the real cumulative cap.
The in-pipeline guard (AUTH #031 $100 / $50-per-day) starts from a fresh ledger on
every run, so it only stops a single run whose estimate would cross a cap.
"""

from __future__ import annotations

import io
import json
import os
import tarfile
from pathlib import Path

import modal

_HERE = Path(__file__).parent
image = modal.Image.from_dockerfile((_HERE / "Dockerfile").as_posix(), context_dir=_HERE)
app = modal.App("gj-recon-spike", image=image)


@app.function(gpu="A10G", timeout=3600)
def reconstruct(
    images_tar: bytes,
    scan_id: str,
    source: str,
    rate_per_hour_usd: float,
    sfm: str = "colmap",
) -> tuple[dict, bytes, bytes]:
    """Run SfM -> train -> compress -> mesh in-container; return (cost sheet, splat, mesh)."""
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
    from reconstruction.spike import cost_sheet

    scan_source = require_offsite_source(source)  # defence in depth: never a user scan
    # The image's COLMAP is the Ubuntu apt build (no CUDA): SIFT must run on CPU.
    # Set GJ_COLMAP_CUDA=1 in the Dockerfile once a CUDA-enabled COLMAP is used.
    sfm_adapter = select_sfm(sfm, use_gpu=os.environ.get("GJ_COLMAP_CUDA") == "1")

    work = Path(tempfile.mkdtemp())
    images = work / "images"
    images.mkdir()
    with tarfile.open(fileobj=io.BytesIO(images_tar)) as tar:
        tar.extractall(images, filter="data")  # noqa: S202 - archive is authored locally below

    image_count = sum(1 for p in images.iterdir() if p.is_file())
    scan = ScanInput(
        scan_id=scan_id,
        image_dir=images,
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
    )
    return (
        cost_sheet(run),
        run.package.splat.path.read_bytes(),
        run.package.mesh.path.read_bytes(),
    )


@app.local_entrypoint()
def main(
    images: str,
    scan_id: str = "spike",
    source: str = "public",
    sfm: str = "colmap",
    rate: float = 1.10,
    out: str = "./out",
) -> None:
    """Tar a local image dir, run the pipeline on Modal, save the outputs + cost sheet."""
    # Local import: modal puts this file's directory on sys.path. Validate before
    # any upload so a user scan never leaves the machine.
    from reconstruction import SFM_CHOICES, require_offsite_source

    require_offsite_source(source)
    if sfm not in SFM_CHOICES:
        raise SystemExit(f"--sfm must be one of {SFM_CHOICES}, got {sfm!r}")
    src = Path(images)
    if not src.is_dir():
        raise SystemExit(f"--images {images!r} is not a directory")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for p in sorted(src.iterdir()):
            if p.is_file():
                tar.add(p, arcname=p.name)

    sheet, splat_bytes, mesh_bytes = reconstruct.remote(buf.getvalue(), scan_id, source, rate, sfm)

    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{scan_id}.{sheet['format']}").write_bytes(splat_bytes)
    (out_dir / f"{scan_id}.obj").write_bytes(mesh_bytes)
    (out_dir / "cost.json").write_text(json.dumps(sheet, indent=2) + "\n")
    print(json.dumps(sheet, indent=2))
