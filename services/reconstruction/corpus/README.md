# Reconstruction corpus: capture guide, handover and storage rules

`services/reconstruction/corpus/` · M0-CAPT-01 · Owner: gj-capture · Operator: gj-operator · Used by M0-OWNER-01 (10 rooms + 5 tabletops) and the M1 reconstruction work (M1-CAPT-03).

**Rule zero: raw media never enters git.** This folder holds only this README, `manifest.json`, `manifest.schema.json`, and the open-license stand-in record `open_video_corpus.json` + `OPEN_VIDEO_ATTRIBUTION.md` (§7). `.gitignore` ignores everything else here. CI `secret-scan / repo hygiene` fails any commit that tracks `.mov/.mp4/.m4v/.heic/.ply/.splat/.spz`. The videos live in the project's private Modal volume `gj-corpus` (on the same Modal account as the reconstruction pipeline, AUTH #033). They never go to a third-party share, the Operator VM's repo checkout, or Supabase (see "Why not the Supabase staging bucket" below).

---

## 1. Owner: how to film (iPhone Camera app)

Set this up once:

| Setting | Where |
|---|---|
| **4K at 30 fps** | Settings > Camera > Record Video |
| **HDR Video off** (recommended: SDR reconstructs more predictably) | Settings > Camera > Record Video > HDR Video |
| **Camera location off** | Settings > Privacy & Security > Location Services > Camera > **Never** |
| **Video mode**, not Cinematic. **Action mode off** (the running-figure icon should not be yellow) | Camera app |

Before each video: make the light **bright and even** (lamps on, curtains open, no strong backlight). Take out or turn away anything with **faces (people or photos), documents, screens showing personal information, or addresses** (mail, packages). People should be out of the room. Hold the phone the same way (portrait or landscape) for the whole video.

**Room walkthrough (10 rooms, about 90 s each, never more than 3 min):**
1. Start in a doorway or corner and hold the phone up at **chest height**.
2. Walk a **slow arc** through the room. **Move sideways**; don't just stand and turn. Keep the far walls and furniture in view.
3. Sweep back over anything you went past quickly.
4. Do a **second pass**, low (under tables, around chair legs) and high (over shelves and the tops of furniture).
5. At least 3 of the rooms should include a **couch, coffee table, dining chair and bookshelf** (Movement Bible §1 objects).

**Tabletop build (5 builds, 30–60 s each; at least 2 Lego):**
1. Put the build in the middle of a table and step back so the **whole build is in frame**.
2. Walk **one slow circle** around it with the phone **low** (near table height), then **one slow circle higher**, looking down at it.
3. Keep the build centred the whole time.

These are the same coaching scripts the app will use (design/proposals/capture-ux-coaching-v1.md §2: room = chest-height arc + low/high pass; tabletop = slow orbit at two heights; paces per §3: under 90 s active, 3 min max).

## 2. Owner: how to send the videos

The team sends you **an upload link** (a private web page; it works for 72 hours and can only receive files, not show them). Send one video at a time.

**From the iPhone:**
1. On Wi-Fi, open the link in **Safari**.
2. Tap **Choose File**, then **Photo Library**, and pick the video. Tap **Options** at the top of the picker, choose **Current**, then **Done**. This keeps the full-quality original. You can also pick the video from **Files** instead.
3. Tap **Room** or **Tabletop build**, tick what's in it (couch, coffee table, dining chair, bookshelf, or "It is a Lego build"), and pick the light.
4. Tick **"No faces, documents, screens or addresses are visible."**
5. Tap **Upload** and keep the page open until it says **Done**. A 3-minute 4K video is about 0.5 GB, which takes a few minutes on home Wi-Fi. If it stops, tap Upload again.
6. Repeat for the next video.

**From a Mac:** AirDrop the videos from the iPhone to the Mac (this keeps the originals), open the same link in Safari or Chrome, and follow steps 2–6, choosing the file from Downloads.

When all 15 are sent, tell the team. That message is your confirmation for M0-OWNER-01 AT-3. The ticked box is stored per video.

---

## 3. Operator: intake (runs on the Operator VM; media never touches it)

One-time setup (done 2026-09-27; repeat only to rotate the key or redeploy):

```bash
cd ~/projects/gigantic-journeys && set -a; . ./.env.local; set +a   # MODAL_TOKEN_ID / MODAL_TOKEN_SECRET
python services/reconstruction/tools/corpus_intake.py setup          # random link-signing key -> Modal secret gj-corpus-intake (never printed)
modal deploy services/reconstruction/corpus_intake_app.py             # deploys the upload page (its URL is printed by `link`)
```

Every handover:

```bash
python services/reconstruction/tools/corpus_intake.py link --hours 72   # prints the Owner's upload link
python services/reconstruction/tools/corpus_intake.py status            # uploads received / in progress
python services/reconstruction/tools/corpus_intake.py process           # strip + verify + store + manifest rows
python services/reconstruction/tools/corpus_manifest.py --summary       # validate + M0-OWNER-01 counts
```

- **`link`** prints a capability URL. Anyone holding it can upload (never read) until it expires. Default 72 h, maximum 7 days. Send it to the Owner privately. Never put it in git, tickets, PRs or logs. The page accepts only `.mov/.mp4/.m4v/.heic/.jpg`, at most 4 GB per file, in chunks of 32 MB or less that are appended only at the exact current offset.
- **`process`** runs `process_inbox` **in a Modal container**. For each finished upload it:
  1. runs `tools/strip_metadata.py` (ffmpeg `-map 0:V:0 -c copy -map_metadata -1`: no re-encode; drops QuickTime `keys`/`udta` location, make/model/software, XMP, timed-metadata tracks and audio; keeps the rotation matrix);
  2. re-verifies the file with ExifTool (`-ee`) and ffprobe; if anything survives, the file is rejected and listed as FAILED;
  3. moves the clean file to `/corpus/<id>/<id>.mov` with a `capture.json`;
  4. **deletes the raw upload**;
  5. purges any unfinished upload older than 7 days (SECURITY_CHECKLIST §6.1).

  It then adds the new rows to `manifest.json` (existing rows keep any hand corrections) and validates them. Review the rows, fix labels if the Owner mis-ticked, and commit `manifest.json` (text only). `location_found_on_intake: true` means Camera location was on. The stored copy is clean, but tell the Owner.
- **Warnings** in `intake.warnings` compare each video against this guide: not 4K or H.264 (usually the picker's "Automatic" re-compression; ask for a re-upload with Options > Current), fps other than 30, HDR on, too short or too long, dim light.
- **Reconstruct** (M1-CAPT-03 pipeline on Modal): `python services/reconstruction/tools/corpus_intake.py fetch room-01 --out ~/gj-corpus-work --frames 2` downloads the stripped video and extracts frames. It refuses any path inside the git checkout. Then run `modal run services/reconstruction/modal_app.py --images ~/gj-corpus-work/room-01/images --scan-id room-01 --source corpus`. A Modal function can also mount the volume directly: `modal.Volume.from_name("gj-corpus", version=2)`, path `/corpus/<id>/`. Delete `~/gj-corpus-work/<id>` after the run.
- **Delete** (Owner request or bad capture): `python services/reconstruction/tools/corpus_intake.py delete room-03` removes the video and its manifest row. The id is tombstoned and never reused.

### Where things live

| What | Where | Lifetime |
|---|---|---|
| Raw upload (may carry GPS) | `gj-corpus:/inbox/<upload-id>/` | Until `process` strips it (then deleted); unfinished uploads purged after 7 days |
| Stripped, verified video | `gj-corpus:/corpus/<id>/<id>.mov` | Kept as the benchmark corpus (SPEC R1 / M1) until the Owner asks for deletion |
| Intake record | `gj-corpus:/corpus/<id>/capture.json` | Deleted with the capture |
| Manifest (no media, no GPS) | `services/reconstruction/corpus/manifest.json` (git) | Reviewed like code |
| Link-signing key | Modal secret `gj-corpus-intake` | Rotate: `modal secret delete gj-corpus-intake`, then `setup` (old links stop working) |
| Scratch frames for a run | `~/gj-corpus-work/<id>/` on the VM (outside the repo) | Delete after the run |

## 4. Manifest (`manifest.json`, schema `manifest.schema.json`)

One row per capture: `id` (`room-01`…, `tabletop-01`…), `mode`, `source`, `captured_on` (date only), `device.model` (marketing model only, never a serial or device name), `duration_s`, `lighting`, `objects` (rooms: `couch`, `coffee_table`, `dining_chair`, `bookshelf`; tabletops: `lego`; plus optional `other` words), `readiness` {`score`, `source`} and `coverage` {`summary`, `fraction`, `passes`} in the same shape as the live upload bundle (SPEC §3.1). Camera-app captures have no on-device score, so they read `not-measured` / `null`. Each row also carries `video` (codec, size, fps, rotation, sha256 of the stripped file), `storage.path`, `privacy` (stripped + verified-with + location-found + Owner check), `intake.warnings` and `notes` (300 characters maximum).

Every object is `additionalProperties: false`, so there is nowhere to put GPS, an address or a person. `tools/corpus_manifest.py` also rejects free text that looks like coordinates, a street address, a postal code, an e-mail, a phone number or a URL. CI validates the committed manifest (`tests/test_corpus_manifest.py`).

## 5. Why a Modal volume and not the Supabase staging bucket

AT-1 anticipated a "staging bucket once Supabase exists". Staging now exists, but it is on the **Free plan**: the project's global upload limit is **50 MB per object** (a bucket asking for more is refused with `413 EntityTooLarge`, probed 2026-09-27), and total storage is 1 GB. One 90-second 4K video is about 250 MB, and the full corpus is about 4–8 GB. The Modal volume is on the account the reconstruction already runs on, so the pipeline reads it with no extra copy. It costs nothing while idle (the upload page scales to zero), and it keeps data on project infrastructure (ADR-0005, SECURITY_CHECKLIST §6.3/§6.5). Moving the intake to a private Supabase bucket later needs the staging project on Pro (Owner spend decision). Only the upload target in `corpus_intake_app.py` would change; the stripper, manifest and schema stay the same.

## 6. Rules this follows

- SECURITY_CHECKLIST §4.1–4.2: location/EXIF/XMP/QuickTime atoms are stripped server-side, re-verified, and counted (`location_found_on_intake`). §4.3: fixture tests (`tests/test_strip_metadata.py`) inject synthetic GPS into generated JPEG, HEIC, MP4 and MOV files.
- §6.5: the corpus is Owner-supplied and consented. Bots handle only stripped corpus files, never user media. Real user scans never use this path.
- §6.3 / ADR-0005: reconstruction is corpus-only on our own infrastructure. No managed bridge is used.
- §1: the only secret (the link-signing key) lives in a Modal secret; nothing is committed. §7: the tools are standard library only (no new pip dependency); ffmpeg/ExifTool come from the Debian/Ubuntu archives in the Modal image and CI.

## 7. Open-license stand-in corpus (`/open-video`, Owner decision 2026-09-28)

For M0-OWNER-01 the Owner chose to source the day-one corpus from free, open-license online videos instead of filming it, and to keep it in this same private Modal volume (not Supabase). These clips are **not** Owner captures, so they do not go through the intake, do not get `manifest.json` rows (that schema describes Owner/app captures only) and live in their own namespace:

| What | Where |
|---|---|
| Video (as downloaded; the ESO clip is trimmed with a stream copy) | `gj-corpus:/open-video/rooms/<slug>/source.mp4`, `gj-corpus:/open-video/tabletop/<slug>/source.mp4` |
| Per-clip record (source page, direct file URL, creator, license + URL, attribution, resolution/duration/fps, sha256, why it suits reconstruction, caveats) | `.../<slug>/meta.json` |
| Whole-set manifest and credits | `gj-corpus:/open-video/MANIFEST.json`, `gj-corpus:/open-video/ATTRIBUTION.md` |
| Git record (text only, same content) | `open_video_corpus.json`, `OPEN_VIDEO_ATTRIBUTION.md` (this folder) |

Licenses accepted: CC0, CC BY, CC BY-SA (flagged), Pexels License, Pixabay Content License, Mixkit Stock Video **Free** License (Mixkit "Restricted" items are non-commercial and were rejected). No NC, ND or editorial-only material. The current set uses Pexels (10), Pixabay (3), Mixkit Free (1) and CC BY 4.0 ESO (1); only the ESO clip legally requires attribution ("F. Snik/Leiden University/ESO"), which must be shown wherever that clip or a render derived from it is shown publicly.

Use them like any corpus video: `modal volume get gj-corpus /open-video/rooms/<slug>/source.mp4 ~/gj-corpus-work/<slug>/` (outside the repo), extract frames, run the M1-CAPT-03 pipeline, delete the scratch copy. Check the `sha256` in `meta.json`, and read `caveats` first: several clips are portrait, short (8–15 s) or single-pass, and the glassware clip is a deliberate transparent-object stress case.
