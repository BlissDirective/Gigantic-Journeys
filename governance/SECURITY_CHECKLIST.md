# Security Checklist

`governance/SECURITY_CHECKLIST.md` · v1.0 · 2026-09-15 · Applied to every PR by the Coordinator and audited weekly (AUDIT). Rows are numbered for citation in reviews. **B** rows block a merge; **G** rows are milestone gates (§12); **S** rows are suggested and never block. Where a row mentions a test, the test is a suggestion (AUTH #003) and the control itself is what the row requires.

## 0. Threat model in one paragraph

The app holds two sensitive things: biometric imagery (faces, bodies) and photographic scans of people's homes. The backend holds identities, environment packages, and ratings that feed a public leaderboard. The build system holds signing keys and vendor credentials. Adversaries: a curious or malicious community member (scraping packages, spamming ratings, uploading abusive scans), a compromised Bot VM (all Bots share one computer that xAI says is not a security boundary), a leaked or public repository, and vendors' data practices. Every control below maps to one of those.

## 1. Secret hygiene

| # | Control | |
|---|---|---|
| 1.1 | Secret scanning in CI on every push and PR (gitleaks, `.gitleaks.toml`), plus a weekly full-history scan; findings fail the check. | B |
| 1.2 | No `.env*` other than `.env.example` (names only) is ever tracked; `.gitignore`, the `repo-hygiene` job, and pre-commit enforce it. | B |
| 1.3 | Secrets live only in `~/projects/gigantic-journeys/.env.local` on the Bot VM, the Bot credential store, and GitHub Actions secrets. Never in chat, tickets, issues, PR text, screenshots, logs, reports, or fixtures. | B |
| 1.4 | Production Supabase service key, Apple certificates and provisioning profiles, the Android release keystore, and payment credentials exist only in CI secrets added by the Owner. No Bot holds them. | B |
| 1.5 | Leak procedure: any secret that touched git is compromised; rotate within 1 hour; record in `governance/INCIDENTS.md` (created on first use); rewrite history only with Owner approval. | B |
| 1.6 | GitHub native secret scanning and push protection enabled on the repository (free on a public repo; Owner action M0-REPO-02). | G (M0) |

## 2. Row-Level Security on every table

| # | Control | |
|---|---|---|
| 2.1 | Every table created in a migration has `enable row level security` and at least one `create policy` in the same migration; `supabase/scripts/check_rls.py` fails CI otherwise. | B |
| 2.2 | Policy patterns: owner-only (`user_id = auth.uid()`), published-read (published and moderation cleared), service-role-only (no client policy). A test per policy (two users plus anon) is suggested. | B |
| 2.3 | The client uses only the anon key; the service-role key is used only from Inngest or edge functions on the server. | B |
| 2.4 | Storage buckets are private by default; object paths include the owner id; bucket policies are reviewed like table policies. | B |
| 2.5 | Schema changes are AUTH-gated (`data/schemas/`; migrations creating tables cite an `APPROVED #n`). | B |

## 3. Signed URLs for environment packages and media

| # | Control | |
|---|---|---|
| 3.1 | Packages, splats, meshes, avatar assets, and full-size thumbnails are delivered only through signed URLs with a TTL of 15 minutes or less, issued server-side after an authorization check. | B |
| 3.2 | Deep links resolve to an authorization check, never directly to storage. | B |
| 3.3 | The CDN forwards the signature; direct storage URLs are never exposed to the client. | B |
| 3.4 | Weekly audit lists public buckets and unsigned endpoints; the list must be empty (feed thumbnails excepted if an ADR says so). | G (M4) |

## 4. GPS and EXIF stripping

| # | Control | |
|---|---|---|
| 4.1 | Every image or video leaving the device has GPS, EXIF, XMP, and container location metadata (JPEG/HEIC EXIF, MP4/MOV QuickTime location atoms) removed on device before upload. | B |
| 4.2 | The server verifies and strips again; an upload still carrying location is rejected and counted. | B |
| 4.3 | Fixture tests covering JPEG, HEIC, MP4, and MOV with synthetically injected GPS. | S |
| 4.4 | Environment packages and thumbnails carry no location data and no capture metadata beyond what the schema allows. | B |

## 5. Biometric consent gate (BIPA and peers)

| # | Control | |
|---|---|---|
| 5.1 | No face or body photo bytes leave the device, and no vendor job is created, until a consent record exists: user id, policy version, timestamp, locale, hash of the exact consent text shown, stated retention. | B |
| 5.2 | Consent is a separate, explicit step with one plain sentence and a "learn more" sheet; never bundled into onboarding, terms, or the camera permission. | B |
| 5.3 | Training use of derived avatar data is a separate opt-in toggle, default off. | B |
| 5.4 | Withdrawal and deletion are one tap from settings and complete within 30 days, including vendor-side deletion. | B |
| 5.5 | The consent copy in `legal/` is versioned; a new version re-prompts. Illinois BIPA, Texas CUBI, and Washington MHMDA requirements are addressed in the copy and reviewed by counsel before M5. | G (M5) |
| 5.6 | Users under 13 are gated out before consent (13+ age gate). | G (M5) |

## 6. Source media deletion

| # | Control | |
|---|---|---|
| 6.1 | Raw scan video, poses, and depth are deleted from storage automatically when derived assets exist; failed jobs are deleted within 7 days. | B |
| 6.2 | Face and body photos are deleted on device, in storage, and at the vendor immediately after avatar generation; a deletion receipt (job id, timestamp, vendor response) is logged without the media. | B |
| 6.3 | Vendor retention and deletion terms (Luma; Meshy or Tripo) are on file in `legal/vendors/` before the vendor touches user data; a vendor that trains on customer data by default is not used without an opt-out in place. | G (M1, M2) |
| 6.4 | Per-user delete-all removes every data class in `SPEC.md` §7; an end-to-end run on staging is suggested. | G (M5) |
| 6.5 | Bots never handle raw user photos or video; the test corpus is Owner-supplied and consented. | B |

## 7. Dependency pinning and audit

| # | Control | |
|---|---|---|
| 7.1 | Exact pins everywhere: `==` in requirements, `package-lock.json` committed, Unity `Packages/manifest.json` with `packages-lock.json`, git packages pinned to a commit, GitHub Actions pinned to a major tag at minimum (SHA pins for third-party actions from M4). | B |
| 7.2 | `pip-audit` and `npm audit` (high and above) run in CI on every PR; Dependabot weekly. | B |
| 7.3 | A new dependency needs a one-line justification and a license compatible with a closed-source commercial app (MIT, BSD, Apache-2.0; no GPL or AGPL in the app). | B |
| 7.4 | Unity packages and asset-store purchases are recorded with version and license (Motion Warping: Climb & Interact under AUTH #001). | B |

## 8. Bot least privilege

| # | Control | |
|---|---|---|
| 8.1 | Bots authenticate to GitHub as a dedicated machine user with a fine-grained PAT scoped to this repository: Contents RW, Pull requests RW, Issues RW, Metadata R; no Administration, Secrets, Actions, Workflows, or Environments; expiry 90 days or less; rotated each milestone (AUTH #002). | G (M0) |
| 8.2 | Bots cannot merge to main (branch protection plus CODEOWNERS); only the Coordinator merges. | G (M0) |
| 8.3 | Bots hold only staging credentials (Supabase staging, vendor sandboxes where available), never production keys. | B |
| 8.4 | gj-qa-release uses a separate ops account for TestFlight and Play Console with no production secrets. | G (M5) |
| 8.5 | Vendor API keys carry per-key daily spend caps where supported; the pipeline halts at the $50/day cap (kit §7). | B |
| 8.6 | Every credential creation or rotation is an AUTH (account) and is logged. | B |

## 9. Mobile app hardening (OWASP Mobile Top 10, 2024)

| # | Item | Control |
|---|---|---|
| 9.1 | M1 Improper credential usage | No API keys in the binary; vendor calls go through the backend; Supabase anon key only. |
| 9.2 | M2 Inadequate supply chain security | §7; Unity packages from verified sources; builds reproducible in CI. |
| 9.3 | M3 Insecure authentication and authorization | Supabase Auth with Apple and Google sign-in; every server endpoint checks auth; RLS backs every query. |
| 9.4 | M4 Insufficient input and output validation | Schemas validated at ingestion (telemetry, corrections, ratings, packages); size and type limits on uploads. |
| 9.5 | M5 Insecure communication | TLS only; certificate pinning decided at M5 (ADR); no plaintext endpoints. |
| 9.6 | M6 Inadequate privacy controls | §4, §5, §6; privacy labels accurate; telemetry pseudonymous. |
| 9.7 | M7 Insufficient binary protections | IL2CPP builds; symbols stripped from release; debug overlay compiled out (`GJ_DEBUG`). |
| 9.8 | M8 Security misconfiguration | Debug endpoints, verbose logging, and test modes off in release; CI checks release flags. |
| 9.9 | M9 Insecure data storage | Local caches in the app container only; no media in shared storage; photos removed after upload. |
| 9.10 | M10 Insufficient cryptography | Platform crypto only; no home-grown schemes; signed URLs from the storage provider. |

## 10. Telemetry, moderation, and abuse

| # | Control | |
|---|---|---|
| 10.1 | Telemetry events validate against the frozen schema, which admits no GPS, email, raw media references, or user free text (a forbidden-field test is suggested). | B |
| 10.2 | Ratings and reports are rate-limited per user and device; the ranking has anti-gaming rules and passes a rate-spam test (M4 exit). | G (M4) |
| 10.3 | Leaderboard times are validated against route length and movement constants; impossible times are rejected. | G (M4) |
| 10.4 | The moderation queue shows an "Under review" state, escalates to the Owner, and gives Bots no raw media beyond the published thumbnail and package. | G (M4) |

## 11. Incident response

Contain (rotate, unpublish), record in `governance/INCIDENTS.md`, notify the Owner immediately, root-cause in the next AUDIT, add a control here via PR. Biometric-data incidents escalate to counsel.

## 12. Milestone gates (must be green at the named checkpoint)

| Checkpoint | Rows |
|---|---|
| M0 | 1.1–1.6, 8.1, 8.2 |
| M1 | 4.1–4.3 (upload path), 6.1, 6.3 (Luma), 7.1–7.2 |
| M2 | 5.1–5.4, 6.2, 6.3 (Meshy or Tripo) |
| M3 | 9.7, 9.8 (release flags) |
| M4 | 2.1–2.5, 3.1–3.4, 10.1–10.4 |
| M5 | 5.5, 5.6, 6.4, 8.4, 9.1–9.10, accurate App Store privacy labels |
