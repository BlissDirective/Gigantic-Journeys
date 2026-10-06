"""Batch runner for the audio-source recipe (M1-GAME-04, AUTH #048) -- vendor-agnostic.

Walks the ``sources`` manifest, asks an ``AudioProvider`` to generate each clip family, saves the
clips, and applies the recipe's ffmpeg post-process. It **defaults to a dry run** (plans, spends
nothing, needs no API key); a real run needs ``--execute`` and spends on the provider's account, so
``--limit`` caps the number of API calls. Generated audio is written outside the tracked tree
(``services/audio/_generated/`` is git-ignored) -- clips are never committed; provenance goes in
``qa/audio-sources.md`` and the files are wired into Unity by gj-gameplay.

    # plan only ($0):          python services/audio/generate_audio.py
    # smoke (one real family): python services/audio/generate_audio.py --execute --event walk
    # a capped batch:          python services/audio/generate_audio.py --execute --limit 50

Standard library only.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import sources
from sources import AudioProvider, GenerationSpec

_REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = _REPO / "services" / "audio" / "_generated"


def estimate(specs: list[GenerationSpec] | None = None) -> dict:
    """Rough cost signal: clip families and total provider calls the full manifest would make."""
    specs = specs if specs is not None else sources.build_manifest()
    families = 0
    calls = 0
    for s in specs:
        n_variants = len(s.materials) if s.materials else 1
        families += n_variants
        calls += n_variants * s.count
    return {"families": families, "calls": calls, "events": len(specs)}


def _ext(output_format: str) -> str:
    if output_format.startswith("mp3"):
        return ".mp3"
    if output_format.startswith("pcm") or output_format.startswith("ulaw"):
        return ".wav"
    if output_format.startswith("opus"):
        return ".opus"
    return ".bin"


def postprocess_file(raw: Path, final: Path, pp: sources.PostProcess) -> Path:
    """Apply the recipe's ffmpeg filter chain raw -> final. If the clip is left raw or ffmpeg is
    missing, just move raw to final. Returns the final path."""
    filters = sources.ffmpeg_filters(pp)
    if not filters or shutil.which("ffmpeg") is None:
        raw.replace(final)
        return final
    cmd = ["ffmpeg", "-y", "-i", str(raw), "-af", ",".join(filters), str(final)]
    subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603 (fixed argv, no shell)
    raw.unlink(missing_ok=True)
    return final


def run(
    provider: AudioProvider,
    out_dir: Path | str = DEFAULT_OUT,
    *,
    specs: list[GenerationSpec] | None = None,
    limit: int | None = None,
    dry_run: bool = True,
    postprocess: bool = True,
    event: str | None = None,
    material: str | None = None,
) -> dict:
    """Generate (or, in a dry run, just plan) the manifest. Returns a summary dict."""
    specs = specs if specs is not None else sources.build_manifest()
    out = Path(out_dir)
    ext = _ext(getattr(provider, "output_format", "mp3"))
    planned: list[str] = []
    written: list[str] = []
    failed: list[dict] = []
    calls = 0

    for spec in specs:
        if event is not None and spec.event != event:
            continue
        for req in spec.expand():
            if material is not None and req.material != material:
                continue
            planned.append(req.id)
            if dry_run:
                continue
            if limit is not None and calls >= limit:
                return _summary(planned, written, failed, calls, dry_run, stopped=True)
            clips = None
            for attempt in (1, 2):  # one retry so a transient blip doesn't lose the whole batch
                try:
                    clips = provider.generate(req)  # spends on the provider's account
                    break
                except Exception as exc:  # record + continue; a single family never aborts the run
                    if attempt == 2:
                        failed.append({"id": req.id, "error": str(exc)[:200]})
            if clips is None:
                continue
            calls += req.count
            dest_dir = out / req.event
            dest_dir.mkdir(parents=True, exist_ok=True)
            for i, data in enumerate(clips):
                raw = dest_dir / f"{req.id}__{i}.raw{ext}"
                raw.write_bytes(data)
                final = dest_dir / f"{req.id}__{i}{ext}"
                if postprocess:
                    final = postprocess_file(raw, final, req.post_process)
                else:
                    raw.replace(final)
                written.append(str(final))
    return _summary(planned, written, failed, calls, dry_run, stopped=False)


def _summary(planned, written, failed, calls, dry_run, *, stopped) -> dict:
    return {
        "dry_run": dry_run,
        "planned_families": len(planned),
        "written_files": len(written),
        "failed_families": len(failed),
        "failures": failed[:20],
        "provider_calls": calls,
        "stopped_at_limit": stopped,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate GJ audio clips from the sound-bank recipe.")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument(
        "--execute", action="store_true", help="actually generate (spends); default is a dry run"
    )
    ap.add_argument("--limit", type=int, default=None, help="max provider calls (cost guard)")
    ap.add_argument("--event", default=None, help="only this bank event")
    ap.add_argument("--material", default=None, help="only this material")
    ap.add_argument("--no-postprocess", action="store_true")
    ap.add_argument("--provider", choices=["dry-run", "elevenlabs"], default="elevenlabs")
    args = ap.parse_args()
    event = args.event or None  # a CI input of "" means "all events", not an impossible filter
    material = args.material or None

    est = estimate()
    print(
        f"manifest: {est['events']} events, {est['families']} clip families, ~{est['calls']} calls"
    )

    if not args.execute:
        res = run(
            sources.DryRunProvider(),
            args.out,
            dry_run=True,
            event=event,
            material=material,
        )
        print(f"DRY RUN (no spend): {res['planned_families']} families planned; pass --execute.")
        return 0

    if args.provider == "elevenlabs":
        from elevenlabs_provider import ElevenLabsProvider

        provider: AudioProvider = ElevenLabsProvider()
    else:
        provider = sources.DryRunProvider()
    res = run(
        provider,
        args.out,
        limit=args.limit,
        dry_run=False,
        postprocess=not args.no_postprocess,
        event=event,
        material=material,
    )
    print(f"generated: {res}")
    if res["failed_families"]:
        print(f"::warning::{res['failed_families']} families failed: {res['failures']}")
    if res["written_files"] == 0 and res["planned_families"] > 0:
        print("::error::nothing was generated (check ELEVENLABS_API_KEY and the provider)")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - manual runner
    raise SystemExit(main())
