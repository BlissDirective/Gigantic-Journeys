# Proposal — Publish, browse, rank, moderation (v1 / M4)

**Status: PROPOSAL for Owner review · 2026-09-20 · Coordinator.** Rationale doc (not a decision). Deepens SPEC §3.7 (+ §3.9 retention, §3.10 backend) and **decomposes milestone M4 into tickets** (none exist yet). **Builds on — does not re-open — the locked browse cards (decision 8) and results/store screens (decision 9), both AUTH #005.** Adopting it is a design-change **AUTH** touching SPEC §3.7. Grounded in Design Skills rules 24/25/28/50, SECURITY_CHECKLIST §2/§3/§4.4/§10, and **Apple App Store Review Guideline 1.2 (UGC)** — a hard launch gate.

## 0. Thesis
This is the **back half that turns a private scan into a living, ranked, trustworthy community** — the loop that makes GJ a platform, not a single-player toy (the Roblox/Dreams UGC lesson, rule 50). The screens are locked (decisions 8/9); what's missing is the **systems and the trust layer**. Three principles:
- **Trust is the product.** A UGC feed lives or dies on moderation and anti-cheat. Getting these right is a launch gate (Apple 1.2), not a polish item.
- **The place is the content.** Browse by place, rank by a blend of *how it plays* and *how it's built*, never by follower counts or vanity metrics.
- **Creator dignity.** Fast, visible moderation and honest creator stats are the strongest retention loop (rule 25); rejection is always explained and appealable.

## 1. Publish flow + moderation pipeline
**States:** `Draft (creator-only, always playable by its creator)` → `Publish tapped (opt-in)` → **server-side re-strip** (GPS/EXIF/location atoms removed again, verified; SECURITY_CHECKLIST §4.4) → **automated vision moderation pass** → `Under review` (decision 8g badge; creator-only) → `Cleared → Public` **or** `Rejected (one-line reason + Appeal)`. Unpublish removes from all feeds immediately (§3.9) and frees a free-tier slot.

**Moderation pipeline (the trust layer):**
- **Automated vision pass** screens every publish for the report reasons (decision 8d: private information visible, inappropriate content, not a real place, broken environment) before public.
- **Human queue** (gj-data, escalation to Owner) handles low-confidence auto flags, **all user reports**, and appeals; **Bots get no raw media beyond the published thumbnail + package** (SECURITY_CHECKLIST §10.4).
- **Reports** (decision 8d one-tap + reason sheet) are rate-limited per user/device (§10.2); a reported item shows "Under review" to the reporter immediately.
- **Illegal content** (e.g. CSAM) has a defined escalation to authorities + preservation; repeat offenders are actioned; **abusive users can be blocked**.
- **Apple 1.2 four pillars (hard gate), all satisfied:** (1) a filter for objectionable content (the vision pass), (2) report + timely response (one-tap report + the queue), (3) block abusive users, (4) published developer contact info. §9.1 is where the *clearance model* fork lives.

## 2. Ranking + anti-gaming
The feed surfaces environments through the locked sort tabs (decision 8b: **Top this week · New · Near your scale** [Room/Tabletop]). The score blends:
- **Community four-axis ratings** (fun / interesting / interactive / exciting — decision 8c), and
- **Derived objective signals** (SPEC §3.7): verticality, move variety, reachable volume, completion rate, replay rate.
- **"Top this week"** applies a time-decay so fresh, well-received places surface; **New** is recency; **Near your scale** filters Room vs Tabletop.
- **Anti-gaming** (owned by gj-data, SECURITY_CHECKLIST §10.2, an **M4 exit test**): per-user/device rate-limits, one-rating-per-account-per-environment, weighting toward trusted signals, self-rating and brigade detection, and **survival of a deliberate rate-spam test**.
The exact **composition** (how much ratings vs signals) is §9.2's fork; whatever the choice, weights are **telemetry-tunable** post-launch without a redesign.

## 3. Leaderboards + time-trial integrity
- **Per-route time trials** with a **ghost replay** for the UX; **creator stats** (plays, completions, best times) on the creator's own environments (decision 8e, creator-only in v1).
- **Plausibility validation** (SPEC §3.7): a submitted time is accepted only if it clears the **deterministic reachability validator's theoretical minimum** for that route (reuse the journey-gen validator, M1-SCEN-05 — the same movement.json constants that gate route generation gate leaderboard times) plus telemetry sanity checks. The *depth* of verification is §9.3's fork.
- Times are rate-limited and tied to a completed, validated run; impossible or anomalous times are rejected, not shown.

## 4. Environment package + delivery
- **Package** (SPEC §3.7): splat, collision mesh, scene graph, environment spec, thumbnail — vendor-neutral, versioned.
- **Delivery:** Supabase storage behind a **CDN**; every package/splat/mesh/full thumbnail served **only through signed URLs (≤15 min TTL), issued server-side after an auth check; the CDN forwards the signature; direct storage URLs are never exposed** (SECURITY_CHECKLIST §3.1/§3.3). Packages carry **no location data** (§4.4).
- **Deep links** (decision 8f): open the environment card with a single *Journey* action; App Store fallback if not installed; the link carries no location data.
- **Free tier:** unlimited scans and play; **3 published environments live at once** (SPEC §3.7) — the cap is enforced at publish; owning an IAP SKU lifts it (value set at M5, SPEC §3.8).

## 5. Data model + RLS (the backend contract)
New Supabase tables (migrations, not the frozen `data/schemas/`): `environments`, `publishes`, `ratings`, `reports`, `leaderboard_times`, `moderation_actions`. **RLS on every table** (SECURITY_CHECKLIST §2.1) with the locked policy patterns (§2.2):
- **owner-only** (`user_id = auth.uid()`) for drafts, a creator's own stats, and their unpublished environments;
- **published-read** (published **and** moderation-cleared) for public browse/play;
- **service-role-only** for the moderation queue and ranking jobs (no client policy).
Ratings/reports/time submissions are **rate-limited per user + device**; every server endpoint checks auth and RLS backs every query (§9.3 of the checklist). This is a **security-sensitive** area → 100% independent secondary review (AUTH #007).

## 6. Moderation ops + safety
- The queue is operated by **gj-data**, escalates to the **Owner**, and never exposes raw user media to Bots beyond the thumbnail + package (§10.4).
- **Retention** (§3.9): a published copy lives while published; **unpublish removes it from feeds immediately**; per-user delete-all removes everything; source scan video is already deleted once derived assets exist.
- **Creator-facing:** rejection reasons are one line with an **Appeal**; "Under review" is fast and visible (rule 25) so the community trusts the feed.
- **Developer contact info** is published (Apple 1.2 #4) — a LEGAL follow-up (UGC ToS / EULA acknowledging Apple's zero-tolerance for objectionable UGC).

## 7. Governance — M4 ticket decomposition (none exist yet)
Adopting this deepens **SPEC §3.7** and creates the M4 set:
- **M4-PLAT-01** — Environment package + CDN delivery via signed URLs (≤15 min, server-side auth, CDN forwards signature); unpublish; free-tier 3-live cap. *(SEC-sensitive)*
- **M4-DATA-01** — Social data model + RLS + rate-limits (the §5 tables + policies). *(SEC-sensitive)*
- **M4-DATA-02** — Ranking + anti-gaming (the §2 blend + Top-this-week decay; rate-spam test = M4 exit).
- **M4-DATA-03** — Moderation pipeline + queue + appeal + Apple 1.2 (vision pass, states, human queue, block, escalation).
- **M4-GAME-01** — In-app publish + browse + rating + report (wires decisions 8/9 to the backend).
- **M4-GAME-02** — Leaderboards + time-trial integrity (ghosts + plausibility validation reusing M1-SCEN-05).
- **M4-QA-01** — M4 exit harness: 50 published environments, zero moderation misses in the Owner's review, ranking survives a rate-spam test.
- **M4-FORE-01** — M4 checkpoint report.
- **LEGAL follow-up** — UGC ToS/EULA + published contact info (Apple 1.2 #4).

The fork answers (§9) shape the ATs of M4-DATA-03 (clearance), M4-DATA-02 (ranking composition), and M4-GAME-02 (integrity depth).

## 8. Non-goals for v1 (kept out on purpose)
Public creator profiles, follows/friends feeds, comments/DMs, and remix/fork of others' environments are **post-launch** (decisions 8b/8e: "friends/social later"). v1 is browse → rate → report → race, with creator stats visible to the creator only.

## 9. Decisions needed before editing the protected doc
### 9.1 Moderation clearance model
- **(A) Auto-clear + human-on-report** *(recommended)* — the vision pass clears most publishes to public quickly; a human queue handles low-confidence flags, all reports, and appeals. Scales; satisfies Apple 1.2. Risk: a bad item can be briefly public before a report.
- **(B) Human-review-every-publish before public** — every environment waits for a human to clear it. Safest, feasible at the ~50-tester M4 scale; does not scale past launch, adds latency + ops load, and needs a transition plan to (A). (Both let a creator always play their own; the fork is what makes it *public*.)

### 9.2 Ranking composition
- **(A) Balanced blend** of four-axis ratings + objective signals, telemetry-tunable *(recommended)* — rewards both "fun" and "well-built"; anti-gaming mitigates the moderate gameability.
- **(B) Ratings-led** — community four-axis dominates; most democratic, most gameable (leans hardest on anti-gaming).
- **(C) Signals-led** — objective build-quality signals dominate; least gameable, but can surface impressive-but-not-fun places.

### 9.3 Leaderboard integrity depth
- **(A) Plausibility floor + telemetry sanity** *(recommended)* — reject times below the deterministic validator's theoretical minimum (reuse M1-SCEN-05) and obvious anomalies; a ghost for the UX. Cheap; catches blatant cheats; misses sophisticated ones.
- **(B) Full deterministic replay verification** — record the run's inputs/telemetry and re-simulate server-side to confirm the time is genuine. Near-uncheatable leaderboards, but needs a deterministic, replayable movement sim + server-side re-simulation — significant engineering (fits "build it legendary, no rush").

On your answers I'll file the AUTH, deepen SPEC §3.7, and create the M4 tickets (with the fork-shaped ATs). Unless you object, I'll adopt the **publish/moderation pipeline**, the **signed-URL delivery + RLS model**, the **Apple 1.2 compliance set**, and the **v1 non-goals** as specified.
