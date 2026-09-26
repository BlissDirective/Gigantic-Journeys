# gj-data — Resources

The annotated research list for the data hat. Research focus is from the kit §3 role block: game telemetry analysis, UGC moderation systems, privacy-preserving ML on user data, active learning from corrections, and leaderboard anti-cheat. Ranking and anti-gaming get their own group because M4-DATA-02 and SECURITY_CHECKLIST §10.2 gate them. Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26: HTTP 200 plus a page-title check, and arXiv titles matched against the arXiv API. Vendor links (vision moderation APIs, analytics, rate-limit services) are references, not approvals. No moderation vendor is chosen (M4-DATA-03), and any vendor, account or paid tier needs an ADR and an AUTH (`agents/grok/README.md` §6; REVIEW_RUBRIC B3, H1). Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first: SPEC §3.7, §3.9, §7, §8 (M6); `design/proposals/publish-browse-rank-moderation-v1.md`; SECURITY_CHECKLIST §10; `data/reports/README.md`, `data/schemas/README.md`, `services/moderation/README.md`, `ml/README.md`; tickets M0-DATA-01, M4-DATA-01/02/03, M4-GAME-02.

## A. Game telemetry analysis and the weekly report

1. **GameAnalytics — Documentation** — <https://docs.gameanalytics.com/> · *vendor guide* — Event taxonomy (progression, design, error events) to compare against the frozen catalogue (M0-DATA-01).
2. **Unity Gaming Services — Analytics overview** — <https://docs.unity.com/ugs/manual/analytics/manual/overview> · *vendor guide* — How a Unity-native analytics stack structures standard vs custom events.
3. **PostHog — Funnels** — <https://posthog.com/docs/product-analytics/funnels> · *doc* — Funnel construction for scan → summit → route → publish conversion in the weekly report.
4. **PostHog — Retention** — <https://posthog.com/docs/product-analytics/retention> · *doc* — Cohort retention tables for the weekly report.
5. **Mixpanel — Funnels** — <https://docs.mixpanel.com/docs/reports/funnels> · *doc* — Funnel conversion windows and step ordering conventions.
6. **Evan Miller — How not to run an A/B test** — <https://www.evanmiller.org/how-not-to-run-an-ab-test.html> · *doc* — Peeking bias; relevant when weekly numbers are used to tune ranking weights.
7. **lifelines — survival analysis in Python** — <https://lifelines.readthedocs.io/> · *repo* — Kaplan–Meier curves for time-to-quit and time-to-summit per environment.
8. **statsmodels — proportion confidence intervals** — <https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html> · *doc* — Wilson intervals on completion rates so small environments aren't over-read.
9. **pandas documentation** — <https://pandas.pydata.org/docs/> · *doc* — Aggregation and pivot tables for the weekly report scripts.
10. **DuckDB documentation** — <https://duckdb.org/docs/> · *doc* — Fast local SQL over exported aggregates without a warehouse or a new vendor.
11. **Polars documentation** — <https://docs.pola.rs/> · *doc* — Lazy, memory-efficient aggregation for larger event exports.
12. **Matplotlib — hexbin** — <https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hexbin.html> · *doc* — Fall/stuck heatmaps over env-local A-unit positions (the role's weekly heatmaps).
13. **PostgreSQL — Window functions tutorial** — <https://www.postgresql.org/docs/current/tutorial-window.html> · *doc* — Per-environment and per-route rollups directly in Supabase.
14. **PostgreSQL — Materialized views** — <https://www.postgresql.org/docs/current/rules-materializedviews.html> · *doc* — Precomputed weekly aggregates the report reads instead of raw events.
15. **Supabase — Read replicas** — <https://supabase.com/docs/guides/platform/read-replicas> · *doc* — The DEVELOPMENT_PLAN's "read-only replica" for analysis (a paid feature: AUTH first).
16. **JSON Schema** — <https://json-schema.org/> · *doc* — The 2020-12 dialect the frozen telemetry schemas use (data/schemas/README.md).
17. **python-jsonschema** — <https://python-jsonschema.readthedocs.io/> · *repo* — Validate every exported event against the frozen schema before analysis.
18. **Census Bureau — Disclosure avoidance** — <https://www.census.gov/topics/research/disclosure-avoidance.html> · *doc* — Small-cell suppression practice for aggregates-only reports (data/reports/README.md).
19. **k-anonymity (Wikipedia)** — <https://en.wikipedia.org/wiki/K-anonymity> · *doc* — Why tiny cohorts in a report can re-identify a player; set a minimum cell size.

## B. Ranking, rating aggregation and anti-gaming

20. **Evan Miller — How not to sort by average rating** — <https://www.evanmiller.org/how-not-to-sort-by-average-rating.html> · *doc* — Lower-bound scoring so a single 5-star vote can't top the feed.
21. **Evan Miller — Bayesian average ratings** — <https://www.evanmiller.org/bayesian-average-ratings.html> · *doc* — Priors for four-axis ratings on environments with few votes.
22. **Evan Miller — Ranking items with star ratings** — <https://www.evanmiller.org/ranking-items-with-star-ratings.html> · *doc* — Multi-level (5-segment) rating aggregation, matching decision 8's rating rows.
23. **Wilson score interval (Wikipedia)** — <https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval> · *doc* — Confidence bounds for completion and replay rates in the blend.
24. **Steam — User Reviews Revisited (off-topic review bombs)** — <https://steamcommunity.com/games/593110/announcements/detail/1808664240333155775> · *postmortem* — How Steam detects and handles brigades: model for "brigade detection" in M4-DATA-02.
25. **SybilRank (NSDI 2012)** — <https://www.usenix.org/conference/nsdi12/technical-sessions/presentation/cao> · *paper* — Graph-based fake-account detection; ideas for down-weighting untrusted raters.
26. **BIRDNEST: Bayesian inference for ratings-fraud detection** — <https://arxiv.org/abs/1511.06030> · *paper* — Detects suspicious rating bursts and skewed distributions, the rate-spam pattern.
27. **Stripe — Scaling your API with rate limiters** — <https://stripe.com/blog/rate-limiters> · *doc* — Token-bucket and concurrent limiters for ratings/reports/time submissions (§10.2).
28. **Cloudflare — What is rate limiting** — <https://www.cloudflare.com/learning/bots/what-is-rate-limiting/> · *doc* — Rate-limit concepts and bypass patterns (rotating IPs, many accounts).
29. **Supabase — Auth rate limits** — <https://supabase.com/docs/guides/auth/rate-limits> · *doc* — Built-in limits that bound account farming for rating spam.
30. **Upstash ratelimit (JS)** — <https://github.com/upstash/ratelimit-js> · *repo* — Reference sliding-window implementation (a pattern reference, not an approved vendor).
31. **Apple — DeviceCheck** — <https://developer.apple.com/documentation/devicecheck> · *doc* — Per-device bits for "per device" rate limits without device IDs in telemetry (§10.1).
32. **Apple — Establishing your app's integrity (App Attest)** — <https://developer.apple.com/documentation/devicecheck/establishing-your-app-s-integrity> · *doc* — Attest that ratings and times come from a genuine app instance.
33. **scikit-learn — Outlier detection** — <https://scikit-learn.org/stable/modules/outlier_detection.html> · *doc* — Isolation forest / LOF for anomalous rating accounts in the spam test.
34. **Median absolute deviation (Wikipedia)** — <https://en.wikipedia.org/wiki/Median_absolute_deviation> · *doc* — Robust spread for flagging rating bursts without being fooled by the burst itself.
35. **Google — Rules of Machine Learning** — <https://developers.google.com/machine-learning/guides/rules-of-ml> · *doc* — Start with simple heuristics and a tunable blend before any learned ranker.

## C. UGC moderation systems and trust and safety

36. **App Store Review Guidelines — 1.2 User-generated content** — <https://developer.apple.com/app-store/review/guidelines/#user-generated-content> · *doc* — The four pillars the moderation pipeline must satisfy (SECURITY_CHECKLIST §10.5).
37. **Santa Clara Principles** — <https://santaclaraprinciples.org/> · *doc* — Notice, reasons and appeal: backs the one-line rejection reason + Appeal (decision 8).
38. **Trust & Safety Professional Association — T&S fundamentals** — <https://www.tspa.org/curriculum/ts-fundamentals/> · *doc* — Queue operations, policy writing and escalation fundamentals.
39. **Tech Coalition** — <https://www.technologycoalition.org/> · *doc* — Industry practice on child-safety detection and reporting.
40. **NCMEC — CyberTipline** — <https://www.missingkids.org/gethelpnow/cybertipline> · *doc* — Where illegal-content escalation goes (proposal §1 "escalation to authorities").
41. **Microsoft PhotoDNA** — <https://www.microsoft.com/en-us/photodna> · *vendor guide* — Hash-matching for known illegal imagery; a candidate for the vision pass (vendor TBD).
42. **Thorn — Safer** — <https://safer.io/> · *vendor guide* — CSAM detection for platforms; another candidate to evaluate under an AUTH.
43. **Meta ThreatExchange (PDQ/TMK hashing)** — <https://github.com/facebook/ThreatExchange> · *repo* — Open perceptual hashing for image/video matching without sharing media.
44. **Google Cloud Vision — SafeSearch detection** — <https://cloud.google.com/vision/docs/detecting-safe-search> · *vendor guide* — Likelihood-graded adult/violence labels; a vision-pass option (vendor TBD, M4-DATA-03).
45. **Amazon Rekognition — Content moderation** — <https://docs.aws.amazon.com/rekognition/latest/dg/moderation.html> · *vendor guide* — Hierarchical moderation labels with confidence thresholds.
46. **Azure AI Content Safety** — <https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview> · *vendor guide* — Severity-graded image moderation with human-review workflows.
47. **LAION CLIP-based NSFW detector** — <https://github.com/LAION-AI/CLIP-based-NSFW-Detector> · *repo* — A self-hostable baseline that fits the "our own infrastructure" posture (SPEC §3.9).
48. **OpenCLIP** — <https://github.com/mlfoundations/open_clip> · *repo* — Open CLIP models for zero-shot checks like "not a real place" and "private information visible".
49. **Learning Transferable Visual Models From Natural Language Supervision (CLIP)** — <https://arxiv.org/abs/2103.00020> · *paper* — Why zero-shot image–text scoring can cover custom report reasons.
50. **EU Digital Services Act** — <https://digital-strategy.ec.europa.eu/en/policies/digital-services-act-package> · *doc* — Notice-and-action and statement-of-reasons duties if GJ ships in the EU.
51. **UK Online Safety Act** — <https://www.gov.uk/government/collections/online-safety-act> · *doc* — UGC-service duties relevant to a UK launch.
52. **Roblox Community Standards** — <https://en.help.roblox.com/hc/en-us/articles/203313410-Roblox-Community-Standards> · *doc* — A UGC game's public policy; model for GJ's report reasons and actions.
53. **Grimmelmann — The Virtues of Moderation** — <https://scholarship.law.cornell.edu/facpub/1486/> · *paper* — Taxonomy of moderation techniques (exclusion, pricing, organizing, norm-setting).

## D. Leaderboard anti-cheat and time plausibility

54. **Apple — Game Center** — <https://developer.apple.com/game-center/> · *doc* — Platform leaderboards; GJ runs its own validated board, so know what Game Center does and doesn't check.
55. **Apple GameKit — Leaderboards** — <https://developer.apple.com/documentation/gamekit/encourage-progress-and-competition-with-leaderboards> · *doc* — Score submission semantics and limits.
56. **Steamworks — Leaderboards** — <https://partner.steamgames.com/doc/features/leaderboards> · *doc* — Trusted vs client-submitted scores: the core anti-cheat decision.
57. **Unity Gaming Services — Leaderboards** — <https://docs.unity.com/ugs/manual/leaderboards/manual/leaderboards> · *vendor guide* — Server-side score validation hooks (pattern reference; not an approved vendor).
58. **Unity Gaming Services — Cloud Code** — <https://docs.unity.com/ugs/manual/cloud-code/manual> · *vendor guide* — Server-authoritative validation pattern for submitted times.
59. **Gabriel Gambetta — Client-server game architecture** — <https://www.gabrielgambetta.com/client-server-game-architecture.html> · *doc* — "Never trust the client": why times must clear the server-side validator (§10.3).
60. **Glenn Fiedler — Deterministic lockstep** — <https://gafferongames.com/post/deterministic_lockstep/> · *doc* — Input-replay determinism; groundwork for ghost-replay verification (proposal §9.3 depth).
61. **OWASP MASVS** — <https://mas.owasp.org/MASVS/> · *doc* — MASVS-RESILIENCE: tamper and runtime-integrity controls behind trustworthy submissions.
62. **OWASP MASTG** — <https://mas.owasp.org/MASTG/> · *doc* — Test cases for tampering, hooking and memory editing that fake times rely on.

## E. Privacy-preserving data and ML on user data

63. **NIST Privacy Framework** — <https://www.nist.gov/privacy-framework> · *doc* — Structure for data-minimization decisions around telemetry and training data.
64. **NIST SP 800-188 — De-identifying government datasets** — <https://csrc.nist.gov/pubs/sp/800/188/final> · *doc* — De-identification techniques and their limits for exported aggregates.
65. **GDPR Art. 5 — Principles** — <https://gdpr-info.eu/art-5-gdpr/> · *doc* — Purpose limitation and minimization: training on derived data only, opt-in (SPEC §3.9).
66. **GDPR Art. 17 — Right to erasure** — <https://gdpr-info.eu/art-17-gdpr/> · *doc* — Delete-all must remove past correction contributions (SPEC §7).
67. **GDPR Art. 25 — Data protection by design** — <https://gdpr-info.eu/art-25-gdpr/> · *doc* — The legal basis for the forbidden-field schema test (§10.1).
68. **California — CCPA** — <https://oag.ca.gov/privacy/ccpa> · *doc* — US consumer rights to know and delete that the opt-in toggle and delete-all serve.
69. **The Algorithmic Foundations of Differential Privacy** — <https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf> · *paper* — The DP reference if aggregate releases or training ever need formal guarantees.
70. **Apple — Differential Privacy Overview** — <https://www.apple.com/privacy/docs/Differential_Privacy_Overview.pdf> · *doc* — How Apple collects usage aggregates privately; a model for "aggregates only".
71. **Deep Learning with Differential Privacy** — <https://arxiv.org/abs/1607.00133> · *paper* — DP-SGD, the technique if the surface classifier trains on user-derived data.
72. **Communication-Efficient Learning of Deep Networks from Decentralized Data** — <https://arxiv.org/abs/1602.05629> · *paper* — Federated averaging: an option if derived data should never leave devices.
73. **Membership Inference Attacks against Machine Learning Models** — <https://arxiv.org/abs/1610.05820> · *paper* — Why a model trained on user environments can leak who contributed.
74. **Machine Unlearning** — <https://arxiv.org/abs/1912.03817> · *paper* — SISA training so opt-out/delete-all can remove a user's influence without full retrains.
75. **OpenDP** — <https://github.com/opendp/opendp> · *repo* — Open DP library for private aggregate statistics.
76. **Google differential-privacy** — <https://github.com/google/differential-privacy> · *repo* — Production DP aggregation primitives.
77. **Opacus** — <https://opacus.ai/> · *repo* — DP-SGD for PyTorch.
78. **TensorFlow Privacy** — <https://github.com/tensorflow/privacy> · *repo* — DP training plus membership-inference testing tools.
79. **Datasheets for Datasets** — <https://arxiv.org/abs/1803.09010> · *paper* — Document the opt-in correction dataset: provenance, consent, exclusions.
80. **Model Cards for Model Reporting** — <https://arxiv.org/abs/1810.03993> · *paper* — Report each retrain's metrics and limits (M6 before/after on the held-out corpus).

## F. Active learning, correction curation and retraining

81. **Active Learning Literature Survey (Settles)** — <https://burrsettles.com/pub/settles.activelearning.pdf> · *paper* — The classic survey: uncertainty, query-by-committee and expected-error sampling.
82. **A Survey of Deep Active Learning** — <https://arxiv.org/abs/2009.00236> · *paper* — Modern deep-model active learning strategies and pitfalls.
83. **Deep Bayesian Active Learning with Image Data** — <https://arxiv.org/abs/1703.02910> · *paper* — MC-dropout uncertainty to prioritize which surfaces to ask users about.
84. **Active Learning for Convolutional Neural Networks: A Core-Set Approach** — <https://arxiv.org/abs/1708.00489> · *paper* — Diversity sampling so corrections don't all come from one room type.
85. **Learning Loss for Active Learning** — <https://arxiv.org/abs/1905.03677> · *paper* — Predicting loss to choose informative samples.
86. **ReDAL: Region-based and Diversity-aware Active Learning for Point Cloud Semantic Segmentation** — <https://arxiv.org/abs/2107.11769> · *paper* — Region-level queries on 3D scenes, close to per-surface corrections.
87. **SQN: Weakly-Supervised Semantic Segmentation of Large-Scale 3D Point Clouds** — <https://arxiv.org/abs/2104.04891> · *paper* — Learns 3D segmentation from very sparse point labels, the regime one-tap "fix this label" corrections produce.
88. **Confident Learning: Estimating Uncertainty in Dataset Labels** — <https://arxiv.org/abs/1911.00068> · *paper* — Find wrong user corrections before they enter training.
89. **Learning from Noisy Labels with Deep Neural Networks: A Survey** — <https://arxiv.org/abs/2007.08199> · *paper* — Robust losses and filtering for crowd-sourced label noise.
90. **Data Programming: Creating Large Training Sets, Quickly** — <https://arxiv.org/abs/1605.07723> · *paper* — Weak supervision: combine corrections with validator heuristics as labelling functions.
91. **Poisoning Attacks against Support Vector Machines** — <https://arxiv.org/abs/1206.6389> · *paper* — Why malicious corrections are an attack surface for retraining.
92. **Certified Defenses for Data Poisoning Attacks** — <https://arxiv.org/abs/1706.03691> · *paper* — Bounding the damage a fraction of bad corrections can do.
93. **Overcoming catastrophic forgetting in neural networks** — <https://arxiv.org/abs/1612.00796> · *paper* — EWC; keep old classes working when retraining on new correction data.
94. **ScanNet** — <https://arxiv.org/abs/1702.04405> · *paper* — Indoor semantic benchmark; class taxonomy comparison for Bible §4 surface classes.
95. **ScanNet++** — <https://arxiv.org/abs/2308.11417> · *paper* — High-fidelity indoor scans with dense semantics; a held-out-style evaluation reference.
96. **PointNet++** — <https://arxiv.org/abs/1706.02413> · *paper* — Point-cloud segmentation baseline for the surface classifier.
97. **Mask3D** — <https://arxiv.org/abs/2210.03105> · *paper* — Transformer 3D instance segmentation for surface/object labels.
98. **OpenScene** — <https://arxiv.org/abs/2211.15654> · *paper* — Open-vocabulary 3D labels that corrections could refine.
99. **Segment Anything** — <https://arxiv.org/abs/2304.02643> · *paper* — 2D masks lifted to 3D for surface proposals; context for scene-graph models.
100. **cleanlab** — <https://github.com/cleanlab/cleanlab> · *repo* — Confident-learning implementation to audit correction labels.
101. **modAL** — <https://github.com/modAL-python/modAL> · *repo* — Active-learning loop scaffolding in Python.
102. **Label Studio** — <https://labelstud.io/> · *repo* — Self-hostable labelling UI for internal review of disputed corrections.
103. **CVAT** — <https://github.com/cvat-ai/cvat> · *repo* — Open annotation tool, including 3D point clouds.
104. **scikit-learn — GroupKFold** — <https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html> · *doc* — Split by environment so the held-out corpus never leaks into training.
105. **scikit-learn — Probability calibration** — <https://scikit-learn.org/stable/modules/calibration.html> · *doc* — Calibrated confidence for the classifier and the vision pass's low-confidence routing.
106. **scikit-learn — Model evaluation** — <https://scikit-learn.org/stable/modules/model_evaluation.html> · *doc* — Per-class precision/recall/F1 for before/after retrain reports.
107. **MLflow documentation** — <https://mlflow.org/docs/latest/index.html> · *doc* — Track retrain runs, datasets and metrics reproducibly.
108. **DVC documentation** — <https://dvc.org/doc> · *doc* — Version derived training datasets so a user's deletion can be traced to data versions.
