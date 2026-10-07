"""Static checks on mapanything_ab_app.py (modal / torch are not installed in CI)."""

import ast
import pathlib

from reconstruction import mapanything_frontend as maf

APP = pathlib.Path(__file__).resolve().parents[1] / "mapanything_ab_app.py"
TREE = ast.parse(APP.read_text(encoding="utf-8"))
FNS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}


def _constants() -> dict:
    out = {}
    for node in TREE.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = node.value.value
    return out


def test_pins_match_the_reviewed_adapter():
    c = _constants()
    assert c["MAPANYTHING_CODE_COMMIT"] == maf.MAPANYTHING_CODE_COMMIT
    assert c["MAPANYTHING_REVISION"] == maf.MAPANYTHING_REVISION
    src = APP.read_text(encoding="utf-8")
    assert "facebook/map-anything-apache" in src
    assert "'facebook/map-anything'" not in src and '"facebook/map-anything"' not in src


def test_gpu_spend_needs_explicit_go():
    main = FNS["main"]
    args = [a.arg for a in main.args.args]
    defaults = dict(zip(args[-len(main.args.defaults) :], main.args.defaults, strict=True))
    assert isinstance(defaults["gpu_go"], ast.Constant) and defaults["gpu_go"].value is False
    body = main.body
    guard = next(
        i
        for i, n in enumerate(body)
        if isinstance(n, ast.If)
        and isinstance(n.test, ast.UnaryOp)
        and n.test.operand.id == "gpu_go"
    )
    remote = next(
        i for i, n in enumerate(body) if "starmap" in ast.dump(n) or ".remote" in ast.dump(n)
    )
    assert guard < remote
    assert any(isinstance(n, ast.Return) for n in body[guard].body)


def test_frontend_ab_validates_ids_and_deletes_artifacts():
    fn = FNS["frontend_ab"]
    calls = {
        n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "_check_clip_id" in calls
    tries = [n for n in ast.walk(fn) if isinstance(n, ast.Try)]
    assert any("rmtree" in ast.dump(stmt) for t in tries for stmt in t.finalbody)
    assert "internal_eval=True" in ast.unparse(fn)
