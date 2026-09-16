# iPhone Duo — optional feature track (proposal)

`design/proposals/iphone-duo-track.md` · v0.1 · 2026-09-15 · Coordinator, for the Owner's selection.
Status: **selected 2026-09-15**. The Owner chose candidates 1, 2, and 3 (stand-mode console layout, unfold as the signature transition, rear-camera avatar capture). Tickets: M1-DUO-01 (research spike), M3-DUO-01, M3-DUO-02, M2-DUO-01, M5-DUO-01 (featuring nomination and launch video). Candidates 4–9 stay in BACKLOG.md. AUTH #003 covers the track. Everything here is additive: the app must be complete and equal in value on every iPhone (SPEC §11).

## 1. What the device is (Apple and press, retrieved 2026-09-15)

- Apple's first foldable iPhone. Inner display 7.6-inch Super Retina XDR, about 50 % larger than iPhone 18 Pro Max, nano-texture finish; outer display 5.4-inch with the same aspect ratio. Both 120 Hz ProMotion, up to 3000 nits.
- A20 Pro with a dual 16-core Neural Engine; 6-core CPU up to 20 % faster than A19 Pro; up to 50 % more memory bandwidth.
- Cameras: 48 MP Fusion main plus 48 MP Fusion ultra wide (2x optical-quality zoom), 12 MP Center Stage front camera, an under-display inner camera; 4K 120 fps video. No LiDAR is listed.
- Postures: landscape, portrait, tent, stand. Split View across displays. Apple Pencil (USB-C) support arriving later in 2026. iOS 27 with Apple Intelligence.
- Dual battery: up to 31 h video (inner) or 44 h (outer). Titanium frame, IP68, eSIM only.
- Pre-orders October 16, 2026; launch October 23, 2026. $1,999 (256 GB) to $3,199 (2 TB).

## 2. Timing

v1 store submission is planned for weeks 16 to 18 of the build, around mid-January 2027, roughly 12 weeks after the Duo ships. The Duo stays the newest iPhone through Q1 2027, and App Store editorial features apps that adopt a new form factor well after its launch. The angle is therefore "the first traversal game built for iPhone Duo" at *our* launch, plus a TestFlight public beta timed with the Duo's holiday window if M3 lands on schedule.

## 3. Constraints (from the v1 product lock and AUTH #003)

1. Optional and additive. No Duo-only content; identical value on every iPhone.
2. No synthetic game objects. Duo features change presentation, input, and capture, never what is in the environment.
3. No delay to v1. Each feature is its own ticket with a go/no-go at the M3 checkpoint; anything unfinished ships in v1.1.
4. Verification needs a Duo in hand or Xcode's Duo simulator (which needs a Mac). Design adaptively to screen size and posture; verify when a device is available. A Duo development device is an AUTH (spend) if the Owner wants one.
5. Research first: iOS 27 posture and hinge APIs and how Unity 6 exposes them; Split View behavior for Unity apps; rendering to the outer display while folded; Apple Pencil input in Unity.

## 4. Candidate features (ranked by value against effort)

| # | Feature | Why it fits Gigantic Journeys | Effort | Depends on |
|---|---|---|---|---|
| 1 | **Stand-mode console layout.** Fold at about 90°: the upper half is 100 % photograph with no HUD overlay at all; the lower half holds the stick, jump, the contextual action, the diorama overview with summit beacon and route lines, and the timer. | Reads like a handheld console; the photo stays untouched (Design Skills rule 1). Marketing shot number one. | Medium | Posture API; design decision 5 variant |
| 2 | **Unfold is the signature transition.** Opening the Duo triggers the shrink/diorama moment: the room on the outer display unfolds into the tiny world across the inner display. "Open your iPhone. Open your world." | Ties the one hero animation (decision 3) to a physical gesture only this device has. | Low to medium | Posture events; decision 3 text |
| 3 | **Rear-camera avatar capture with Duo Preview.** In tent mode on a table, the 48 MP rear cameras photograph the player while the outer display shows framing and coaching; the full-body rotation and the face close-up rotation come from the best cameras. | Better likeness for the M2 blind-test target; hands-free capture. | Low | Duo Preview behavior in Unity or a native plugin |
| 4 | **Split View capture coaching.** Inner display split: live camera on one side, coverage heat-map and "missed corner" hints on the other, at 7.6 inches. | Capture is the mode most apps get wrong (Design Skills §3.5); more room for coaching. | Medium | Split View in Unity |
| 5 | **Ghost race in Split View.** Per-route time trial with your own ghost or the leaderboard best rendered side by side. | Uses recorded routes already in v1; not networked multiplayer, so no conflict with the non-goals. | Medium | Route recording (M3) |
| 6 | **Apple Pencil route drawing.** Draw a challenge route on the diorama; the validator checks reachability and turns it into a playable route. Pencil also serves the one-tap "fix this label" correction in M6. | Turns the validator into a creative tool; unique to Pencil-on-iPhone. | Medium | Pencil support (later 2026); validator (M1) |
| 7 | **Vista photo mode at 7.6 inches and 3000 nits.** Wide-format vista shots exported at the inner display's aspect, share sheet. | Cheap showcase of the photoreal scan. | Low | Photo mode (M3) |
| 8 | **Outer-display Live Activity.** "Flag planted on <environment>" and the current route time on the 5.4-inch outer display when folded. | Native iOS feature; keeps the game present when closed. | Low | Live Activities |
| 9 | **Browse grid on the inner display.** Environment cards in two columns; diorama thumbnails get room. | Browse by place (rule 24) benefits from the canvas. | Low | Browse (M4) |

Recommended first picks if the Owner wants a Duo story at launch: 1, 2, and 3. They are visible in a 15-second clip, low risk, and touch systems already planned for M2 and M3.

## 5. Marketing beats

- App Store featuring nomination (App Store Connect) citing Duo adoption, submitted with the v1 build.
- Launch video: 3 s of a real room, the unfold, the diorama, 10 s of stand-mode play, publish, a friend plays. The diorama view remains the hero shot (Design Skills rule 28).
- TestFlight public beta link seeded in Duo early-adopter communities; hashtags #GiganticJourneys #iPhoneDuo.

## 6. Next steps

1. Owner picks candidates (reply with numbers).
2. Coordinator creates `M3-DUO-nn` tickets, starting with a research spike on the iOS 27 posture and Split View APIs in Unity (owner gj-gameplay, with gj-design for the layout variants).
3. Owner decides on a Duo development device (AUTH spend) or accepts device-less adaptive design until one is available.

Sources: [Apple, iPhone Duo](https://www.apple.com/iphone-duo/) · [MacRumors, release date and pre-orders](https://www.macrumors.com/2026/09/12/iphone-duo-release-date-preorders/) · [Macworld guide](https://www.macworld.com/article/2629813/iphone-ultra-folding-design-price-specs-release-date.html) · [Wikipedia](https://en.wikipedia.org/wiki/IPhone_Duo)
