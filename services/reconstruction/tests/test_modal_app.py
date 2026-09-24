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


def test_build_context_is_pinned_to_the_service_dir():
    tree = ast.parse(MODAL_APP.read_text(encoding="utf-8"))
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "from_dockerfile"
    ]
    assert len(calls) == 1
    assert "context_dir" in {k.arg for k in calls[0].keywords}
