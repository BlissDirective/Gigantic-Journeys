"""The Owner upload page (tools/intake_web.py): signed links, append-only chunked uploads."""

from __future__ import annotations

import asyncio
import json

import pytest
from tools import intake_web as iw

KEY = b"k" * 48
NOW = 1_800_000_000.0


def call(app, method, path, query="", body=b"", token=None, chunks=None):
    """Drive the ASGI app once; returns (status, headers, body-bytes)."""
    headers = [(b"x-upload-token", token.encode())] if token else []
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query.encode(),
        "headers": headers,
    }
    parts = chunks if chunks is not None else [body]
    msgs = [
        {"type": "http.request", "body": p, "more_body": i < len(parts) - 1}
        for i, p in enumerate(parts)
    ]
    sent = []

    async def receive():
        return msgs.pop(0) if msgs else {"type": "http.disconnect"}

    async def send(m):
        sent.append(m)

    asyncio.run(app(scope, receive, send))
    start = sent[0]
    return start["status"], dict(start["headers"]), b"".join(m.get("body", b"") for m in sent[1:])


@pytest.fixture
def app(tmp_path):
    commits = []
    a = iw.IntakeApp(tmp_path, KEY, on_change=lambda: commits.append(1), clock=lambda: NOW)
    a.commits = commits
    return a


@pytest.fixture
def token():
    return iw.make_token(KEY, 72, now=NOW)


def meta(**over):
    m = {
        "name": "IMG_0001.MOV",
        "size": 10,
        "mode": "room",
        "lighting": "bright-daylight",
        "privacy_ok": True,
        "objects": {"couch": True, "bookshelf": True},
        "note": "",
    }
    m.update(over)
    return json.dumps(m).encode()


# ---------------------------------------------------------------- links
def test_token_roundtrip_expiry_and_tamper():
    t = iw.make_token(KEY, 1, now=NOW)
    assert iw.check_token(KEY, t, now=NOW) == int(NOW + 3600)
    assert iw.check_token(KEY, t, now=NOW + 3601) is None  # expired
    assert iw.check_token(b"x" * 48, t, now=NOW) is None  # wrong key
    body, sig = t.split(".")
    assert iw.check_token(KEY, body + "." + sig[::-1], now=NOW) is None
    assert iw.check_token(KEY, None) is None and iw.check_token(KEY, "a.b.c") is None


def test_link_lifetime_and_key_are_bounded():
    with pytest.raises(ValueError):
        iw.make_token(KEY, iw.MAX_LINK_HOURS + 1)
    with pytest.raises(ValueError):
        iw.make_token(b"short", 1)


# ---------------------------------------------------------------- routes
def test_everything_is_403_without_a_valid_link(app):
    status, headers, body = call(app, "GET", "/")
    assert status == 403 and b"expired" in body
    for method, path in [("GET", "/api/check"), ("POST", "/api/start"), ("PUT", "/api/chunk")]:
        assert call(app, method, path)[0] == 403
    expired = iw.make_token(KEY, 1, now=NOW - 7200)
    assert call(app, "GET", "/", token=expired)[0] == 403


def test_page_served_with_link_in_query_and_hardened_headers(app, token):
    status, headers, body = call(app, "GET", "/", query=f"t={token}")
    assert status == 200 and b"Send your scans" in body
    assert headers[b"cache-control"] == b"no-store"
    assert headers[b"referrer-policy"] == b"no-referrer"
    assert b"default-src 'none'" in headers[b"content-security-policy"]
    # The page asks for the Bible §1 classes, the Lego flag, lighting and the privacy check.
    for word in (b"Couch", b"Coffee table", b"Dining chair", b"Bookshelf", b"Lego", b"No faces"):
        assert word in body


def test_full_chunked_upload_lands_in_inbox(app, token, tmp_path):
    status, _, body = call(app, "POST", "/api/start", body=meta(size=10), token=token)
    assert status == 200
    upload_id = json.loads(body)["id"]
    assert iw.UPLOAD_ID.match(upload_id)
    assert call(app, "PUT", "/api/chunk", f"id={upload_id}&offset=0", b"01234", token)[0] == 200
    # a retried chunk at a stale offset is refused with the true offset (append-only)
    status, _, body = call(app, "PUT", "/api/chunk", f"id={upload_id}&offset=0", b"xxxxx", token)
    assert status == 409 and json.loads(body)["received"] == 5
    status, _, body = call(
        app, "PUT", "/api/chunk", f"id={upload_id}&offset=5", token=token, chunks=[b"56", b"789"]
    )
    assert status == 200 and json.loads(body)["received"] == 10
    assert call(app, "POST", "/api/finish", f"id={upload_id}", token=token)[0] == 200
    d = tmp_path / upload_id
    assert (d / "upload.mov").read_bytes() == b"0123456789"
    assert not (d / "upload.part").exists()
    saved = json.loads((d / "owner.json").read_text())
    assert saved["mode"] == "room" and saved["objects"]["couch"] is True
    assert saved["objects"]["lego"] is False and saved["privacy_ok"] is True
    assert "completed_at" in saved
    assert len(app.commits) >= 4  # start, two chunks, finish each persisted


def test_finish_refused_until_every_byte_arrived(app, token):
    upload_id = json.loads(call(app, "POST", "/api/start", body=meta(size=10), token=token)[2])[
        "id"
    ]
    call(app, "PUT", "/api/chunk", f"id={upload_id}&offset=0", b"0123", token)
    status, _, body = call(app, "POST", "/api/finish", f"id={upload_id}", token=token)
    assert status == 409 and json.loads(body)["received"] == 4
    status, _, body = call(app, "GET", "/api/status", f"id={upload_id}", token=token)
    assert json.loads(body)["received"] == 4


def test_oversize_chunk_is_rejected_and_rolled_back(app, token, tmp_path):
    upload_id = json.loads(call(app, "POST", "/api/start", body=meta(size=4), token=token)[2])["id"]
    status, _, _ = call(app, "PUT", "/api/chunk", f"id={upload_id}&offset=0", b"0123456", token)
    assert status == 400
    assert (tmp_path / upload_id / "upload.part").stat().st_size == 0


@pytest.mark.parametrize(
    "bad",
    [
        {"name": "notes.txt"},
        {"name": "x.zip"},
        {"size": 0},
        {"size": iw.MAX_FILE_BYTES + 1},
        {"mode": "outdoor"},
        {"lighting": "night"},
        {"privacy_ok": False},
    ],
)
def test_start_validates_the_form(app, token, bad):
    status, _, body = call(app, "POST", "/api/start", body=meta(**bad), token=token)
    assert status == 400 and json.loads(body)["error"]


@pytest.mark.parametrize("upload_id", ["../../etc", "x", "20260927T000000-zzzzzzzz", ""])
def test_upload_ids_cannot_escape_the_inbox(app, token, upload_id):
    assert call(app, "PUT", "/api/chunk", f"id={upload_id}&offset=0", b"x", token)[0] == 400


def test_there_is_no_download_or_listing_route(app, token):
    for path in ("/api/list", "/api/download", "/inbox", "/api/files"):
        assert call(app, "GET", path, token=token)[0] in (400, 404)


def test_async_commit_hook_is_awaited(tmp_path, token):
    seen = []

    async def commit():
        seen.append(1)

    a = iw.IntakeApp(tmp_path, KEY, on_change=commit, clock=lambda: NOW)
    assert call(a, "POST", "/api/start", body=meta(), token=token)[0] == 200
    assert seen == [1]
