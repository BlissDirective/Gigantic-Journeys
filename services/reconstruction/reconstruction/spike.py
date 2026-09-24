"""Spike driver: run the reconstruction pipeline end to end from the CLI.

Real mode wires the container adapters (COLMAP/GLOMAP + gsplat/Brush + Open3D)
and enforces the spend cap; ``--dry-run`` uses the no-GPU fakes so the whole
flow is exercised on any machine (and in CI). Writes a JSON cost sheet for the
spike report (M1-CAPT-03).

Examples:
    # CPU dry run (no GPU) — proves the wiring end to end
    python -m reconstruction.spike --images ./imgs --scan-id room1 --dry-run

    # Real run on the GPU box, held under the AUTH #031 spike cap
    python -m reconstruction.spike --images ./imgs --scan-id room1 \\
        --trainer gsplat --sfm glomap --rate 1.0
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from .compress import Compressor, SplatTransformCompressor
from .cost import CostLedger
from .fakes import FakeCompressor, FakeMesher, FakeSfM, FakeTrainer
from .mesh import Mesher, Open3DMesher
from .models import Format, ReconstructionConfig, ScanInput, Source
from .pipeline import ReconstructionRun, run_pipeline
from .sfm import ColmapSfM, GlomapSfM, SfM
from .trainer import BrushTrainer, GsplatTrainer, Trainer

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def count_images(image_dir: Path) -> int:
    """Count image files in a capture dir (0 if the dir is absent/empty)."""
    if not image_dir.is_dir():
        return 0
    return sum(1 for p in image_dir.iterdir() if p.suffix.lower() in _IMAGE_EXTS)


def build_adapters(trainer_name: str, sfm_name: str) -> tuple[SfM, Trainer, Compressor, Mesher]:
    """Real container adapters."""
    sfm: SfM = GlomapSfM() if sfm_name == "glomap" else ColmapSfM()
    trainer: Trainer = GsplatTrainer() if trainer_name == "gsplat" else BrushTrainer()
    return sfm, trainer, SplatTransformCompressor(), Open3DMesher()


def build_fake_adapters() -> tuple[SfM, Trainer, Compressor, Mesher]:
    """No-GPU fakes for a dry run."""
    return FakeSfM(), FakeTrainer(), FakeCompressor(), FakeMesher()


def cost_sheet(run: ReconstructionRun) -> dict:
    """A one-scan record for the spike report's cost table."""
    pkg = run.package
    return {
        "scan_id": pkg.scan_id,
        "splat_count": pkg.splat.splat_count,
        "format": pkg.splat.fmt.value,
        "package_bytes": pkg.total_size_bytes,
        "within_budget": run.within_budget,
        "gpu_seconds": round(run.cost.gpu_seconds, 2),
        "rate_per_hour_usd": run.cost.rate_per_hour_usd,
        "usd": round(run.cost.usd, 4),
        "day": run.cost.day.isoformat(),
    }


def run_spike(args: argparse.Namespace) -> ReconstructionRun:
    """Build the config + adapters from parsed args and run the pipeline."""
    image_dir = Path(args.images)
    image_count = args.image_count or count_images(image_dir) or 1
    config = ReconstructionConfig(
        splat_budget=args.splat_budget,
        compress_format=Format(args.format),
        sfm=args.sfm,
    )
    scan = ScanInput(
        scan_id=args.scan_id,
        image_dir=image_dir,
        image_count=image_count,
        source=Source(args.source),
    )
    if args.dry_run:
        sfm, trainer, compressor, mesher = build_fake_adapters()
    else:
        sfm, trainer, compressor, mesher = build_adapters(args.trainer, args.sfm)
    return run_pipeline(
        scan,
        config,
        sfm=sfm,
        trainer=trainer,
        compressor=compressor,
        mesher=mesher,
        work_dir=Path(args.work_dir),
        ledger=CostLedger(),
        gpu_rate_per_hour_usd=args.rate,
        day=dt.date.today(),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reconstruction.spike", description=__doc__)
    parser.add_argument("--images", required=True, help="capture image directory")
    parser.add_argument("--scan-id", default="spike")
    parser.add_argument("--source", default="corpus", choices=[s.value for s in Source])
    parser.add_argument("--work-dir", default="./work")
    parser.add_argument("--cost-sheet", default=None, help="cost-sheet JSON path")
    parser.add_argument("--trainer", default="gsplat", choices=["gsplat", "brush"])
    parser.add_argument("--sfm", default="glomap", choices=["glomap", "colmap"])
    parser.add_argument("--format", default="spz", choices=[f.value for f in Format])
    parser.add_argument("--splat-budget", type=int, default=2_000_000)
    parser.add_argument("--rate", type=float, default=1.0, help="GPU $/hr for costing")
    parser.add_argument("--image-count", type=int, default=0, help="0 = auto-count")
    parser.add_argument("--dry-run", action="store_true", help="use no-GPU fakes")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run = run_spike(args)
    sheet = cost_sheet(run)
    out = Path(args.cost_sheet) if args.cost_sheet else Path(args.work_dir) / "cost.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sheet, indent=2) + "\n")
    print(json.dumps(sheet, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
