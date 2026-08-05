# Cover Letter — Journal of Real-Time Image Processing

> 用途：JRTIP 投稿系统随稿上传。占位符 [ ] 投稿前填写。
> 硬性要求（审稿团 D10）：必须实质论述 real-time 问题；主动披露切分策略；提及补充材料；不点名竞品工作。

---

[Date]

To the Editor-in-Chief
Journal of Real-Time Image Processing
Springer

Dear Editor-in-Chief,

We submit our manuscript entitled **"Real-Time Multi-Behavior Detection of Group-Housed Pigs on Edge Devices: Class-Imbalance-Aware Sampling and a Lightweight FasterNet Backbone"** for consideration as an Original Research Article in the Journal of Real-Time Image Processing. The manuscript is not under consideration elsewhere, is not a revision or resubmission, and all authors have approved this submission.

**Why this work fits the journal's real-time scope.** The paper does not treat real-time performance as a benchmark afterthought; the real-time constraint is the problem formulation itself. Behavior events in commercial pig barns (fighting bouts, feeding, drinking) unfold over seconds and must be captured continuously on hardware that a farm can actually deploy at scale. We therefore ask a specifically real-time question: *what accuracy can be retained, and for which behaviors, when detection must run within the latency and power envelope of a ~5 W edge board?* The answer is validated end-to-end: the full PyTorch → ONNX → TensorRT pipeline is executed on a Jetson Nano (Maxwell GPU, TensorRT 8.2), and sustained on-device latency is measured at two operating points (50.2 ms/19.7 FPS at 640×640; 30.0 ms/33.3 FPS at 480×480, ≈5 W total board power). Both points exceed the temporal resolution that behavior monitoring requires, and the 480×480 point leaves measured headroom for multi-stream deployment—an explicit latency-versus-resolution trade-off that practitioners can tune. We also document, with measurements, three deployment realities that server-side benchmarks hide: the absence of usable INT8 acceleration on Maxwell-generation boards, TensorRT operator fusion absorbing a partial-convolution speed advantage at this model scale, and toolchain failure modes with their remedies. We believe this measured, boundary-aware discussion of real-time operation is precisely what the journal's readership expects.

**Summary of contributions.** (1) A class-imbalance-aware, frequency-capped offline sampling strategy that improves rare, welfare-relevant behaviors (e.g., *active* AP50 +11.3 points on the held-out test set) at zero parameter and latency cost, with a sensitivity analysis of the duplication cap. (2) A lightweight FasterNet backbone substitution combined with an identity-preserving weight-integration method; the resulting model is statistically comparable to the baseline (−4.4% parameters, fastest server-side throughput in our comparison), and we report two failed attention-integration attempts that motivated the method. (3) A two-level generalization analysis—an unseen-sequence stress test and a zero-shot cross-dataset evaluation on an independent farm—plus the on-device validation described above.

**A note on evaluation protocol, disclosed proactively.** Our headline results use the dataset publisher's random frame split, which is standard practice in this literature; we state explicitly that adjacent frames inflate absolute accuracy. Rather than leaving this caveat as a limitation paragraph, we quantify it: a sequence-disjoint re-split shows all models degrade sharply (e.g., baseline 0.596 → 0.155 mAP50), and zero-shot evaluation on an independent farm dataset (696 images, different facility and breeds) collapses all models to 0.036–0.067 mAP50. We report these numbers in full in Section 6, together with the finding that exposure re-balancing partially mitigates degradation on visually alien validation scenes. We would rather be measured about where the framework works than claim a generality we did not test.

**Supplementary material.** One supplementary file (Supplementary_Material.pdf/docx) accompanies the submission, containing the per-class AP50 breakdown (Table S1) referenced in Section 4.4.

**Declarations.** The source datasets are public (Roboflow Universe, CC BY 4.0). Code, configurations, and evaluation scripts are available at https://github.com/kksmks/pig-behavior-yolo. The study used only publicly available, non-invasively acquired data; no animal experiments were performed. The authors declare no conflict of interest. AI-assisted tools were used for language polishing and code assistance; all experiments, measurements, and reported numbers were produced and verified by the authors.

We hope the manuscript's combination of measured edge deployment, honest generalization analysis, and class-imbalance methodology makes it a good fit for the Journal of Real-Time Image Processing, and we look forward to the reviewers' comments.

Sincerely,

[Author names]
[Affiliations]
[Corresponding author email]
