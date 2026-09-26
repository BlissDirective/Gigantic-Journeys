# Repository settings API readback

Ticket: `M0-REPO-02`
Repository: `BlissDirective/Gigantic-Journeys`
Readback date: 2026-09-26
Owner decision: 2026-09-26 1:23 PM CT

This file contains only public repository configuration. No credentials, tokens, or secret values are recorded.

## Branch protection

Endpoint: `GET /repos/BlissDirective/Gigantic-Journeys/branches/main/protection`

```json
{
  "enforce_admins": false,
  "required_status_checks": {
    "strict": false,
    "checks": [
      {"app_id": 15368, "context": "lint gate"},
      {"app_id": 15368, "context": "gitleaks"},
      {"app_id": 15368, "context": "repo hygiene (env files, keys, raw media, size)"},
      {"app_id": 15368, "context": "tickets validate"},
      {"app_id": 15368, "context": "movement.json single source of truth"},
      {"app_id": 15368, "context": "protected paths need APPROVED"},
      {"app_id": 15368, "context": "unity tests gate"}
    ]
  },
  "required_pull_request_reviews": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

Interpretation: main is protected for pull requests; administrators are exempt, so the Owner's admin credential can still push directly. Force-pushes and branch deletion are blocked. No per-PR review requirement is configured.

## Secret scanning

Endpoint: `GET /repos/BlissDirective/Gigantic-Journeys`

```json
{
  "private": false,
  "security_and_analysis": {
    "secret_scanning": {"status": "enabled"},
    "secret_scanning_push_protection": {"status": "enabled"}
  }
}
```
