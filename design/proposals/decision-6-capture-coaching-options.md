# Decision 6 — Capture coaching UI: options for the Owner's lock

`design/proposals/decision-6-capture-coaching-options.md` · 2026-09-16 · Coordinator. Binding constraints (`DESIGN_SYSTEM.md` §6; Design Skills rules 12–15; decision 2: teal is the capture-state and progress color): coach steady motion, overlap, angles, and light; live coverage heat-map; speed meter turning amber; blur rejection with a haptic; "you missed this corner"; two scripts (room walkthrough, tabletop orbital) chosen by one illustrated toggle; reject early and kindly; no text-only instructions; active capture under 90 s. Reply `APPROVED: decision 6 = recommended package`, or list the letters that differ; the Coordinator assigns the AUTH number when logging.

## 6a. Coverage feedback

- **A (recommended). Paint the room.** A translucent teal wash accumulates directly on the live camera view over surfaces already captured (anchored in AR), so uncovered areas stay unpainted; a small coverage ring at the top right shows the percentage. Nothing to read; the room itself is the map of what is missing (rules 12 and 15).
- B. A separate top-down heat-map in a corner. Precise, but pulls the eye off the viewfinder.

## 6b. Speed meter

- **A (recommended).** A thin arc under the record button fills teal at a good pace and turns amber with one gentle haptic when the phone moves too fast; the line "Slow down a little" appears only after a full second of amber, then fades.
- B. A numeric speed readout. Accurate, unreadable while walking.

## 6c. Blur and low light

- **A (recommended).** Blur: one soft haptic tick and a single amber pulse on the frame edge; no words. Low light: a one-line card, "Too dark here. Turn on a lamp?", with Continue anyway. The capture never hard-stops (rule 14).
- B. Hard stop until conditions improve. Safer output, more abandoned captures.

## 6d. Mode toggle

- **A (recommended).** A two-segment toggle above the record button with looping line illustrations: Room (a figure arcing at chest height around a couch) and Tabletop (a figure circling a build at two heights). Chosen before recording, remembered for next time, never in settings (rule 13).
- B. Auto-detect from the first seconds with a confirmation sheet. Clever, and wrong often enough to annoy.

## 6e. Missed-corner hint

- **A (recommended).** Before upload, a 3D arrow anchored in the live view points at the largest unpainted region with "You missed this corner" and two actions: Got it (keeps recording) and Upload anyway.
- B. A list of gaps. Text where an arrow does the job.

## 6f. Progress and timing

- **A (recommended).** A ring around the record button fills over 90 s as a target, not a limit; past three minutes it turns amber with "Long captures rebuild worse" (rule 12). Coverage percentage sits inside the ring. Done appears at 60 % coverage or after 60 s, whichever comes first.
- B. A countdown that stops recording at 3 minutes. Clean, but punishes big rooms.

## 6g. Primary action and states

- **A (recommended).** One 72 pt record button: neutral disc at rest, teal while recording, Done as the single primary action afterward (rule 4). Preview of the last 5 s before upload with Retake.

## 6h. iPhone Duo

- Split View coaching (candidate 4) is not selected for v1; the standard layout runs on the 7.6-inch display. Recorded for v1.1.

## Recommended package

6a-A, 6b-A, 6c-A, 6d-A, 6e-A, 6f-A, 6g-A.
