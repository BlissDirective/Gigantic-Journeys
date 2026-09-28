"""Corpus manifest schema + rules (M0-CAPT-01 AT-2): the committed manifest validates,
rows carry the Bible §1 classes / Lego flag, readiness + coverage, and no GPS,
addresses or people."""

from __future__ import annotations

import copy
import json

import pytest
from tools import corpus_manifest as cm

jsonschema = pytest.importorskip("jsonschema")

SCHEMA = json.loads(cm.SCHEMA.read_text(encoding="utf-8"))
VIDEO = {
    "container": "mov",
    "codec": "hevc",
    "width": 3840,
    "height": 2160,
    "fps": 29.97,
    "hdr": False,
    "rotation": 0,
    "audio_kept": False,
    "size_bytes": 300_000_000,
    "sha256": "a" * 64,
}


def row(mode="room", cid=None, **owner_over):
    owner = {
        "mode": mode,
        "lighting": "bright-daylight",
        "objects": {
            "couch": True,
            "coffee_table": True,
            "dining_chair": False,
            "bookshelf": True,
            "lego": True,
        },
        "privacy_ok": True,
        "note": "north-facing window",
    }
    owner.update(owner_over)
    return cm.build_row(
        capture_id=cid or f"{mode}-01",
        owner=owner,
        video=dict(VIDEO),
        duration_s=92.4 if mode == "room" else 45.0,
        device_model="iPhone 15 Pro",
        captured_on="2026-09-28",
        received_on="2026-09-28",
        strip_tool="strip_metadata.py 1.0",
        verified_with=["exiftool 13.25", "ffprobe 7.1"],
        location_found=False,
    )


def manifest(*rows):
    return {
        "schema_version": "1.0",
        "storage": {"backend": "modal-volume", "volume": "gj-corpus", "root": "/corpus"},
        "captures": list(rows),
    }


def test_schema_is_valid_draft_2020_12():
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


def test_committed_manifest_validates():
    data = json.loads(cm.MANIFEST.read_text(encoding="utf-8"))
    assert cm.validate(data) == []


def test_room_and_tabletop_rows_validate():
    m = manifest(row("room"), row("tabletop"))
    assert cm.validate(m) == []
    room, table = m["captures"]
    assert set(room["objects"]) == {"couch", "coffee_table", "dining_chair", "bookshelf"}
    assert table["objects"] == {"lego": True}
    assert room["readiness"] == {"score": None, "source": "not-measured"}
    assert room["storage"]["path"] == "/corpus/room-01/room-01.mov"
    assert room["intake"]["warnings"] == []


@pytest.mark.parametrize("field", ["gps", "latitude", "address", "location", "people", "serial"])
def test_no_location_or_identity_field_can_be_added(field):
    r = row()
    r[field] = "x"
    assert cm.validate(manifest(r))
    r = row()
    r["device"][field] = "x"
    assert cm.validate(manifest(r))


def test_room_needs_all_four_bible_classes_and_tabletop_needs_lego():
    r = row()
    del r["objects"]["couch"]
    assert cm.validate(manifest(r))
    t = row("tabletop")
    del t["objects"]["lego"]
    assert cm.validate(manifest(t))


@pytest.mark.parametrize(
    "note,label",
    [
        ("shot at 41.8781, -87.6298", "coordinates"),
        ("our place, 1600 Pennsylvania Ave", "street address"),
        ("call 312-555-0100 for access", "phone number"),
        ("ask jane@example.com", "e-mail"),
        ("see https://maps.example/x", "url"),
    ],
)
def test_free_text_with_places_or_contacts_is_rejected(note, label):
    r = row()
    r["notes"] = note
    errs = cm.validate(manifest(r))
    assert any(label in e for e in errs), errs


def test_build_row_scrubs_a_note_that_looks_personal():
    r = row(note="1234 Oak Street")
    assert "removed" in r["notes"] and cm.validate(manifest(r)) == []


def test_ids_unique_prefix_matches_mode_and_path_matches_id():
    a, b = row(), row()
    assert any("duplicate" in e for e in cm.validate(manifest(a, b)))
    bad = row()
    bad["id"] = "tabletop-01"
    assert cm.validate(manifest(bad))
    moved = row()
    moved["storage"]["path"] = "/corpus/room-02/room-02.mov"
    assert any("storage.path" in e for e in cm.validate(manifest(moved)))


def test_device_is_a_model_never_a_serial_or_name():
    r = row()
    r["device"]["model"] = "Jane's iPhone"
    assert cm.validate(manifest(r))


def test_readiness_and_coverage_share_the_live_bundle_shape():
    r = row()
    r["readiness"] = {"score": 0.82, "source": "gj-app"}
    r["coverage"] = {"summary": "painted 82%", "fraction": 0.82, "passes": 2}
    assert cm.validate(manifest(r)) == []
    r["readiness"]["score"] = 1.5
    assert cm.validate(manifest(r))


def test_quality_warnings_follow_the_capture_guide():
    v = dict(VIDEO, width=1920, height=1080, codec="h264", fps=60, hdr=True)
    w = cm.quality_warnings("room", v, 200, "dim")
    text = " ".join(w)
    for needle in ("not 4K", "H.264", "60 fps", "HDR", "3 min", "dim"):
        assert needle in text
    assert cm.quality_warnings("tabletop", VIDEO, 45, "mixed") == []
    assert "long for a tabletop" in " ".join(cm.quality_warnings("tabletop", VIDEO, 120, "mixed"))


def test_next_id_never_reuses_a_taken_id():
    assert cm.next_id("room", set()) == "room-01"
    assert cm.next_id("room", {"room-01", "room-02", "tabletop-01"}) == "room-03"


def test_summary_counts_owner_targets():
    rooms = [row(cid=f"room-0{i}") for i in range(1, 4)]
    tables = [
        row("tabletop", cid="tabletop-01"),
        row("tabletop", cid="tabletop-02", objects={"lego": False}),
    ]
    s = cm.summary(manifest(*rooms, *tables))
    assert s["rooms"] == 3 and s["tabletops"] == 2
    assert s["rooms_with_all_bible_classes"] == 0  # dining_chair False in the fixture
    assert s["lego_tabletops"] == 1


def test_cli_validates(capsys):
    assert cm.main([str(cm.MANIFEST)]) == 0
    assert "OK" in capsys.readouterr().out


def test_schema_and_manifest_are_the_only_committed_corpus_files():
    # README + manifest + schema are text; the media never lives in the repo.
    # The open-license video stand-in corpus (M0-OWNER-01) adds a text manifest and
    # an attribution note; its clips live only in the gj-corpus Modal Volume. The
    # reconstruction results (M1-CAPT-03) are a text summary; splats stay in the volume.
    names = {p.name for p in cm.CORPUS_DIR.iterdir() if not p.name.startswith(".")}
    allowed = {
        "README.md",
        "manifest.json",
        "manifest.schema.json",
        "open_video_corpus.json",
        "OPEN_VIDEO_ATTRIBUTION.md",
        "open_video_recon_results.json",
    }
    assert names <= allowed, names


def test_example_rows_do_not_mutate_shared_fixture():
    a = row()
    b = copy.deepcopy(a)
    b["objects"]["couch"] = False
    assert a["objects"]["couch"] is True
