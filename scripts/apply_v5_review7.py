# -*- coding: utf-8 -*-
"""Review-board report #7 fixes — apply R1 mandatory wording repairs to v5.

1. Abstract: "statistically indistinguishable" overclaims (n=3 t-test is not an
   equivalence test) -> "statistically comparable" (matches Section 4.5 verdict).
2. 2.1: unverified absence claims about PBR-YOLO (per-class AP / split protocol,
   full text inaccessible) -> verified-only wording; Rahman random image-level
   split confirmed from their own full text ("within-facility performance").
3. Discussion: redundant phrasing + n=2 causal overclaim -> softened.
4. Supplementary Table S2 caption: mark entries as single-run (seed 0) values so
   the overall row (0.596) cannot be misread against the three-seed mean (0.6060).
"""
from docx import Document

PAPER = r"E:\pig-behavior-yolo\paper\JRTIP-paper-v5.docx"
SUPP = r"E:\pig-behavior-yolo\paper\Supplementary_Material_v5.docx"

PAPER_REPL = [
    (
        "while accuracy stays statistically indistinguishable from the baseline across three repeated runs",
        "while accuracy stays statistically comparable to the baseline across three repeated runs",
    ),
    (
        "; class imbalance, which is central to our setting, does not arise in their formulation. "
        "Neither reports per-class accuracy on rare behaviors, and both evaluate on random frame splits.",
        ", evaluating on a random image-level split that they explicitly frame as within-facility "
        "performance. Class-imbalance mitigation, central to our setting, is not part of either "
        "formulation and, to our knowledge, neither reports per-class accuracy on rare behaviors "
        "or generalization to unseen sequences.",
    ),
    (
        "Attention-augmented detectors such as PBR-YOLO [27] report strong results with "
        "attention-augmented lightweight designs, but our two failed integrations (M1, M2) show "
        "that these gains do not transfer when",
        "Attention-augmented lightweight detectors such as PBR-YOLO [27] report strong results, "
        "but our two failed integrations (M1, M2) suggest that these gains may not transfer when",
    ),
]

SUPP_REPL = [
    (
        "M5 values were re-measured under the official validation protocol (overall mAP50 0.5933, "
        "matching the cloud-reported 0.5932).",
        "All entries are single-run values (seed 0); the three-seed means for the overall metric "
        "are reported in Section 4.5 of the main text. M5 values were re-measured under the "
        "official validation protocol (overall mAP50 0.5933, matching the cloud-reported 0.5932).",
    ),
]


def apply(path, repls):
    doc = Document(path)
    hits = [0] * len(repls)
    for p in doc.paragraphs:
        for r in p.runs:
            for i, (old, new) in enumerate(repls):
                if old in r.text:
                    r.text = r.text.replace(old, new)
                    hits[i] += 1
    ok = all(n == 1 for n in hits)
    for i, n in enumerate(hits):
        print(f"[{'OK' if n == 1 else f'PROBLEM {n}'}] {path.split(chr(92))[-1]} repl {i}: {repls[i][0][:50]}...")
    if ok:
        doc.save(path)
        print("saved:", path)
    return ok


if __name__ == "__main__":
    ok1 = apply(PAPER, PAPER_REPL)
    ok2 = apply(SUPP, SUPP_REPL)
    print("ALL DONE" if (ok1 and ok2) else "NOT saved — check anchors")
