"""Environment-package format + reference validator (M1-GAME-01 loader prep / M4-PLAT-01).

An environment package is the bundle the Unity runtime loads (M1-GAME-01): the
``environment_spec.json`` manifest plus the assets it names — the splat, the collision
mesh, the scene graph, the traversal graph and a thumbnail. ``environment_spec.json`` is
the fixed entry point; every other file is referenced by the package-relative name in its
``assets`` block (never a URL, bucket path or user id — SPEC §3.9, AUTH #034).

This module is the **reference** the C# loader conforms to: ``validate`` performs the same
parse + checks the loader must (manifest schema, the two graph docs schema-valid, the
binary assets present, and the three documents cross-consistent via the frozen
``check_consistency`` checker). ``assemble`` writes a package from a triple + assets.

Pure standard library + jsonschema (already a dev/test dep). No Unity or C# here — the
runtime loader + rendering (beacon / route markers / vistas, DESIGN_SYSTEM §1) is
gj-gameplay's; see CONTRACT.md for the load order and placement rules it implements.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

_ENV = Path(__file__).resolve().parents[2] / "data" / "schemas" / "environment"
MANIFEST = "environment_spec.json"
_DOC_ASSETS = ("scene_graph", "traversal_graph")
_BINARY_ASSETS = ("splat", "collision_mesh", "thumbnail")


class PackageError(ValueError):
    """Raised when a package cannot be assembled or read."""


def _schema(kind: str) -> dict:
    return json.loads((_ENV / f"{kind}.json").read_text(encoding="utf-8"))


def _schema_errors(kind: str, doc: dict) -> list[str]:
    errs = sorted(Draft202012Validator(_schema(kind)).iter_errors(doc), key=str)
    return [f"{kind}: {e.message}" for e in errs]


def _check_consistency():
    path = _ENV / "check_consistency.py"
    spec = importlib.util.spec_from_file_location("gj_check_consistency", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assemble(
    scene: dict,
    graph: dict,
    spec: dict,
    assets: dict[str, bytes],
    out_dir: Path,
) -> Path:
    """Write a package into ``out_dir`` using the filenames ``spec['assets']`` declares.

    ``assets`` supplies the raw bytes for the binary assets (keys splat / collision_mesh /
    thumbnail). The scene graph and traversal graph are written from ``scene`` / ``graph``.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = spec["assets"]
    (out_dir / MANIFEST).write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    (out_dir / names["scene_graph"]).write_text(
        json.dumps(scene, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / names["traversal_graph"]).write_text(
        json.dumps(graph, indent=2) + "\n", encoding="utf-8"
    )
    for field in _BINARY_ASSETS:
        if field not in assets:
            raise PackageError(f"assemble: missing bytes for '{field}'")
        (out_dir / names[field]).write_bytes(assets[field])
    return out_dir


def validate(pkg_dir: Path) -> list[str]:
    """Return a list of problems with the package at ``pkg_dir`` (empty = loadable).

    The same checks the C# loader runs before it trusts a package: the manifest is present
    and schema-valid; the scene + traversal graphs load from the names it declares and are
    schema-valid; the binary assets exist under their declared names; and the three
    documents are cross-consistent (ids, scale, capture mode, movement hash, routes).
    """
    pkg_dir = Path(pkg_dir)
    manifest = pkg_dir / MANIFEST
    if not manifest.exists():
        return [f"missing {MANIFEST} (package manifest)"]
    try:
        spec = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{MANIFEST}: invalid JSON ({exc})"]

    problems = _schema_errors("environment_spec", spec)
    assets = spec.get("assets", {}) if isinstance(spec, dict) else {}

    docs: dict[str, dict | None] = {"scene_graph": None, "traversal_graph": None}
    for field in _DOC_ASSETS:
        name = assets.get(field)
        path = pkg_dir / name if name else None
        if not name or not path.exists():
            problems.append(f"missing {field} asset '{name}'")
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{field} '{name}': invalid JSON ({exc})")
            continue
        problems += _schema_errors(field, doc)
        docs[field] = doc

    for field in _BINARY_ASSETS:
        name = assets.get(field)
        if not name or not (pkg_dir / name).exists():
            problems.append(f"missing {field} asset '{name}'")

    scene, graph = docs["scene_graph"], docs["traversal_graph"]
    if scene is not None and graph is not None and not problems:
        cc = _check_consistency()
        problems += [f"consistency: {p}" for p in cc.check(scene, graph, spec)]
    return problems


def assemble_from_files(
    scene_path: Path,
    graph_path: Path,
    spec_path: Path,
    splat: Path,
    collision_mesh: Path,
    thumbnail: Path,
    out_dir: Path,
) -> Path:
    def _load(p: Path) -> dict:
        return json.loads(Path(p).read_text(encoding="utf-8"))

    assets = {
        "splat": Path(splat).read_bytes(),
        "collision_mesh": Path(collision_mesh).read_bytes(),
        "thumbnail": Path(thumbnail).read_bytes(),
    }
    return assemble(_load(scene_path), _load(graph_path), _load(spec_path), assets, out_dir)
