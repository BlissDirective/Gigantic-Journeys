# `ADRs/`

Architecture decision records: one file per decision, numbered `NNNN-slug.md`, never edited after acceptance (superseded by a new ADR instead). Template: `0000-template.md`.

An ADR is required for any architecture or vendor change, anything in the plan's human gates (plan §5), and any choice that a later milestone would find expensive to reverse (engine, backend, reconstruction vendor, package format, movement architecture, IAP provider).

Creating or changing an ADR is an AUTH (design-change): the PR cites `APPROVED #n`. ADRs 0001–0004 record decisions the Owner had already made in the kit, plan, Bible, and AUTH #001; they were created under AUTH #000.

| ADR | Title | Status |
|---|---|---|
| 0001 | Engine and rendering: Unity 6, URP, Gaussian splat renderer | Accepted (recorded) |
| 0002 | Backend: Supabase, Vercel, Inngest; the secrets model | Accepted (recorded) |
| 0003 | Reconstruction and avatar via third-party APIs; vendor-neutral package | Accepted (recorded) |
| 0004 | Movement architecture: five assemblies, motion matching spike, motion warping | Accepted (recorded) |
