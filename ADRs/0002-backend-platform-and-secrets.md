# ADR-0002: Backend: Supabase, Vercel, Inngest; the secrets model

Date: 2026-09-15 · Status: Accepted (recorded from plan §1, kit §0 and §3.5) · Authorization: APPROVED #000 · Owner Bot: gj-platform

## Context
A small team needs auth, Postgres, storage, edge functions, an API surface, and durable multi-step workflows for scan → reconstruct → scene graph → journey → package, with vendor timeouts retried rather than stalling the pipeline.

## Decision
Supabase for auth, Postgres (RLS on every table), storage, and edge functions; Vercel for API functions; Inngest for durable workflows. Secrets model (kit §0): keys live in the Bot VM's `.env.local` and the Bot credential store for staging, and in GitHub Actions secrets for CI; production Supabase service key, Apple signing certificates, and payment credentials are CI-only and never held by a Bot.

## Alternatives considered
- Firebase: weaker relational model and RLS story for the ranking and moderation tables.
- Self-hosted Postgres plus a queue: more ops than the team can carry in 16 weeks.

## Consequences
RLS-by-default is enforced in CI (`supabase/scripts/check_rls.py`). Packages are served only through signed URLs behind a CDN. Every account (Supabase, Vercel, Inngest) needs an AUTH before creation.

## Follow-ups
M0-PIPE-01, M0-PLAT-01, M0-DATA-01.
