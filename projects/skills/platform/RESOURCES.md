# gj-platform — Resources

The annotated research list for the platform hat. Research focus is from kit §3: Supabase RLS patterns, Inngest, mobile backend security, CDN for large assets, event schema design, and privacy-by-design. Storage/signed URLs and deletion/metadata stripping get their own groups because SECURITY_CHECKLIST §3, §4 and §6 gate them. Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26: HTTP 200 plus a page-title check. Vendor links are references, not approvals. Any new account, CDN, storage vendor or paid tier needs an ADR and an AUTH (ADR-0002; SECURITY_CHECKLIST §8.6). Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first: `ADRs/0002-backend-platform-and-secrets.md`; `supabase/README.md` and the migrations; `api/README.md`; SPEC §3.7, §3.9, §3.10, §7; SECURITY_CHECKLIST §1–§4, §6–§10; `legal/RETENTION_SCHEDULE.md`.

## A. Supabase Postgres, RLS and auth

1. **Supabase — Postgres roles** — <https://supabase.com/docs/guides/database/postgres/roles> · *doc* — anon, authenticated and service_role: who each policy targets.
2. **Supabase — pg_cron** — <https://supabase.com/docs/guides/database/extensions/pg_cron> · *doc* — Scheduled purges (failed jobs ≤ 7 days, §6.1) and the weekly public-bucket audit (§3.4).
3. **Supabase — Database backups** — <https://supabase.com/docs/guides/platform/backups> · *doc* — Backup windows decide when "deleted" is really deleted (open counsel item in legal/RETENTION_SCHEDULE.md §4).
4. **Supabase — Custom claims and role-based access control** — <https://supabase.com/docs/guides/database/postgres/custom-claims-and-role-based-access-control-rbac> · *doc* — Moderator/admin roles via JWT claims for the moderation queue (M4-DATA-01).
5. **Supabase — Row Level Security** — <https://supabase.com/docs/guides/database/postgres/row-level-security> · *doc* — The canonical RLS guide; owner-only and published-read patterns (SECURITY_CHECKLIST §2.2).
6. **Supabase — RLS performance recommendations** — <https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv> · *doc* — Wrap auth.uid() in a select and index policy columns; keeps browse queries fast under RLS.
7. **Supabase — Securing your API** — <https://supabase.com/docs/guides/api/securing-your-api> · *doc* — Why the anon key is safe only with RLS on every exposed table (§2.3).
8. **Supabase — API keys (anon vs service_role)** — <https://supabase.com/docs/guides/api/api-keys> · *doc* — The key model: anon in the client, service role only server-side (§2.3, §9.1).
9. **Supabase — Database migrations** — <https://supabase.com/docs/guides/deployment/database-migrations> · *doc* — Migration workflow behind supabase/migrations and the schema_migrations record (supabase/README.md).
10. **Supabase CLI reference** — <https://supabase.com/docs/reference/cli/introduction> · *doc* — supabase start, db push and functions deploy used in local and staging work.
11. **Supabase — Local development** — <https://supabase.com/docs/guides/local-development> · *doc* — Running the stack from supabase/config.toml without project keys (M0-PLAT-01 AT-1).
12. **Supabase — Testing your database (pgTAP)** — <https://supabase.com/docs/guides/database/testing> · *doc* — Policy tests per pattern (two users + anon), suggested by §2.2.
13. **Supabase — Auth overview** — <https://supabase.com/docs/guides/auth> · *doc* — Email confirmation, anonymous sign-in off, providers (§9.3; M1-PLAT-01 AT-4).
14. **Supabase — Login with Apple** — <https://supabase.com/docs/guides/auth/social-login/auth-apple> · *doc* — Apple sign-in, pending the Owner's OAuth client (M1-PLAT-01 AT-4).
15. **Supabase — Login with Google** — <https://supabase.com/docs/guides/auth/social-login/auth-google> · *doc* — Google sign-in, also pending the Owner.
16. **Supabase — Auth JWTs** — <https://supabase.com/docs/guides/auth/jwts> · *doc* — How auth.uid() comes from the JWT that edge functions verify (verify_jwt = true).
17. **Supabase — Database functions and security definer** — <https://supabase.com/docs/guides/database/functions> · *doc* — When a security-definer function bypasses RLS and how to lock its search_path.
18. **Supabase — Database advisors (security lints)** — <https://supabase.com/docs/guides/database/database-advisors> · *doc* — Built-in lints for RLS-disabled tables and unsafe functions; a second net behind check_rls.py.
19. **Supabase — Going into production checklist** — <https://supabase.com/docs/guides/deployment/going-into-prod> · *doc* — Pre-launch settings (SSL, network restrictions, rate limits) for M5.
20. **Supabase — Rate limits (Auth)** — <https://supabase.com/docs/guides/auth/rate-limits> · *doc* — Built-in auth rate limits; ratings/reports need their own (M4-DATA-01 AT-3).
21. **PostgreSQL — Row Security Policies** — <https://www.postgresql.org/docs/current/ddl-rowsecurity.html> · *doc* — The engine semantics: USING vs WITH CHECK, permissive vs restrictive, FORCE RLS.
22. **PostgreSQL — CREATE POLICY** — <https://www.postgresql.org/docs/current/sql-createpolicy.html> · *doc* — Exact syntax that check_rls.py looks for in each migration.
23. **PostgreSQL — Check constraints** — <https://www.postgresql.org/docs/current/ddl-constraints.html> · *doc* — Database-level invariants like environments_published_requires_cleared.
24. **pgTAP** — <https://pgtap.org/> · *doc* — Unit-testing framework for Postgres policies and constraints.
25. **Supabase GitHub** — <https://github.com/supabase/supabase> · *repo* — Source and issues for platform behaviour questions.

## B. Storage, signed URLs and edge functions

26. **Supabase — Delete storage objects** — <https://supabase.com/docs/guides/storage/management/delete-objects> · *doc* — Deleting objects via the API (not SQL) so raw scan media is actually purged (§6.1, delete-all).
27. **Supabase — Storage access control** — <https://supabase.com/docs/guides/storage/security/access-control> · *doc* — Bucket policies on storage.objects, reviewed like table policies (§2.4).
28. **Supabase — Storage buckets fundamentals (private vs public)** — <https://supabase.com/docs/guides/storage/buckets/fundamentals> · *doc* — Private by default; public buckets only if an ADR names them (§3.4).
29. **Supabase JS — createSignedUrl** — <https://supabase.com/docs/reference/javascript/storage-from-createsignedurl> · *doc* — The call environment-urls uses with TTL_SECONDS = 900 (§3.1).
30. **Supabase — Resumable uploads (TUS)** — <https://supabase.com/docs/guides/storage/uploads/resumable-uploads> · *doc* — Large capture-bundle uploads that survive flaky mobile networks.
31. **Supabase — Storage CDN** — <https://supabase.com/docs/guides/storage/cdn/fundamentals> · *doc* — How Supabase's CDN caches objects and what that means for signed URLs (§3.3).
32. **Supabase — Edge Functions** — <https://supabase.com/docs/guides/functions> · *doc* — Runtime for environment-urls; server-side authz before any URL is issued.
33. **Supabase — Edge Functions auth** — <https://supabase.com/docs/guides/functions/auth> · *doc* — Verifying the caller's JWT and creating a client as the caller so RLS applies.
34. **Supabase — Edge Function secrets** — <https://supabase.com/docs/guides/functions/secrets> · *doc* — Where the service-role key lives server-side (never the repo, §1.3).
35. **Supabase — Image transformations** — <https://supabase.com/docs/guides/storage/serving/image-transformations> · *doc* — Thumbnail resizing on delivery; transformed output must still carry no metadata (§4.4).
36. **Supabase — Supabase Storage (S3 compatibility)** — <https://supabase.com/docs/guides/storage/s3/compatibility> · *doc* — S3 API for tooling and CDN origins.

## C. Inngest and durable workflows

37. **Inngest documentation** — <https://www.inngest.com/docs> · *doc* — The durable workflow engine behind journey/pipeline (ADR-0002, M0-PIPE-01).
38. **Inngest — Steps (step.run)** — <https://www.inngest.com/docs/learn/inngest-steps> · *doc* — Steps are memoized, so a retry resumes at the failed step (api/src/inngest/functions.ts).
39. **Inngest — Handling idempotency** — <https://www.inngest.com/docs/guides/handling-idempotency> · *doc* — Event-id and function-level idempotency keys; the M1-PIPE-01 AT-1 requirement.
40. **Inngest — Retries** — <https://www.inngest.com/docs/features/inngest-functions/error-retries/retries> · *doc* — Default retry counts and backoff for vendor failures.
41. **Inngest — Inngest errors (NonRetriableError)** — <https://www.inngest.com/docs/features/inngest-functions/error-retries/inngest-errors> · *doc* — Classified errors: stop retrying on permanent failures (REVIEW_RUBRIC E3).
42. **Inngest — Failure handlers (onFailure)** — <https://www.inngest.com/docs/features/inngest-functions/error-retries/failure-handlers> · *doc* — Mark an environment failed and trigger the free-retry handoff (M1-CAPT-02 AT-5).
43. **Inngest — Concurrency** — <https://www.inngest.com/docs/guides/concurrency> · *doc* — Cap parallel GPU reconstruction jobs to respect the $50/day cap (§8.5).
44. **Inngest — Throttling** — <https://www.inngest.com/docs/guides/throttling> · *doc* — Rate-limit starts per user so one account can't flood the pipeline.
45. **Inngest — Wait for event** — <https://www.inngest.com/docs/features/inngest-functions/steps-workflows/wait-for-event> · *doc* — Waiting for an external reconstruction callback instead of polling.
46. **Inngest — Sleep / delayed steps** — <https://www.inngest.com/docs/reference/functions/step-sleep> · *doc* — Delayed follow-ups such as the 7-day failed-job purge (§6.1).
47. **Inngest — Cancellation** — <https://www.inngest.com/docs/features/inngest-functions/cancellation> · *doc* — Cancel running jobs when a user deletes their data (deletion flow step 2).
48. **Inngest — Local development (Dev Server)** — <https://www.inngest.com/docs/local-development> · *doc* — Running the pipeline locally with no account (M0-PIPE-01).
49. **Inngest — Serve (Node)** — <https://www.inngest.com/docs/learn/serving-inngest-functions> · *doc* — How api/src/server.ts exposes functions to Inngest.
50. **Inngest — Event payload format and schemas** — <https://www.inngest.com/docs/features/events-triggers/event-format> · *doc* — Typed events (EventSchemas) for scan.submitted.
51. **Inngest — Signing keys** — <https://www.inngest.com/docs/platform/signing-keys> · *doc* — Request signing between Inngest and the API; the key lives only in .env.local and CI.
52. **Inngest JS SDK** — <https://github.com/inngest/inngest-js> · *repo* — Source for SDK behaviour; api/package.json uses the v3 SDK.
53. **Stripe — Designing robust and predictable APIs with idempotency** — <https://stripe.com/blog/idempotency> · *doc* — The classic write-up on idempotency keys and safe retries.
54. **Vercel Functions documentation** — <https://vercel.com/docs/functions> · *doc* — The API host in ADR-0002; limits and regions for the serve endpoint.
55. **Vercel — Environment variables** — <https://vercel.com/docs/environment-variables> · *doc* — Where deploy-time secrets live; never in the repo.

## D. Mobile backend security

56. **OWASP Mobile Top 10 (2024)** — <https://owasp.org/www-project-mobile-top-10/> · *doc* — The list SECURITY_CHECKLIST §9 walks, M1–M10.
57. **OWASP MASVS** — <https://mas.owasp.org/MASVS/> · *doc* — Verification standard behind the Mobile Top 10 controls.
58. **OWASP MASTG** — <https://mas.owasp.org/MASTG/> · *doc* — Testing guide for iOS app controls (storage, network, crypto).
59. **OWASP API Security Top 10 (2023)** — <https://owasp.org/API-Security/editions/2023/en/0x11-t10/> · *doc* — Broken object-level authorization is exactly what RLS prevents.
60. **OWASP ASVS (GitHub)** — <https://github.com/OWASP/ASVS> · *repo* — Server-side verification requirements for the API and edge functions.
61. **OWASP Cheat Sheet — Authorization** — <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html> · *doc* — Deny by default, check on every request (§3.2 deep links).
62. **OWASP Cheat Sheet — File Upload** — <https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html> · *doc* — Type/size validation for capture uploads (§9.4).
63. **OWASP Cheat Sheet — Secrets Management** — <https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html> · *doc* — Rotation and least privilege (§1, §8).
64. **OWASP Cheat Sheet — Logging** — <https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html> · *doc* — What never goes in logs (PII, tokens); REVIEW_RUBRIC C10.
65. **gitleaks** — <https://github.com/gitleaks/gitleaks> · *repo* — The secret scanner behind the required gitleaks check (§1.1).
66. **GitHub — Secret scanning push protection** — <https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection> · *doc* — The native layer the Owner enables (§1.6).
67. **GitHub Actions — Using secrets** — <https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions> · *doc* — CI secrets only in jobs that need them (REVIEW_RUBRIC C9).
68. **GitHub Actions — Security hardening** — <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions> · *doc* — Pinning actions and limiting token permissions (§7.1).
69. **npm audit** — <https://docs.npmjs.com/cli/v10/commands/npm-audit> · *doc* — Required clean at high and above for api/ (§7.2).
70. **pip-audit** — <https://github.com/pypa/pip-audit> · *repo* — Required for the Python scripts and services (§7.2).
71. **Apple — Sign in with Apple** — <https://developer.apple.com/sign-in-with-apple/> · *doc* — Required alongside Google sign-in (§9.3); App Store guideline 4.8 context.
72. **Apple — App Transport Security** — <https://developer.apple.com/documentation/security/preventing-insecure-network-connections> · *doc* — TLS-only networking on iOS (§9.5).

## E. CDN and large-asset delivery

73. **Cloudflare R2 documentation** — <https://developers.cloudflare.com/r2/> · *doc* — Zero-egress object storage, the cost lever the reconstruction analysis highlights.
74. **Cloudflare R2 — Presigned URLs** — <https://developers.cloudflare.com/r2/api/s3/presigned-urls/> · *doc* — Short-lived signed access if packages move to R2 (§3.1).
75. **Cloudflare — Cache and signed URLs (Workers + tokens)** — <https://developers.cloudflare.com/workers/examples/signing-requests/> · *doc* — Verifying signatures at the edge so the CDN forwards them (§3.3).
76. **Backblaze B2 — Cloud storage docs** — <https://www.backblaze.com/docs/cloud-storage> · *doc* — The other zero-egress option named in the platform handbook.
77. **Cloudflare — Bandwidth Alliance** — <https://www.cloudflare.com/bandwidth-alliance/> · *doc* — Why B2-behind-Cloudflare egress is free or discounted.
78. **AWS CloudFront — Signed URLs** — <https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html> · *doc* — Reference model for CDN-level signed URLs and key pairs.
79. **HTTP range requests (MDN)** — <https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests> · *doc* — Resumable and partial downloads of large splat packages.
80. **HTTP caching (MDN)** — <https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching> · *doc* — Cache-Control for immutable, versioned package objects.
81. **Unity — UnityWebRequest** — <https://docs.unity3d.com/ScriptReference/Networking.UnityWebRequest.html> · *doc* — How the client downloads packages from signed URLs.
82. **Unity Addressables** — <https://docs.unity3d.com/Packages/com.unity.addressables@2.3/manual/index.html> · *doc* — Remote content catalogues; weigh against a plain signed-URL download.
83. **Niantic SPZ format** — <https://github.com/nianticlabs/spz> · *repo* — Compressed splat format that shrinks packages toward the ≤ 150 MB target (SPEC §6).
84. **PlayCanvas SOG / splat-transform** — <https://github.com/playcanvas/splat-transform> · *repo* — SOG compression named in the iOS splat-render plan (M1-UNITY-01).

## F. Event schema design and freezing

85. **JSON Schema 2020-12** — <https://json-schema.org/draft/2020-12> · *doc* — The draft data/schemas uses (M0-DATA-01, M1-DATA-01).
86. **Understanding JSON Schema** — <https://json-schema.org/understanding-json-schema/> · *doc* — Practical guide: additionalProperties false, enums, formats.
87. **python-jsonschema** — <https://github.com/python-jsonschema/jsonschema> · *repo* — The validator for fixture and forbidden-field tests in pytest.
88. **Ajv JSON schema validator** — <https://ajv.js.org/> · *doc* — Validating events at ingestion in TypeScript (§9.4).
89. **Semantic Versioning 2.0.0** — <https://semver.org/> · *doc* — schema_version semver and the freeze/change rule (data/schemas/README.md).
90. **Confluent — Schema evolution and compatibility** — <https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html> · *doc* — Backward/forward compatibility rules to apply before any post-freeze change.
91. **Segment — Tracking plan best practices** — <https://segment.com/docs/protocols/tracking-plan/best-practices/> · *doc* — Naming and envelope conventions for a telemetry catalogue.
92. **CloudEvents specification** — <https://github.com/cloudevents/spec> · *repo* — A standard event envelope to compare against the GJ common envelope.
93. **Snowplow — Self-describing events and schemas** — <https://docs.snowplow.io/docs/fundamentals/schemas/> · *doc* — Versioned, validated event schemas at ingestion, the model M0-DATA-01 follows.

## G. Privacy-by-design, deletion and metadata stripping

94. **GDPR Article 17 — Right to erasure** — <https://gdpr-info.eu/art-17-gdpr/> · *doc* — Legal basis for the delete-all flow (legal/RETENTION_SCHEDULE.md §2).
95. **GDPR Article 25 — Data protection by design and by default** — <https://gdpr-info.eu/art-25-gdpr/> · *doc* — Minimization and defaults, e.g. training opt-in default off.
96. **Apple — Offering account deletion in your app** — <https://developer.apple.com/support/offering-account-deletion-in-your-app/> · *doc* — App Store requirement for in-app account deletion; shapes Settings → Delete my data.
97. **Apple — Privacy manifest files** — <https://developer.apple.com/documentation/bundleresources/privacy-manifest-files> · *doc* — Required declarations of data use and SDK API reasons.
98. **Apple — App privacy details** — <https://developer.apple.com/app-store/app-privacy-details/> · *doc* — Privacy labels must match what the backend actually collects (§9.6).
99. **Apple ImageIO — CGImageDestination (metadata control)** — <https://developer.apple.com/documentation/imageio/cgimagedestination> · *doc* — Re-encoding images on iOS without GPS/EXIF (§4.1).
100. **Apple AVFoundation — AVAssetExportSession metadata** — <https://developer.apple.com/documentation/avfoundation/avassetexportsession/metadata> · *doc* — Clearing QuickTime location atoms from video before upload (§4.1).
101. **ExifTool** — <https://exiftool.org/> · *doc* — Reference tool for server-side verification and for building GPS-injected fixtures (§4.2, §4.3).
102. **Pillow — Image.getexif** — <https://pillow.readthedocs.io/en/stable/reference/Image.html> · *doc* — Python-side EXIF inspection and stripping in fixture tests.
103. **FFmpeg — map_metadata option** — <https://ffmpeg.org/ffmpeg.html> · *doc* — Dropping container metadata from MP4/MOV server-side.
104. **NIST Privacy Framework** — <https://www.nist.gov/privacy-framework> · *doc* — A structured way to map data classes to controls for counsel review.
