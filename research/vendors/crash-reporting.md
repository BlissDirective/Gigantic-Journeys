# Vendor research — Crash reporting (AUTH #017)

**Decision-support for AUTH #017 · observed 2026-09-17 · Coordinator research pass.** For Unity 6 / IL2CPP on iOS, privacy-strict (pseudonymous IDs, no PII — SPEC §7, SECURITY_CHECKLIST §10), cost-sensitive. Pricing/limits change; re-check the cited pages before signup. This is research, not a locked decision — the tool choice is confirmed when the Builder wires it in (an ADR notes it if the pipeline warrants).

## Recommendation

**Primary: Sentry (free Developer tier). Supplement: Apple Xcode Organizer / MetricKit (free, first-party). Fallback: Firebase Crashlytics** if Sentry's event cap binds and the Google-data dependency is acceptable.

Sentry is the only option that satisfies all three constraints at once:
- **Privacy (the deciding factor).** `sendDefaultPii = false` by default — no IP, device UUID, or user id unless explicitly opted in — which maps directly onto our no-PII telemetry posture and makes App Store privacy labels honest and minimal. EU data residency and self-hosting are available escape hatches. Crashlytics *can* be tuned toward PII-free but still sends data to Google and collects an install UUID + IP by default.
- **Directly tracks the M3 99% crash-free KPI** via Release Health (crash-free users/sessions) as a first-class metric.
- **Official Unity 6 package** with automated IL2CPP/native symbol upload; $0 for a solo dev at our scale.

**Watch item:** free **Developer** tier is ~**5k error events/mo, 1 user, 30-day retention**. Ample for a small launch, but a crash storm can exhaust it. Mitigate with server-side scrubbing + client sampling; pre-approved upgrade path is **Team (~$26/mo)** — that would need a spend AUTH.

**Why the Apple supplement:** MetricKit/Organizer is the most privacy-preserving source (first-party, on-device) and catches native/OS crashes even from users who never hit the SDK path — but it can't be primary (opted-in-users-only, 24–48h delay, no alerting, no crash-free dashboard, no Unity SDK). Wire it up once via dSYM upload to App Store Connect; a MetricKit plugin is optional and can wait.

## Comparison

| Criterion | Sentry (Unity SDK) | Firebase Crashlytics (Unity SDK) | Apple Xcode Organizer / MetricKit |
|---|---|---|---|
| Free tier / cost | Free **Developer**: ~5k errors/mo, 1 user, 30-day retention. Paid Team ~$26/mo (50k, 90-day), Business ~$80/mo | **Free & unlimited** crash events (Spark or Blaze). Strongest on raw cost | Free (included with the Apple Developer Program) |
| Unity 6 + IL2CPP iOS | Official package; auto dSYM upload via `sentry-cli`; native + C# crashes. *IL2CPP C#-line mapping imperfect for some cases; native still symbolicates.* Verify on your exact Unity version (a 6.5-beta iOS build issue is reported) | Official SDK; IL2CPP is the only iOS backend and Crashlytics symbolicates it (SDK 8.6.1+); editor plugin auto-configures dSYM upload — **lowest-friction setup** | **No Unity SDK.** Needs a native MetricKit subscriber + your own pipeline. Highest effort |
| Privacy | **Best fit.** PII off by default; server-side scrubbing on; EU residency + self-host | Configurable, **but** default install-UUID + IP, all data to Google; no EU-only guarantee | **Strongest** — first-party, on-device; but partial coverage (opted-in users only), ≥5 users/report |
| Features | Release Health (crash-free users/sessions), breadcrumbs, alerting, dashboards | Reference-grade crash-free metrics, velocity alerting, breadcrumbs, dashboards | Crash counts + logs only; no release-health dashboard, no alerting, 24–48h delay |

## Sources (observed 2026-09-17)

- Sentry pricing — https://sentry.io/pricing/
- Sentry Unity SDK — https://docs.sentry.io/platforms/unity/ · known limitations — https://docs.sentry.io/platforms/unity/troubleshooting/known-limitations/ · data collected — https://docs.sentry.io/platforms/unity/data-management/data-collected/
- Sentry scrubbing / PII / EU residency — https://docs.sentry.io/security-legal-pii/scrubbing/ · https://sentry.io/trust/privacy/
- Sentry Unity 6.5-beta iOS issue — https://discussions.unity.com/t/sentry-sdk-for-unity-doesnt-work-for-unity-6-5-beta-b8-b9-for-ios-building/1720746
- Firebase pricing — https://firebase.google.com/pricing
- Crashlytics Unity setup / IL2CPP — https://firebase.google.com/docs/crashlytics/get-started?platform=unity · https://firebase.google.com/docs/crashlytics/unity/get-deobfuscated-reports · crash-free metrics — https://firebase.google.com/docs/crashlytics/crash-free-metrics
- Crashlytics data collection & labels — https://firebase.google.com/docs/ios/app-store-data-collection · opt-in control — https://firebase.google.com/docs/crashlytics/unity/customize-crash-reports
- Apple MetricKit / Xcode Organizer — https://developer.apple.com/documentation/analytics-reports/app-crashes
