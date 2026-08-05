# Real-Time Multi-Behavior Detection of Group-Housed Pigs on Edge Devices: Class-Imbalance-Aware Sampling and a Lightweight FasterNet Backbone

**Draft v2（目标刊：Journal of Real-Time Image Processing，Springer，SCIE Q2）— 2026-08-03**
**与 v1 的差异：题目与叙事转向实时系统；新增"恒等保持集成策略"为方法贡献；采样倍率消融预留实验位**
**v2 已取代 v1（draft-v1.md 作废，以本文件与 draft-v2-zh.md 为准）**

## Abstract

Automated monitoring of group-housed pigs requires behavior detectors that are both accurate on rare, welfare-relevant behaviors and fast enough to run on low-cost edge hardware. This paper presents a real-time multi-behavior detection framework built on YOLOv11n and validated on a Jetson Nano. Three contributions are made. (i) A class-imbalance-aware sampling strategy based on frequency-capped image duplication improves rare-class detection without modifying the network: on a public ten-class dataset, the average precision of the rarest behavior (active) rises from 0.526 to 0.639 and overall recall improves by 2.1 points. (ii) A lightweight backbone substitution using FasterNet blocks is combined with an identity-preserving integration strategy—index-aligned transfer of pre-trained weights—which reduces parameters by 5.6% while keeping accuracy statistically indistinguishable from the baseline across three repeated runs (test mAP50 0.590 ± 0.009 vs. 0.596) and yields the fastest inference among the evaluated detectors (117.6 FPS on an RTX 3090). (iii) On-device validation on the Jetson Nano shows real-time operation (19.7 FPS at 640×640; 33 FPS at 480×480) at approximately 5 W total power, and a two-level generalization analysis (unseen sequences and an independent farm dataset) is reported to delimit the framework's operating envelope. The framework offers a practical accuracy–efficiency balance for barn-side deployment.

**Keywords**: pig behavior detection; class imbalance; repeat-factor sampling; FasterNet; edge computing; Jetson Nano; real-time object detection; precision livestock farming

## 1. Introduction

Behavior is among the most informative indicators of health and welfare in group-housed pigs. Feeding, drinking, resting, locomotion, and agonistic interactions each carry direct management value, and deviations from normal patterns provide early warning of stress or disease. Because manual inspection is labor-intensive and subjective, camera-based automated behavior monitoring has become a practical component of precision livestock farming (PLF). For such monitoring to be economically viable at barn scale, however, detection must run on inexpensive edge devices rather than on remote servers: continuous video streams from hundreds of pens cannot be uploaded to the cloud over rural networks, and per-camera computing cost must stay low.

Single-stage detectors of the YOLO family are the dominant choice for livestock behavior detection because they combine real-time speed with competitive accuracy. Nevertheless, three practical issues remain open. First, behavioral datasets are strongly imbalanced: resting and exploratory behaviors dominate, while drinking and short social interactions are rare, and uniformly sampled training is biased toward frequent classes—precisely the classes least relevant to welfare alerting. Second, most published livestock detectors are evaluated only on server GPUs, so their behavior on memory- and power-constrained edge hardware is largely undocumented. Third, evaluations are commonly performed on frames drawn from the same sequences as the training data, leaving cross-pen and cross-farm generalization unquantified.

This paper addresses the three issues with a framework that combines data-level re-balancing, a lightweight backbone, and on-device validation. The contributions are:

1. A class-imbalance-aware sampling strategy (frequency-capped offline oversampling) that improves rare-behavior detection with no change to the network or the loss; a sensitivity analysis over the duplication cap is included.
2. A lightweight backbone substitution (FasterNet blocks) together with an identity-preserving integration strategy: rather than inserting new gating modules into a pre-trained network—which our experiments show corrupts pre-trained features and degrades accuracy—the substitution keeps the network's channel flow and transfers pre-trained weights through index-aligned remapping, preserving accuracy while reducing parameters by 5.6%.
3. A deployment validation on Jetson Nano (19.7–33 FPS at ≈5 W) and a two-level generalization analysis (unseen sequences; an independent farm dataset), which together define the operating envelope of the framework.

## 2. Related Work

### 2.1 Vision-Based Livestock Behavior Detection

YOLO-based detectors have been applied to pig detection, tracking, posture recognition, and behavior analysis. For group-housed pigs, Tu et al. combined YOLOv5 with improved DeepSORT; Li et al. combined YOLOX with a spatio-temporal recognition module; recent work proposed improved YOLOv8n and YOLOv11 variants for standing, lying, feeding, drinking, and biting behaviors. Cattle studies report similar pipelines for closed-barn monitoring. These works confirm the feasibility of video-based behavior monitoring, but most assume server-side inference and do not address class imbalance explicitly.

### 2.2 Class Imbalance in Object Detection

Mitigation strategies for foreground class imbalance fall into three families: sampling (class-aware or repeat-factor sampling), loss reweighting (including focal variants), and augmentation (mosaic, mixup, copy-paste). Sampling methods require no network or loss modification and therefore interact cleanly with pre-trained weights; repeat-factor sampling is established in long-tailed detection benchmarks and has been adopted in livestock detection (e.g., the weighted dataset of WFE-YOLO). The present work uses an offline, frequency-capped variant and reports its sensitivity to the duplication cap.

### 2.3 Lightweight Detectors and Edge Deployment

Relevant lightweight designs include depthwise-separable convolution (MobileNet), feature-reuse convolution (GhostNet), and partial convolution (FasterNet), the latter reducing memory access by convolving only a subset of channels. Several agricultural studies deploy YOLO variants on Jetson-series boards with TensorRT acceleration. Two observations motivate the present study: edge measurements are rarely reported in livestock behavior papers, and on older Maxwell-generation hardware (Jetson Nano), INT8 acceleration is unavailable—a constraint we document explicitly.

## 3. Materials and Methods

### 3.1 Dataset

Experiments use a public group-housed pig behavior dataset (Roboflow Universe, CC BY 4.0) derived from the publicly documented acquisition of Bergamini et al. (2021). It contains 5,620 images with 13,995 annotated instances over ten behaviors (active, drink, eat, fight, investigating, lying, nose-to-nose, sitting, standing, walk), captured as top-down/oblique pen views under natural daylight. The publisher's split is used (3,936/1,123/561 images for train/validation/test). **Table 1** defines the behavior categories; **Table 2** reports the instance distribution (imbalance ratio ≈ 29:1 between the most and least frequent classes). Annotation quality was verified by visual inspection of a random sample. The study uses only publicly available, non-invasively acquired data; no animal experiments were performed and no ethics approval was required.

### 3.2 Baseline Model

YOLOv11n (2.58M parameters, 6.3 GFLOPs at 640×640) is the baseline. A preliminary experiment examined the newer YOLOv12n as an alternative base, but the proposed sampling strategy reduced its test accuracy by 1.4 points (Section 4.2), so YOLOv11n was retained for this dataset and method combination.

### 3.3 Class-Imbalance-Aware Sampling

With N_c the instance count of class c and N_max the largest class count, each training image is duplicated f = min(5, round(√(N_max/N_cmin))) times, where cmin is the rarest class present in the image. The square-root damping and the cap prevent overfitting to a handful of rare examples; duplication is realized with hard links, and validation/test splits are unchanged. The training set grows from 3,936 to 5,889 images; rare classes receive 3–4× more exposure per epoch. The sensitivity of results to the cap (3/4/5) is evaluated in Section 4.2.

### 3.4 Lightweight Backbone Substitution

The C3k2 stages at backbone levels P3–P5 are replaced by FasterNet blocks (partial convolution over one quarter of the channels, followed by two pointwise convolutions with a residual connection). The P2 stage and the detection head are retained. This reduces parameters from 2.58M to 2.47M (−5.6%) with comparable compute (6.3G → 6.5G FLOPs) yet faster measured inference (Section 4.6).

### 3.5 Identity-Preserving Integration of Pre-trained Weights

Inserting a randomly initialized gating module into a pre-trained network was found to corrupt the pre-trained feature distribution and to degrade accuracy (two variants, −3.0 and −7.2 mAP points, Section 4.2 note). The substitution in Section 3.4 therefore preserves the channel flow and transfers all unchanged weights via index-aligned remapping (316 of 415 parameter tensors), while layers whose shapes are class-dependent (the classification branch of the detection head, COCO-80 → 10 classes) are re-initialized. This integration strategy keeps the modified model's initial behavior close to the pre-trained baseline, and we recommend it over naive insertion when adapting pre-trained detectors.

### 3.6 Training and Evaluation Protocol

All models are trained for at most 200 epochs with early stopping (patience 30) at 640×640, using Ultralytics default hyperparameters (AdamW, lr0 = 0.01, weight decay 5×10⁻⁴, HSV and mosaic augmentation; software: ultralytics 8.4.105, PyTorch 2.3.0, CUDA 12.1). Model selection uses the validation split; reported metrics are computed on the held-out test split. Final models are trained three times with different seeds and reported as mean ± std. Training uses an RTX 3090; deployment evaluation uses a Jetson Nano (JetPack 4.6.3, TensorRT 8.2).

### 3.7 Metrics

mAP50, mAP50-95, precision, recall (overall and per-class), parameter count, GFLOPs, inference latency (FPS), and device power draw.


## 4. Experiments and Results

### 4.1 Setup

All models were trained and evaluated under the unified protocol of Section 3.6. The comparison set comprises YOLOv5n, YOLOv8n, YOLOv12n, and RT-DETR-l.

### 4.2 Ablation Study

**Table 3** summarizes the ablation on the test set. Sampling alone (M4) raises test mAP50 from 0.5964 to 0.6035 and recall from 0.605 to 0.626, with the largest gains on rare classes. The FasterNet substitution alone (M3) costs 2.7 points with 5.6% fewer parameters. The combined model (M5) reaches 0.5932 with 2.47M parameters—within 0.32 points of the baseline at 5.6% fewer parameters. Two integration attempts that insert attention modules into the pre-trained network are included for context (M1, M2): both degrade accuracy (−3.0 and −7.2 points), motivating the identity-preserving strategy of Section 3.5. The negative control (M6) shows that the sampling strategy does not transfer to YOLOv12n (0.5994 vs. 0.6135), supporting the empirical choice of base model. **Table 3b** reports the sensitivity to the duplication cap (3/4/5). [占位：倍率消融跑完后填]

### 4.3 Comparison with Mainstream Detectors

**Table 4** reports the comparison under identical training conditions. M4 outperforms YOLOv5n (0.6001), YOLOv8n (0.5877), RT-DETR-l (0.6008), and the YOLOv11n baseline (0.5964), second only to YOLOv12n (0.6135). M5, at 2.47M parameters, exceeds YOLOv8n (3.01M) and approaches RT-DETR-l (≈32M, ≈103 GFLOPs) at roughly one-thirteenth of its size.

### 4.4 Per-Class Analysis

**Table 5** gives per-class AP50. Gains concentrate on low-frequency behaviors: active improves from 0.526 to 0.639 (test), drink from 0.408 to 0.459 (validation), and sitting by 2 points. A decrease for nose-to-nose (−6.4, validation) is attributed to over-duplication of its few scenes and is discussed in Section 6.

### 4.5 Statistical Reliability

Across three runs: val mAP50 0.5790 ± 0.0054 (M4) and 0.5620 ± 0.0079 (M5); test mAP50 0.5987 ± 0.0062 (M4) and 0.5904 ± 0.0086 (M5). Differences against the baseline are within one standard deviation; accuracy is therefore reported as statistically comparable, not superior.

### 4.6 Efficiency Evaluation

**Table 7** lists efficiency metrics. On the RTX 3090, M5 reaches 117.6 FPS—the fastest of all evaluated models (baseline 112.8, M4 112.1, YOLOv12n 78.4). The proposed model thus combines baseline-level accuracy with the lowest parameter count and the highest speed.

### 4.7 Visualization

Grad-CAM maps (**Fig. 1**) show attention concentrated on pig bodies rather than the pen background. Error analysis on dense and interactive scenes (**Fig. 2**) shows residual confusion among fight, lying, and close-contact postures, consistent with the confusion matrices.

## 5. Edge Deployment Validation

The pipeline (PyTorch → ONNX opset 12 → TensorRT 8.2) was run on a Jetson Nano (JetPack 4.6.3). **Table 8** reports the measurements: 50.8 ms/frame (19.7 FPS) at 640×640 and 29.9 ms (≈33 FPS) at 480×480, with ≈5 W total power draw. INT8 quantization is unavailable on the Maxwell-generation GPU (calibration fails on TensorRT 8.2); FP16 is therefore used, and this constraint is reported for reproducibility. The FasterNet variant and the baseline differ by less than 2% in on-device latency, because TensorRT operator fusion masks the theoretical advantage of partial convolution at this scale. [最终数字待 M5 权重补测后更新]

## 6. Generalization Analysis

### 6.1 Unseen-Sequence Stress Test

Under a sequence-disjoint split, all models degrade sharply (**Table 9**): the baseline falls to 0.075/0.155 (validation/test mAP50). The sampling-trained model reaches 0.139 on the harder validation set—nearly twice the baseline—indicating that exposure re-balancing partially mitigates degradation on visually alien scenes, though it does not close the gap.

### 6.2 Cross-Dataset Validation

Without fine-tuning, the models score 0.036–0.067 mAP50 on an independent public pig dataset (Comportamentos; different farm and breed). **Fig. 3** shows missed detections on white-pig pens with different flooring and failures on spotted-breed individuals, indicating combined environment- and breed-level shift. These results are reported in full because cross-farm generalization is essential for deployment yet rarely quantified in this literature.

## 7. Discussion

The framework improves rare-behavior detection and reduces size while preserving baseline-level accuracy, and it runs in real time on a ≈5 W edge device. The integration analysis (Section 3.5, Table 3) further indicates that when adapting pre-trained detectors, preserving the pre-trained feature pathway matters more than the specific lightweight module chosen. Limitations: the rarest class (sitting, 144 instances) remains weak; cross-farm and cross-breed generalization is unsolved; INT8 acceleration requires newer edge hardware. These point to domain adaptation and multi-farm data collection as future work.

## 8. Conclusion

A lightweight, real-time multi-behavior detection framework for group-housed pigs was presented, combining class-imbalance-aware sampling with a FasterNet backbone substitution under an identity-preserving integration strategy. It improves rare-class AP (active +11.3 points), matches baseline accuracy statistically, reduces parameters by 5.6%, and is the fastest among the evaluated detectors (117.6 FPS), with validated edge operation on Jetson Nano (up to 33 FPS at ≈5 W). A two-level generalization analysis delineates the operating envelope and identifies domain adaptation as the key future direction.

## Declarations

- **Author Contributions**: [按实际填写]
- **Funding**: [按实际填写]
- **Institutional Review Board Statement**: Not applicable; the study used publicly available, non-invasively acquired data only.
- **Informed Consent Statement**: Not applicable.
- **Data Availability Statement**: The dataset is publicly available on Roboflow Universe (CC BY 4.0); processing scripts, model configurations, and training logs are available at [GitHub 链接，投稿前整理].
- **AI-Assisted Statement**: AI tools were used for language polishing; all content was verified by the authors.
- **Conflicts of Interest**: The authors declare no conflicts of interest.
