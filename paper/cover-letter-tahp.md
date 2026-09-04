# Cover Letter — Tropical Animal Health and Production

28 August 2026

To the Editor-in-Chief
Tropical Animal Health and Production
Springer

Dear Editor-in-Chief,

We submit our manuscript entitled **"Real-Time Multi-Behavior Detection of Group-Housed Pigs on Edge Devices: Class-Imbalance-Aware Sampling and a Lightweight FasterNet Backbone"** for consideration as a Regular Article in Tropical Animal Health and Production. The manuscript is not under consideration elsewhere, and all authors have approved this submission.

**Why this work fits the journal.** Continuous behavior monitoring is one of the most practical instruments of animal health and welfare management in pig production, and camera-based detection is the only approach that scales to commercial herds without contacting the animals. Our work answers a question that matters directly to farm health management: *which welfare-relevant behaviors can a detector actually catch, reliably, on hardware a farm can afford?* We show that the binding constraint is not model capacity but data imbalance—rare, welfare-critical behaviors (fighting, drinking, brief social contacts) are exactly the ones uniform training overlooks—and that a simple, zero-cost sampling intervention recovers them: the average precision of the rare behavior *active* rises from 0.526 to 0.639 on the held-out test set, and overall recall improves by 2.1 points on the validation set, with three-seed statistics reported for every claim.

**What we contribute to animal production practice.** (1) A deployable detection framework covering ten behaviors of group-housed pigs, validated end-to-end on a ≈7 W edge computer (Jetson Nano) at 19.7–33.3 FPS—real-time for welfare alerting, whose events unfold over seconds—sustained over 12,000 consecutive inferences without thermal throttling. (2) An honest operating envelope: a sequence-disjoint stress test and zero-shot evaluation on an independent farm dataset quantify where the framework works and where cross-farm adaptation is still needed—information practitioners need before trusting any such system. (3) A fully open protocol: code, configurations, training logs, and final weights are public (GitHub + Zenodo DOI), so the results are reproducible and the model is deployable as-is.

We believe this combination of welfare relevance, measured deployability, and transparent evaluation fits the journal's readership in tropical and subtropical animal health and production, where cost-constrained hardware is the norm rather than the exception.

**Declarations.** The study used only publicly available, non-invasively acquired video data; no animal experiments were performed by the authors and no ethics approval was required. The authors declare no competing interests and received no specific funding. AI tools were used for language polishing and code assistance; all experiments, measurements, and reported numbers were produced and verified by the authors.

Sincerely,

Zhan Zhang and Linlin Gou
School of Biological Science and Technology, Liupanshui Normal University, Liupanshui 553000, China
Corresponding author: Zhan Zhang, e-mail: 851709772@qq.com
