"""Static checks on the Modal intake app and the Operator CLI (modal is not installed in CI)."""

from __future__ import annotations

import ast
import pathlib

import pytest

SERVICE = pathlib.Path(__file__).resolve().parents[1]
APP = SERVICE / "corpus_intake_app.py"
SRC = APP.read_text(encoding="utf-8")
TREE = ast.parse(SRC)


def _attr_calls(name):
    return [
        n
        for n in ast.walk(TREE)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == name
    ]


def test_only_the_tools_package_is_mounted():
    mounts = _attr_calls("add_local_dir")
    assert mounts, "images must mount tools/"
    for call in mounts:
        src = ast.unparse(call.args[0])
        assert src == "_HERE / 'tools'", src  # never the repo root (.env.local, .secrets-local/)


def test_storage_is_the_private_modal_volume():
    assert 'VOLUME_NAME = "gj-corpus"' in SRC
    assert "supabase" not in SRC.lower()  # the Free-plan staging bucket caps objects at 50 MB


def test_web_endpoint_runs_one_container_and_needs_the_signing_secret():
    web = next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == "web")
    deco = ast.unparse(web.decorator_list[0])
    assert "max_containers=1" in deco and "secrets=[secret]" in deco
    assert (
        "requires_proxy_auth" not in deco
    )  # the page must open in phone Safari; the link is the auth


def test_raw_upload_is_deleted_after_the_clean_copy_is_stored():
    proc = next(
        n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == "process_inbox"
    )
    body = ast.unparse(proc)
    assert body.index("strip_file") < body.index("shutil.move") < body.rindex("shutil.rmtree(d)")
    assert "STALE_DAYS" in body  # unfinished uploads are purged (SECURITY_CHECKLIST §6.1)


def test_cli_refuses_to_write_media_inside_the_repo(tmp_path):
    pytest.importorskip("jsonschema")
    from tools import corpus_intake

    assert corpus_intake._inside_repo(SERVICE / "corpus")
    assert not corpus_intake._inside_repo(tmp_path)
    with pytest.raises(SystemExit, match="inside the git checkout"):
        corpus_intake.main(["fetch", "room-01", "--out", str(SERVICE / "corpus")])
