"""Owner upload page for the corpus intake (M0-CAPT-01) - a dependency-free ASGI app.

Served by ``corpus_intake_app.py`` as a Modal web endpoint that writes into the
private ``gj-corpus`` Modal volume (``/inbox/<upload-id>/``). Standard library
only, so it is unit-tested in CI without Modal.

Access is a signed, expiring link (HMAC-SHA256 over the expiry with a key that
lives only in the ``gj-corpus-intake`` Modal secret). Without a valid link every
route answers 403; there is no listing and no download route, so the page can
only ever add files to the inbox. Uploads are chunked (<= 32 MiB per request) so
a 3-minute 4K video survives flaky phone connections and never hits a request
timeout; a chunk is accepted only at the exact current offset (append-only).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import inspect
import json
import re
import secrets
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from urllib.parse import parse_qs

CHUNK_BYTES = 32 * 1024 * 1024
MAX_CHUNK_BYTES = 64 * 1024 * 1024
MAX_FILE_BYTES = 4 * 1024 * 1024 * 1024  # Modal's request ceiling is per request; this is per file
MAX_LINK_HOURS = 7 * 24
ALLOWED_EXTS = {".mov", ".mp4", ".m4v", ".heic", ".heif", ".jpg", ".jpeg"}
UPLOAD_ID = re.compile(r"^[0-9]{8}T[0-9]{6}-[0-9a-f]{8}$")
MODES = {"room", "tabletop"}
LIGHTING = {"bright-daylight", "bright-artificial", "mixed", "dim"}
OBJECT_FLAGS = ("couch", "coffee_table", "dining_chair", "bookshelf", "lego")
PART = "upload.part"
META = "owner.json"


# ---------------------------------------------------------------- signed links
def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def make_token(key: bytes, hours: float, now: float | None = None) -> str:
    if not key or len(key) < 32:
        raise ValueError("signing key must be at least 32 bytes")
    if not 0 < hours <= MAX_LINK_HOURS:
        raise ValueError(f"link lifetime must be within (0, {MAX_LINK_HOURS}] hours")
    exp = int((time.time() if now is None else now) + hours * 3600)
    body = _b64(json.dumps({"exp": exp, "n": secrets.token_hex(8)}).encode())
    sig = _b64(hmac.new(key, body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def check_token(key: bytes, token: str | None, now: float | None = None) -> int | None:
    """Return the expiry (epoch s) of a valid, unexpired token, else None."""
    if not token or token.count(".") != 1 or len(token) > 256:
        return None
    body, sig = token.split(".")
    want = _b64(hmac.new(key, body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(want, sig):
        return None
    try:
        exp = int(json.loads(_unb64(body))["exp"])
    except (ValueError, KeyError, TypeError):
        return None
    t = time.time() if now is None else now
    if exp <= t or exp - t > MAX_LINK_HOURS * 3600 + 60:
        return None
    return exp


# ---------------------------------------------------------------- owner form
def clean_owner_meta(raw: object) -> dict:
    """Validate the upload form; raises ValueError with an Owner-readable message."""
    if not isinstance(raw, dict):
        raise ValueError("bad request")
    name = str(raw.get("name") or "")
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError("Only videos (.mov, .mp4) or photos (.heic, .jpg) can be uploaded.")
    size = raw.get("size")
    if not isinstance(size, int) or not 0 < size <= MAX_FILE_BYTES:
        raise ValueError("That file is empty or bigger than 4 GB.")
    mode = raw.get("mode")
    if mode not in MODES:
        raise ValueError("Pick Room or Tabletop.")
    lighting = raw.get("lighting")
    if lighting not in LIGHTING:
        raise ValueError("Pick the lighting.")
    if raw.get("privacy_ok") is not True:
        raise ValueError("Please confirm there are no faces, documents, screens or addresses.")
    objects_in = raw.get("objects") or {}
    if not isinstance(objects_in, dict):
        raise ValueError("bad request")
    objects = {k: bool(objects_in.get(k, False)) for k in OBJECT_FLAGS}
    note = str(raw.get("note") or "")[:300]
    return {
        "ext": ext,
        "size": size,
        "mode": mode,
        "lighting": lighting,
        "objects": objects,
        "privacy_ok": True,
        "note": note,
    }


# ---------------------------------------------------------------- ASGI app
Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]


class IntakeApp:
    """ASGI app. ``root`` is the inbox directory; ``on_change`` persists writes
    (a Modal ``Volume.commit.aio``; sync or async) after each accepted chunk and on finish."""

    def __init__(
        self,
        root: Path,
        key: bytes,
        on_change: Callable[[], object] | None = None,
        clock: Callable[[], float] = time.time,
        max_file_bytes: int = MAX_FILE_BYTES,
    ) -> None:
        self.root = Path(root)
        self.key = key
        self.on_change = on_change or (lambda: None)
        self.clock = clock
        self.max_file_bytes = max_file_bytes

    async def __call__(self, scope: dict, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            while True:
                msg = await receive()
                if msg["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif msg["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if scope["type"] != "http":
            return
        method, path = scope["method"], scope["path"]
        query = {k: v[0] for k, v in parse_qs(scope.get("query_string", b"").decode()).items()}
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        token = headers.get("x-upload-token") or query.get("t")
        exp = check_token(self.key, token, self.clock())
        try:
            if method == "GET" and path == "/":
                if exp is None:
                    return await _html(send, 403, EXPIRED_HTML)
                return await _html(send, 200, UPLOAD_HTML)
            if exp is None:
                return await _json(send, 403, {"error": "This upload link has expired."})
            if method == "GET" and path == "/api/check":
                return await _json(send, 200, {"ok": True, "expires": exp})
            if method == "POST" and path == "/api/start":
                body = await _read_all(receive, 16 * 1024)
                return await self._start(send, body)
            upload = self._upload_dir(query.get("id"))
            if method == "GET" and path == "/api/status":
                return await _json(send, 200, {"received": self._received(upload)})
            if method == "PUT" and path == "/api/chunk":
                return await self._chunk(send, receive, upload, query.get("offset"))
            if method == "POST" and path == "/api/finish":
                return await self._finish(send, upload)
            return await _json(send, 404, {"error": "not found"})
        except ValueError as exc:
            return await _json(send, 400, {"error": str(exc)})

    # -- routes
    async def _start(self, send: Send, body: bytes) -> None:
        try:
            raw = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise ValueError("bad request") from exc
        meta = clean_owner_meta(raw)
        if meta["size"] > self.max_file_bytes:
            raise ValueError("That file is too big.")
        stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime(self.clock()))
        upload_id = f"{stamp}-{secrets.token_hex(4)}"
        d = self.root / upload_id
        d.mkdir(parents=True, exist_ok=False)
        meta["started_at"] = int(self.clock())
        (d / META).write_text(json.dumps(meta, indent=2))
        (d / PART).touch()
        await self._changed()
        await _json(send, 200, {"id": upload_id, "chunk": CHUNK_BYTES})

    async def _chunk(self, send: Send, receive: Receive, d: Path, offset: str | None) -> None:
        meta = self._meta(d)
        part = d / PART
        if not part.exists():
            return await _json(send, 409, {"error": "upload already finished"})
        have = part.stat().st_size
        if offset is None or not offset.isdigit() or int(offset) != have:
            await _drain(receive)
            return await _json(send, 409, {"received": have})
        limit = min(MAX_CHUNK_BYTES, meta["size"] - have)
        n = 0
        # Append straight to the part file: if the phone drops mid-chunk, what arrived
        # stays, and the client's next PUT gets a 409 with the true offset and resumes.
        with part.open("ab") as fh:
            while True:
                msg = await receive()
                if msg["type"] == "http.disconnect":
                    break
                data = msg.get("body", b"")
                if n + len(data) > limit:
                    fh.truncate(have)
                    await _drain(receive, msg)
                    raise ValueError("chunk too large")
                fh.write(data)
                n += len(data)
                if not msg.get("more_body"):
                    break
        await self._changed()
        await _json(send, 200, {"received": have + n})

    async def _finish(self, send: Send, d: Path) -> None:
        meta = self._meta(d)
        part = d / PART
        final = d / f"upload{meta['ext']}"
        if final.exists() and not part.exists():
            return await _json(send, 200, {"ok": True})
        have = part.stat().st_size if part.exists() else 0
        if have != meta["size"]:
            return await _json(send, 409, {"received": have})
        part.rename(final)
        meta["completed_at"] = int(self.clock())
        (d / META).write_text(json.dumps(meta, indent=2))
        await self._changed()
        await _json(send, 200, {"ok": True})

    # -- helpers
    async def _changed(self) -> None:
        result = self.on_change()
        if inspect.isawaitable(result):
            await result

    def _upload_dir(self, upload_id: str | None) -> Path:
        if not upload_id or not UPLOAD_ID.match(upload_id):
            raise ValueError("bad upload id")
        d = self.root / upload_id
        if not (d / META).exists():
            raise ValueError("unknown upload")
        return d

    @staticmethod
    def _meta(d: Path) -> dict:
        return json.loads((d / META).read_text())

    @staticmethod
    def _received(d: Path) -> int:
        part = d / PART
        return part.stat().st_size if part.exists() else json.loads((d / META).read_text())["size"]


async def _read_all(receive: Receive, limit: int) -> bytes:
    buf = b""
    while True:
        msg = await receive()
        buf += msg.get("body", b"")
        if len(buf) > limit:
            raise ValueError("request too large")
        if not msg.get("more_body"):
            return buf


async def _drain(receive: Receive, last: dict | None = None) -> None:
    msg = last or {"type": "http.request", "more_body": True}
    while msg.get("type") == "http.request" and msg.get("more_body"):
        msg = await receive()


_SECURITY_HEADERS = [
    (b"cache-control", b"no-store"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"x-robots-tag", b"noindex, nofollow"),
]


async def _send(send: Send, status: int, ctype: bytes, body: bytes, extra=()) -> None:
    headers = [(b"content-type", ctype), (b"content-length", str(len(body)).encode())]
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": headers + _SECURITY_HEADERS + list(extra),
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _json(send: Send, status: int, obj: dict) -> None:
    await _send(send, status, b"application/json", json.dumps(obj).encode())


async def _html(send: Send, status: int, html: str) -> None:
    csp = (
        b"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
        b"connect-src 'self'; form-action 'none'; base-uri 'none'"
    )
    await _send(
        send,
        status,
        b"text/html; charset=utf-8",
        html.encode(),
        [(b"content-security-policy", csp)],
    )


EXPIRED_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Link expired</title>
<style>body{font:17px -apple-system,system-ui,sans-serif;margin:2rem;color:#111}</style></head>
<body><h1>This upload link has expired</h1><p>Ask the team for a new link.</p></body></html>
"""

# The page (HTML + a little JS, no external assets) lives next to this module.
UPLOAD_HTML = (Path(__file__).parent / "intake_page.html").read_text(encoding="utf-8")
