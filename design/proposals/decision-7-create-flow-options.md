# Decision 7 — Create-flow waiting states: options for the Owner's lock

`design/proposals/decision-7-create-flow-options.md` · 2026-09-16 · Coordinator. Binding constraints (`DESIGN_SYSTEM.md` §7; Design Skills rules 4, 11; SPEC §6 targets: scan to playable ≤ 10 min, avatar < 2 min): progress on every wait over 1 s; determinate progress plus something to look at over 10 s; the splat resolves progressively; a "what's happening" explainer; never a blank spinner. Reply `APPROVED: decision 7 = recommended package`, or list the letters that differ; the Coordinator assigns the AUTH number when logging.

## 7a. The reconstruction wait

- **A (recommended). The room resolves.** The backdrop is the cached blurred room (decision 3's backdrop, built from the capture's last frames or the first splat chunk); the sharp splat resolves progressively from the center as chunks arrive. A determinate bar with four stages: Uploading · Rebuilding your environment · Finding the summit · Choosing routes. One line under it says what is happening ("Turning 1,400 photos into a place you can climb"). The transition then plays straight out of the sharp room.
- B. A slowly rotating placeholder diorama with capture tips. Pleasant, disconnected from the player's own room.

## 7b. The avatar wait

- **A (recommended). You appear.** The captured full-body silhouette turns slowly and fills in from wireframe to textured as stages complete: Reading your photos · Building your head · Fitting your body · Dressing you. It ends on the likeness confirmation (decision 4) with no extra screen in between.
- B. A generic progress bar with the brand icon. Cheap, forgettable.

## 7c. Background continuation

- **A (recommended).** Both waits can run in the background: a Live Activity shows the stage and progress; the player can journey through the demo environment or browse meanwhile; a notification says "Your living room is ready" (the environment's name if the player gave one). Nobody is trapped watching a bar.
- B. Foreground only. Simpler, and the wait becomes the app's first impression.

## 7d. Estimates

- **A (recommended).** "About 4 minutes" from the rolling median of recent jobs, updated as stages complete; the bar never reaches the end and stalls. Under 10 s of remaining time the estimate disappears and the bar just finishes (rule 11).
- B. No estimate. Honest, anxious.

## 7e. Failure states

- **A (recommended).** Kind, specific, actionable, in the voice of decision 2: "This capture was too dark to rebuild. Try again with the lamps on?" with Retry and Keep the capture. Never an error code in the copy; the code goes to the report, not the screen.
- B. A generic "Something went wrong". Forbidden by rule 14's spirit.

## 7f. Cost guard

- **A (recommended).** When the daily cap (kit §7) is reached, the player sees "We are rebuilding a lot of places today. Yours is queued and will be ready by <time>." and the job resumes automatically. The cap is never presented as an error.

## Recommended package

7a-A, 7b-A, 7c-A, 7d-A, 7e-A, 7f-A.
