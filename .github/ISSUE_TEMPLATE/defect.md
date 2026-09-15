---
name: DEFECT (QA)
about: Visual or functional defect found by gj-qa-release during a PR pass or device run.
title: "DEFECT: <ticket id> — <one line>"
labels: ["defect", "qa"]
---

**Ticket / PR:** `M0-XXXX-NN` / #
**Build:** branch + short SHA
**Device:** model, OS version (state if it is the reference Android device)

**Steps to reproduce:**
1.
2.

**Expected:**
**Actual:**

**Evidence:** screenshot path in `qa/evidence/<ticket>/` or attached clip (≤ 30 s)

**Severity:** S1 blocks the milestone exit test · S2 breaks an acceptance test · S3 visible but workaround exists · S4 cosmetic

**Design rule violated (if any):** Design Skills §3.x / DESIGN_SYSTEM.md decision n / Movement Bible §n

**Privacy check:** the evidence contains no faces, addresses, documents, or screens with personal data.
