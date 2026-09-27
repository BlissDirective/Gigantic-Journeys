# Staging Supabase smoke

Run: 2026-09-27 19:28 UTC · `python supabase/scripts/staging_smoke.py` · target: STAGING project (ref redacted).
No keys, URLs, or project refs are recorded here.

| Check | Result | Detail |
|---|---|---|
| `auth.health` | PASS | HTTP 200 |
| `auth.email` | PASS | email=True mailer_autoconfirm=False |
| `auth.anonymous_off` | PASS | anonymous_users=False |
| `auth.apple` | PASS | enabled |
| `auth.google` | PASS | enabled |
| `rest.anon_select` | PASS | HTTP 200, rows=0 |
| `rest.anon_insert` | PASS | HTTP 401 42501 |
| `storage.bucket` | PASS | HTTP 200 public=False |
| `storage.public_url` | PASS | HTTP 400 (must not be 200) |
| `db.rls_every_table` | PASS | 1 app table(s), all RLS + policy |
| `db.migrations` | PASS | 1 applied |
| `fn.environment_urls` | PASS | HTTP 401 without user JWT |

Totals: 12 PASS · 0 FAIL · 0 PENDING
