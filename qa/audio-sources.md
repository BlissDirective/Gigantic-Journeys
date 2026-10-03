# Audio sources — provenance (M1-GAME-04 / AUTH #022, AT-4)

**Policy: CC0 / royalty-free / self-recorded foley only — no licensed or encumbered audio** (clean-IP
posture, SPEC §3.6, AUTH #022). Every shipped clip is listed here with its source, license, and the
`data/audio/sound_bank.json` event(s) it serves. The mobile budget — a sample-memory cap, a
polyphony/voice cap, streamed ambience, compressed clips — is recorded by gj-gameplay as the engine lands.

**Acceptable licenses:** CC0 / public domain, or royalty-free with irrevocable commercial use and no
attribution-in-app requirement (attribution is recorded here regardless). **Not acceptable:** CC-BY-NC,
CC-BY-ND, CC-BY-SA, sample packs with per-title licensing, or anything requiring ongoing royalties.

| Clip file | Event(s) | Source | License | Notes |
|---|---|---|---|---|
| _(pending)_ | | | | gj-gameplay fills this in as clips are sourced |

## Checklist before a clip ships
- [ ] License is CC0 or equivalent (link to the source + license page archived).
- [ ] No attribution-in-app requirement (or the app credits screen covers it).
- [ ] Trimmed, loudness-normalized, compressed to the mobile format; fits the memory/polyphony budget.
- [ ] Mapped to a `data/audio/sound_bank.json` event; round-robin variants grouped.
- [ ] Self-recorded foley: the Owner/recordist owns the recording (note the device + date).
