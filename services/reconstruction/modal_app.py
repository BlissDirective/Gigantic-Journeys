"""Modal entrypoint for the reconstruction spike (M1-CAPT-03).

Runs our container pipeline on a scale-to-zero Modal GPU. The Operator supplies a
Modal token (MODAL_TOKEN_ID / MODAL_TOKEN_SECRET in the VM .env.local) and runs,
from the repo root:

    modal run services/reconstruction/modal_app.py --images ./data/room1/images --scan-id room1

The image is built from services/reconstruction/Dockerfile, so the COLMAP/GLOMAP +
gsplat + Open3D stack matches the pinned container. Corpus-only data; spend is
capped by the Modal dashboard limit (Owner) and the in-pipeline $100 cap (AUTH #031).

Verify against modal.com/docs for your installed Modal version: the Dockerfile
build context (Modal uses the Dockerfile's directory by default, which is where our
`reconstruction/` package lives, so the Dockerfile COPY resolves) and the GPU name.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import modal

_HERE = Path(__file__).parent
image = modal.Image.from_dockerfile((_HERE / "Dockerfile").as_posix())
app = modal.App("gj-recon-spike", image=image)


@app.function(gpu="A10G", timeout=3600)
def reconstruct(
    images_tar: bytes, scan_id: str, source: str, rate_per_hour_usd: float
) -> tuple[dict, bytes, bytes]:
    """Run SfM -> train -> compress -> mesh in-container; return (cost sheet, splat, mesh)."""
    import tempfile

    from reconstruction import (
        CostLedger,
        GlomapSfM,
        GsplatTrainer,
        Open3DMesher,
        ReconstructionConfig,
        ScanInput,
        Source,
        SplatTransformCompressor,
        run_pipeline,
    )
    from reconstruction.spike import cost_sheet

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
        source=Source(source),
    )
    run = run_pipeline(
        scan,
        ReconstructionConfig(),
        sfm=GlomapSfM(),
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
    source: str = "corpus",
    rate: float = 1.0,
    out: str = "./out",
) -> None:
    """Tar a local image dir, run the pipeline on Modal, save the outputs + cost sheet."""
    src = Path(images)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for p in sorted(src.iterdir()):
            if p.is_file():
                tar.add(p, arcname=p.name)

    sheet, splat_bytes, mesh_bytes = reconstruct.remote(buf.getvalue(), scan_id, source, rate)

    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{scan_id}.{sheet['format']}").write_bytes(splat_bytes)
    (out_dir / f"{scan_id}.obj").write_bytes(mesh_bytes)
    (out_dir / "cost.json").write_text(json.dumps(sheet, indent=2) + "\n")
    print(json.dumps(sheet, indent=2))
