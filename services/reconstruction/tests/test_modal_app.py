"""Static checks on modal_app.py (modal itself is not installed in CI)."""

import ast
import pathlib

MODAL_APP = pathlib.Path(__file__).resolve().parents[1] / "modal_app.py"


def _functions() -> dict[str, ast.FunctionDef]:
    tree = ast.parse(MODAL_APP.read_text(encoding="utf-8"))
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _calls(fn: ast.FunctionDef) -> set[str]:
    return {
        n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }


def test_user_scans_are_rejected_locally_and_in_the_container():
    fns = _functions()
    assert "require_offsite_source" in _calls(fns["main"])
    assert "require_offsite_source" in _calls(fns["reconstruct"])


def _attr_calls(name: str) -> list[ast.Call]:
    tree = ast.parse(MODAL_APP.read_text(encoding="utf-8"))
    return [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == name
    ]


def test_build_context_is_pinned_to_the_service_dir():
    calls = _attr_calls("dockerfile_commands")
    assert len(calls) == 1
    assert "context_dir" in {k.arg for k in calls[0].keywords}
    # The package is mounted from the service dir only, never the repo root.
    mounts = _attr_calls("add_local_dir")
    assert len(mounts) == 1
    assert ast.unparse(mounts[0].args[0]) == "_HERE / 'reconstruction'"


def _dockerfile_layers():
    """Load modal_app.dockerfile_layers without importing modal (absent in CI)."""
    tree = ast.parse(MODAL_APP.read_text(encoding="utf-8"))
    keep = [
        n
        for n in tree.body
        if (isinstance(n, ast.FunctionDef) and n.name == "dockerfile_layers")
        or (
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in {"_LAYER", "_SKIP"} for t in n.targets)
        )
    ]
    ns: dict = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(MODAL_APP), "exec"), ns)  # noqa: S102
    return ns["dockerfile_layers"]


def test_dockerfile_splits_into_cached_layers():
    text = (MODAL_APP.parent / "Dockerfile").read_text(encoding="utf-8")
    layers = _dockerfile_layers()(text)
    assert layers[0][0].startswith("FROM nvidia/cuda:")
    assert len(layers) >= 4  # base, torch, gsplat, nerfstudio, colmap
    flat = [line for layer in layers for line in layer]
    # Nothing is COPY'd into the Modal image (code is mounted at start) and
    # comments never reach the layer hash.
    assert not any(line.startswith(("COPY", "ADD")) for line in flat)
    assert not any(line.lstrip().startswith("#") for line in flat)
    # The slow gsplat compile comes before the COLMAP layer, so a COLMAP bump
    # never rebuilds it.
    gsplat = next(i for i, layer in enumerate(layers) if any("gsplat.git" in x for x in layer))
    colmap = next(i for i, layer in enumerate(layers) if any("colmap=" in x for x in layer))
    assert gsplat < colmap


def test_dockerfile_layers_parser():
    parse = _dockerfile_layers()
    text = "# header\n# modal-layer: a\nFROM x\n# c\nRUN a \\\n  b\n\n"
    text += "# modal-layer: b\nRUN c\n# modal-skip\nCOPY . .\n"
    assert parse(text) == [["FROM x", "RUN a \\", "  b"], ["RUN c"]]
