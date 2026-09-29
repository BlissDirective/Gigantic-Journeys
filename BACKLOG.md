# BACKLOG.md

Deferred scope and ideas, each with a one-line rationale. Nothing here is scheduled. Promoting an item into a milestone is a milestone-plan change (AUTH). The Foreman cannot promote without it.

## Deferred from v1 by the product lock (kit, 2026-09-13)
- Synthetic game objects (enemies, coins, platforms, creatures, tokens, hazards): the environment is the content in v1.
- Branded-object collaborations: a post-launch business line once the environment database exists.
- Tier 2 physics as a shipped feature: research track only (SPEC §5); decision at the M4 checkpoint.

## Deferred by AUTH #001 (movement)
- Ultimate Traversal Anims pack, traceur capture via Move.ai, MxM commercial motion-matching license, any mocap suit: V2 pending v1 results.
- Stamina, damage, wall-run: Bible §14.

## V2 verb tools (Bible §14, each an `IVerbProvider` layer)
- Grapple · parachute or glider · climbing picks or suction · spring shoes · rope.

## From the plan v0.1 seed
- Outfits and cosmetics beyond the two SKUs · realism tiers · outdoor and garden capture · street capture with face and plate blur · multiplayer race · level packs by theme · seasonal content · community challenges · Apple Vision Pro and Quest port of the diorama view · affordance library licensing · creator revenue share.

## Harness and process
- SHA-pin third-party GitHub Actions (planned M4, SECURITY_CHECKLIST §7.1).
- Certificate pinning decision (M5 ADR).
- Self-hosted reconstruction path (documented as a fallback in ADR-0003; not built).

## Deferred by AUTH #003 (platform)
- Android release (v1.1): the Unity project keeps the target compiling on demand; open the Play Console early because a personal account needs a 12-tester, 14-day closed test before production access; Material 3 shell work; Android device QA.
- iPhone Duo candidates the Owner does not select (`design/proposals/iphone-duo-track.md`).

## Surfaced by the overnight worker (2026-09-28)
- **Touch controls repositionable and resizable** (DESIGN_SYSTEM decision 5 binding constraint): not in M0-UNITY-03's ATs; the M0 floating stick + fixed jump pad ship first. Source: M0-UNITY-03 QA D1 (gj-operator, 2026-09-28).
- **Double-tap to sprint** (Bible §3.1 "run held 1.5 s or double-tap"): needs a double-tap window value in the proposed movement.json `intent` section. Source: M0-UNITY-03 QA D2.
- **Privacy Policy v0.2 for v1** (`legal/PRIVACY_POLICY.md`): the data table and intro still describe face/body photos and avatar assets under a v1 scope note (AUTH #020). Rewrite the table from `legal/RETENTION_SCHEDULE.md` v0.2, link `legal/DELETION_FLOW.md`, and align the telemetry wording with the frozen schema and the proposed App Store privacy label (`data/schemas/README.md`). Source: M0-LEGAL-02 / M0-DATA-01 (gj-operator, 2026-09-29).
- **Delete-all build + staging test** (`legal/DELETION_FLOW.md` §3–§7): `POST /account/delete` edge function, the Inngest workflow, `deletion_requests` / `deletion_receipts` tables (an AUTH data-schema change), Apple token revocation, and the synthetic-user staging test plus the "every user_id table has a delete step" CI check. SECURITY_CHECKLIST §6.4 (M5 gate) and App Store 5.1.1(v). No ticket exists yet. Source: M0-LEGAL-02.
- **Resize-safe HUD and touch layout (verify on Duo)**: on iPhone Duo (fold, unfold, Split View) the screen size changes mid-session. `TouchIntentSource.Layout` already re-reads `Screen.safeArea` and dpi every frame, so the zones follow a resize. Still to check on a device: (a) cancel an active floating-stick touch when the layout changes, so the stick origin doesn't sit in stale coordinates; (b) keep critical HUD away from the fold at the centre of the inner display; (c) set the `TouchControlsView` viewport height at resize time. Source: M1-DUO-01 research (gj-operator, 2026-09-29).
