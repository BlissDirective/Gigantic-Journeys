# Vendor research — IAP: RevenueCat vs Unity IAP (M5 ADR input)

**Decision-support for the M5 monetization ADR · observed 2026-09-17 · Coordinator research pass.** Unity 6 (6000.5), iOS-first (Android v1.1 later). Two **non-consumable** cosmetic SKUs (outfit pack, "realism+" materials) + one derived **entitlement** ("published environments" cap lifts if the user owns *either* SKU). No subscriptions, no consumables, no loot boxes (SPEC §3.8). Solo dev. Pricing/versions change — re-verify at build time. The choice is locked in the M5 ADR, not here.

## Recommendation

**Lean RevenueCat for v1, with Unity IAP as an explicit, fully-legitimate fallback** — the two are within a hair for a surface this small; the ADR settles it with the decision rule below.

**Why RevenueCat (for this case):**
1. **The entitlement is its native model.** "Own either SKU → lift the cap" is one dashboard entitlement mapped to both products + a one-line runtime check — the biggest reduction in solo-dev code/maintenance (validation + entitlement + restore + cross-platform glue handed off).
2. **Managed server-side receipt validation + webhooks, free**, landing cleanly in the **Supabase backend we already run** (webhook flips the cap server-side; no validation endpoint to build).
3. **Cost is negligible at our scale:** free below **$2,500 monthly tracked revenue**; then **1% of MTR above** the threshold — a small % of money already being made.
4. **Android v1.1 readiness** with the same entitlement abstraction.

**Choose Unity IAP instead if** the Owner prioritizes **zero third-party runtime dependency / zero eventual fee / everything first-party.** For 2 non-subscription SKUs this is sufficient: StoreKit 2 gives automatic local validation, restore is built in, and the OR-entitlement is a few lines persisted in Supabase (optional JWS server check via an edge function). Most of RevenueCat's value (subscription lifecycle, MRR/churn) is unused here — so this is a leaner-dependency, strictly-$0 path, at the cost of writing/maintaining the validation + entitlement + analytics glue yourself.

**Decision rule for the ADR:** default RevenueCat (minimizes code + maintenance, free at our scale); pick Unity IAP if the Owner weights "no external runtime dependency and no eventual fee" above saved glue code.

## Comparison

| Dimension | RevenueCat | Unity IAP (UGS) |
|---|---|---|
| Cost / fees | Free ≤ **$2,500 MTR/mo**; then **1% of MTR** above (Pro). ~1.2–1.4% effective vs net | **Free.** No Unity fee/revenue share on native App Store IAP |
| Server-side validation | **Managed, built-in** | Not managed; StoreKit 2 local validation, you build server-side (e.g. Supabase edge fn verifying JWS) |
| Entitlements (own-either) | **First-class** — one entitlement mapped to both SKUs, single runtime check | None — you write/persist the OR-logic (trivial) |
| Restore | Built-in + cross-account transfer | Built-in API (Apple requires the button either way) |
| Analytics | Free dashboard (revenue, conversion, cohorts) | Not included; bring your own |
| Webhooks | Yes → push to Supabase to flip the cap | None native; emit your own |
| Cross-platform (Android v1.1) | Strong — one abstraction, purchases sync | One API, entitlement/sync logic still yours |
| StoreKit 2 | Yes (purchases-unity v9.x → purchases-ios v5+) | Yes (UGS pkg 5.4.3 for 6000.5 asserts StoreKit v2) |
| SDK maturity / setup | Mature; OpenUPM + EDM4U; Editor unsupported (test on device) | In-engine, no third-party account; early 5.x StoreKit 2 had bugs |
| Dependency / lock-in | Adds a third-party runtime SDK + SaaS in the path (migratable) | Fully first-party to Unity |

## Gotchas to capture in the ADR
- **RevenueCat:** set the App Store **In-App Purchase Key** or StoreKit 2 transactions silently fail to record; configure each SKU as **non-consumable** (not consumable) or restore breaks in v9+; Editor unsupported (test on device).
- **Unity IAP:** you own server-side validation + entitlement persistence; use a **post-5.4 patch** clear of the early-5.x StoreKit 2 duplicate-receipt bug; historically slower vendor support.
- **Both:** EDM4U dependency management; a visible **Restore Purchases** control is an Apple requirement.

## Uncertainty
- RevenueCat's **1% / $2,500 MTR** terms read from the pricing page on 2026-09-17; tiers have changed before — re-confirm at build time.
- Unity IAP's exact StoreKit 2 patch status varies by package version; validate against the version you install.

## Sources (accessed 2026-09-17)
- RevenueCat pricing — https://www.revenuecat.com/pricing/
- RevenueCat Unity install — https://www.revenuecat.com/docs/getting-started/installation/unity
- RevenueCat infrastructure / webhooks — https://www.revenuecat.com/feature/infrastructure · https://www.revenuecat.com/integrations/webhooks
- Unity IAP manual (6000.5, pkg 5.4.3) — https://docs.unity3d.com/6000.5/Documentation/Manual/com.unity.purchasing.html
- Unity IAP stores supported (StoreKit v2) — https://docs.unity.com/ugs/en-us/manual/iap/manual/stores-supported
- Unity IAP receipt validation — https://docs.unity.com/en-us/iap/receipt-validation
