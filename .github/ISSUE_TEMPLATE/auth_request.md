---
name: AUTH REQUEST
about: Ask the Owner to authorize spend, an account, or a design/plan change. Nothing proceeds until the Owner replies APPROVED #n.
title: "AUTH REQUEST #NNN: <one line>"
labels: ["auth-request"]
assignees: ["BlissDirective"]
---

<!--
Number: the next free number after the last entry in governance/AUTHORIZATION_LOG.md and any
open auth-request issues. Keep the block below in the exact format (agents/grok/README.md §6).
One request per issue. Batch related requests by opening them together and linking them.
-->

```
AUTH REQUEST #NNN
Type: spend | account | design-change
What: <one line>
Why: <one line>
Cost: <one-time / monthly>
Reversible: yes | no
Waiting on: Owner
```

**Details** (optional, keep short): links, alternatives considered, what is blocked while waiting.

**Ticket(s) blocked:** `M0-XXXX-NN`

---

The Owner replies in this issue with `APPROVED #NNN` or `DENIED #NNN — <reason>`. The Coordinator
records the decision in `governance/AUTHORIZATION_LOG.md` and closes the issue. Nothing else unblocks it.
