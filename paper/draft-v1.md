# Lightweight Multi-Behavior Detection of Group-Housed Pigs: Class-Imbalance-Aware Sampling, FasterNet Backbone, and Edge Deployment Validation

**Draft v1 — 2026-08-03（基于 outline.md；方括号内为图表占位）**

## Abstract

Automated behavior monitoring of group-housed pigs supports health assessment and welfare management in precision livestock farming, yet two practical obstacles persist: severe class imbalance in behavioral data, which degrades detection of rare but welfare-relevant behaviors, and the computational cost of detectors, which impedes deployment on low-cost edge devices in barns. This study addresses both issues with a lightweight detection framework built on YOLOv11n. First, a class-imbalance-aware sampling strategy based on inverse-frequency-weighted image duplication is introduced; on a public ten-class pig behavior dataset it improves the average precision of the rarest behavior (active) from 0.526 to 0.639 and the overall recall by 2.1 percentage points. Second, the P3–P5 backbone stages are replaced with FasterNet blocks, reducing parameters by 5.6% while keeping accuracy statistically indistinguishable from the baseline (test mAP50 0.590 vs. 0.596, within one standard deviation across three runs) and yielding the fastest inference among the evaluated detectors (117.6 FPS on an RTX 3090). Deployment on a Jetson Nano validates edge feasibility: 19.7 FPS at 640×640 input and 33 FPS at 480×480, with approximately 5 W total power draw. A two-level generalization analysis (unseen-pen sequences and an independent farm dataset) is reported transparently, indicating that cross-barn generalization remains an open challenge. The proposed framework offers an accuracy–efficiency balance suited to edge deployment, together with a reproducible evaluation protocol.

**Keywords**: pig behavior detection; class imbalance; weighted sampling; lightweight model; FasterNet; edge deployment; Jetson Nano; precision livestock farming

## 1. Introduction

Pig behavior is a direct indicator of health, welfare, and environmental adaptation in commercial pig production. Feeding, drinking, resting, locomotion, and agonistic behaviors each carry management value, and deviations from normal patterns are among the earliest observable signs of stress or disease. Manual observation is labor-intensive and subjective, and continuous observation is impractical at commercial scale. Computer-vision-based monitoring offers a non-contact, objective, and scalable alternative, and has therefore become a central topic in precision livestock farming (PLF).

Object detectors of the YOLO family are widely adopted for livestock behavior detection because they combine real-time inference with competitive accuracy. Recent studies report improved YOLO variants for the detection of feeding behavior, postures, and aggression in group-housed pigs, typically by inserting attention modules or re-designing feature-fusion paths. Three limitations recur in this literature. First, behavior datasets are strongly imbalanced: resting and exploratory behaviors dominate, while drinking and short social interactions are rare, and models trained with uniform sampling are biased toward frequent classes. Second, most reported models are evaluated only on server-grade GPUs, leaving open whether they can run on low-cost edge hardware inside barns, where network connectivity and power budgets are constrained. Third, evaluations are almost universally performed on frames drawn from the same sequences as the training data, so the ability of published models to generalize to unseen pens, days, or farms is largely unknown.

This study targets these three gaps. A class-imbalance-aware sampling strategy is applied at the data level, duplicating images that contain rare behaviors with frequency-controlled factors. A lightweight variant of YOLOv11n is constructed by replacing the computationally heavy backbone stages with FasterNet blocks based on partial convolution. The resulting models are evaluated on a public ten-class group-housed pig behavior dataset and on a Jetson Nano edge device. The contributions are:

1. A class-imbalance-aware sampling strategy that improves rare-behavior detection without modifying the network: the average precision of the rarest behavior (active) increases from 0.526 to 0.639 on the test set, and recall improves by 2.1 points, with overall accuracy preserved.
2. A lightweight backbone substitution that reduces parameters by 5.6% (2.58M → 2.47M) while keeping test accuracy statistically comparable to the baseline across three repeated runs, and that achieves the highest inference speed among the evaluated detectors.
3. A deployment validation on Jetson Nano (19.7–33 FPS at approximately 5 W), together with a two-level generalization analysis (unseen sequences and an independent farm dataset) that quantifies the cross-barn performance drop honestly.

## 2. Related Work

### 2.1 Vision-Based Livestock Behavior Detection

Deep learning detectors have been applied to individual identification, tracking, and behavior recognition of pigs and cattle. For group-housed pigs, Tu et al. combined YOLOv5 with improved DeepSORT for behavior tracking; Li et al. combined YOLOX with a spatio-temporal module for joint detection and recognition of multiple behaviors; Liang and colleagues proposed improved YOLOv8n variants for the recognition of standing, lying, feeding, drinking, and biting behaviors. Fuentes et al. monitored individual cattle behaviors with action recognition in closed barns. These works demonstrate the feasibility of video-based behavior monitoring but generally assume server-side inference and balanced class distributions.

### 2.2 Class Imbalance in Object Detection

Foreground class imbalance has been analyzed systematically in the object detection literature, with mitigation strategies falling into three families: sampling (class-aware sampling, repeat-factor sampling), loss reweighting (including focal variants), and data augmentation (mosaic, mixup, copy-paste). Sampling methods are attractive for deployment-oriented work because they modify neither the network nor the loss, avoiding interactions with pre-trained weights; repeat-factor sampling, in particular, has been adopted in long-tailed detection benchmarks and in livestock applications such as WFE-YOLO's weighted dataset. The present study follows this line with an offline, frequency-capped oversampling implementation.

### 2.3 Lightweight Detectors and Edge Deployment

Lightweight architectures relevant to this work include depthwise-separable convolutions (MobileNet), feature-reuse convolution (GhostNet), and partial convolution (FasterNet), which performs spatial convolution on only a subset of channels to reduce memory access. Studies deploying YOLO variants on edge devices (e.g., Jetson-series boards) for agricultural monitoring have reported encouraging frame rates with TensorRT acceleration. However, few livestock behavior studies include on-device measurements, and quantization practices on older edge hardware (e.g., Maxwell-generation Jetson Nano) are rarely discussed. This work reports such measurements, including a negative result on INT8 support.

## 3. Materials and Methods

### 3.1 Dataset

Experiments use a public group-housed pig behavior dataset (Roboflow Universe, CC BY 4.0) derived from the publicly documented acquisition of Bergamini et al. (2021). The dataset contains 5,620 images with 13,995 annotated instances across ten behaviors: active, drink, eat, fight, investigating, lying, nose-to-nose, sitting, standing, and walk. Images are top-down or oblique views of pens under natural lighting. Following the publisher's split, 3,936 images are used for training, 1,123 for validation, and 561 for testing. **Table 1** defines all behavior categories, and **Table 2** reports the instance distribution, which is highly imbalanced (investigating: 4,203 instances; sitting: 144; imbalance ratio ≈ 29:1). Annotation quality was verified by visual inspection of a random sample; the dataset card (sources, license, class distribution, and split protocol) is provided with the released code.

Ethics statement: this study uses only publicly available video/image data captured by non-invasive fixed cameras; no animal experiments or interventions were performed, and no institutional ethics approval was required.

### 3.2 Baseline Model

YOLOv11n (2.58M parameters, 6.3 GFLOPs at 640×640) serves as the baseline. Preliminary experiments also examined the newer YOLOv12n as an alternative base; however, the proposed sampling strategy reduced its test accuracy by 1.4 points (Section 5.2), so YOLOv11n was retained as the base architecture for this dataset and method combination.

### 3.3 Class-Imbalance-Aware Sampling

To increase the exposure of rare behaviors during training without altering the network, an offline repeat-factor oversampling is applied to the training split. Let N_c be the number of instances of class c and N_max the largest class count. Each image's duplication factor is f = min(5, round(√(N_max/N_cmin))), where cmin is the rarest class present in the image; the square root damps extreme ratios and the cap limits overfitting to a handful of examples. Images are duplicated with hard links, leaving validation and test splits untouched. The training set grows from 3,936 to 5,889 images, and the rarest classes (sitting, drink, active) receive 3–4× more exposure per epoch.

### 3.4 FasterNet Backbone Substitution

The second modification replaces the C3k2 stages at backbone levels P3, P4, and P5 with FasterNet blocks. Each block applies partial convolution (PConv, spatial convolution on one quarter of the channels) followed by two pointwise convolutions with a residual connection, reducing redundant memory access. The P2 stage and the entire detection head are retained, which allows pre-trained weights to be transferred to all unchanged layers via index-aligned remapping (316 of 415 parameter tensors). The substitution reduces parameters from 2.58M to 2.47M (−5.6%) with comparable compute (6.3G → 6.5G FLOPs) yet faster measured inference.

### 3.5 Training and Evaluation Protocol

All models are trained for at most 200 epochs with early stopping (patience 30), at 640×640 input, with Ultralytics default hyperparameters (AdamW, lr0 = 0.01, weight decay 0.0005, HSV and mosaic augmentation). Model selection uses the validation split; all reported metrics are computed on the held-out test split. The final models are each trained three times with different random seeds, and results are reported as mean ± standard deviation. Training uses an RTX 3090 GPU; deployment evaluation uses a Jetson Nano (JetPack 4.6.3, TensorRT 8.2).

### 3.6 Metrics

Detection accuracy is measured by mAP50, mAP50-95, precision, and recall, including per-class AP. Efficiency is measured by parameter count, GFLOPs, inference latency (FPS), and device power draw.


## 4. Experiments and Results

### 4.1 Experimental Setup

All experiments were conducted on an RTX 3090 (24 GB) under the unified protocol of Section 3.5. The comparison set includes YOLOv5n, YOLOv8n, YOLOv12n, and RT-DETR-l, trained and evaluated under identical conditions.

### 4.2 Ablation Study

**Table 3** reports the ablation on the test set. The sampling strategy alone (M4) raises test mAP50 from 0.5964 to 0.6035 (+0.71 points) and recall from 0.605 to 0.626, with the largest gains on rare classes. The FasterNet substitution alone (M3) reduces parameters by 5.6% at a 2.7-point accuracy cost. The combined model (M5) recovers most of that gap: 0.5932 test mAP50 with 2.47M parameters, i.e., within 0.32 points of the baseline with 5.6% fewer parameters. The negative control (M6) shows that the same sampling strategy applied to YOLOv12n decreases its accuracy (0.5994 vs. 0.6135), supporting the empirical base-model choice.

### 4.3 Comparison with Mainstream Detectors

**Table 4** compares the proposed models with mainstream detectors under identical training conditions. M4 outperforms YOLOv5n (0.6001), YOLOv8n (0.5877), RT-DETR-l (0.6008), and the YOLOv11n baseline (0.5964), and is second only to YOLOv12n (0.6135). M5, with 2.47M parameters, exceeds YOLOv8n (3.01M) and approaches RT-DETR-l (≈32M, ≈103 GFLOPs) at roughly one-thirteenth of its size.

### 4.4 Per-Class Analysis

**Table 5** details per-class AP50. The sampling strategy yields its clearest gains on low-frequency behaviors: active improves from 0.526 to 0.639 on the test set, drink from 0.408 to 0.459 (validation), and sitting by 2 points. A decrease is observed for nose-to-nose (−6.4 points on validation), which is attributed to over-duplication of its limited scenes; this trade-off is analyzed in Section 6.

### 4.5 Statistical Reliability

Three runs per final model produce val mAP50 of 0.5790 ± 0.0054 (M4) and 0.5620 ± 0.0079 (M5), and test mAP50 of 0.5987 ± 0.0062 (M4) and 0.5904 ± 0.0086 (M5). Differences against the baseline (0.5964) are within one standard deviation, so the accuracy of the proposed models is reported as statistically comparable to the baseline rather than superior.

### 4.6 Efficiency Evaluation

**Table 7** lists efficiency metrics. On the RTX 3090, M5 reaches 117.6 FPS, the fastest among all evaluated models (baseline 112.8, M4 112.1, YOLOv12n 78.4). The parameter reduction of 5.6% and the speed advantage over the attention-centric YOLOv12n (≈33% slower) together characterize the accuracy–efficiency balance of the proposed model.

### 4.7 Visualization

Grad-CAM maps (**Fig. 1**) show that the model attends to pig bodies rather than the pen background. Error analysis on dense and interactive scenes (**Fig. 2**) shows residual confusion between fight, lying, and close-contact postures, consistent with the confusion-matrix findings; these cases are discussed as limitations.

## 5. Edge Deployment Validation

The deployment pipeline (PyTorch → ONNX, opset 12 → TensorRT 8.2) was executed on a Jetson Nano (JetPack 4.6.3). **Table 8** reports the measurements. At 640×640 input the model runs at 50.8 ms per frame (19.7 FPS); at 480×480 it reaches 29.9 ms (≈33 FPS), a resolution–speed trade-off suited to fixed barn cameras. Total device power draw during inference remains approximately 5 W. INT8 quantization was attempted but is not supported on the Maxwell-generation GPU of the Jetson Nano (calibration fails on TensorRT 8.2), so FP16 is used; this hardware constraint is reported for reproducibility. The FasterNet variant and the baseline differ by less than 2% in on-device latency, because TensorRT operator fusion masks the theoretical advantage of partial convolution at this model scale.

## 6. Generalization Analysis

### 6.1 Unseen-Sequence Stress Test

Models were retrained on a sequence-disjoint split (training: 11 sequences; validation/test: pens and days never seen in training). Performance drops sharply for all models (**Table 9**): baseline validation/test mAP50 falls to 0.075/0.155. Notably, the sampling-trained model (M4) reaches 0.139 on the harder validation set — nearly twice the baseline (0.075) — indicating that exposure re-balancing partially mitigates degradation on visually alien scenes, although it does not close the gap.

### 6.2 Cross-Dataset Validation

The models were further evaluated without fine-tuning on an independent public pig dataset (Comportamentos, 696 images, different farm and pig breed). All models score 0.036–0.067 mAP50 (**Table 9**). Visual inspection (**Fig. 3**) shows missed detections on white-pig pens with different flooring and failures on spotted-breed individuals, indicating that the degradation stems from combined environment and breed appearance shift rather than from any single model. These results are reported in full because cross-farm generalization is essential for practical deployment yet is seldom quantified in the livestock detection literature.

## 7. Discussion

The proposed framework improves rare-behavior detection and reduces model size while preserving baseline-level accuracy, and it runs in real time on a ~5 W edge device. Three limitations are acknowledged. First, the rarest class (sitting, 144 instances) remains the weakest; more samples are needed for a definitive evaluation of such classes. Second, cross-farm and cross-breed generalization is unsolved; sampling re-balancing mitigates degradation on alien scenes but cannot compensate for breed-level appearance shift. Domain adaptation or multi-farm training data are necessary next steps. Third, INT8 acceleration requires newer edge hardware (e.g., Orin series). These limitations define the agenda for subsequent work rather than undermining the in-domain conclusions.

## 8. Conclusion

This study presented a lightweight group-housed pig behavior detection framework combining class-imbalance-aware sampling with a FasterNet backbone substitution. On a public ten-class dataset, the framework improves rare-class AP (active +11.3 points), keeps overall accuracy statistically comparable to the YOLOv11n baseline, reduces parameters by 5.6%, and achieves the fastest inference among the evaluated detectors (117.6 FPS). Deployment on Jetson Nano demonstrates real-time operation (up to 33 FPS) at approximately 5 W. A transparent two-level generalization analysis quantifies cross-pen and cross-farm degradation and identifies domain adaptation as the key direction for future work.

## Declarations

- **Author Contributions**: [按实际填写]
- **Funding**: [按实际填写]
- **Institutional Review Board Statement**: Not applicable; this study used only publicly available, non-invasive video/image data.
- **Informed Consent Statement**: Not applicable.
- **Data Availability Statement**: The dataset is publicly available on Roboflow Universe (CC BY 4.0); the processing scripts, model configurations, and training logs are available at [GitHub 链接，投稿前整理].
- **AI-Assisted Statement**: AI tools were used for language polishing; all content was verified by the authors.（按 MDPI 政策声明）
- **Conflicts of Interest**: The authors declare no conflicts of interest.
