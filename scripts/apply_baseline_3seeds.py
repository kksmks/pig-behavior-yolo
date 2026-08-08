# -*- coding: utf-8 -*-
"""Write the 3-seed baseline statistics into JRTIP-paper-v5.docx.

Baseline (YOLOv11n, seeds 0/1/2): val 0.5822 +/- 0.0087, test 0.6060 +/- 0.0084.
Seed 0 exactly reproduces the earlier single-run 0.5964.
Edits three single-run paragraphs: abstract, Table 3 footnote, Section 4.5.
"""
from docx import Document

PATH = r"E:\pig-behavior-yolo\paper\JRTIP-paper-v5.docx"

REPLACEMENTS = [
    # Abstract
    (
        "(test mAP50 0.590 ± 0.009 vs. 0.596)",
        "(test mAP50 0.590 ± 0.009 vs. a three-seed baseline of 0.606 ± 0.008)",
    ),
    # Table 3 footnote
    (
        "versus a single-run baseline of 0.5964—i.e., the single-run values shown here",
        "versus a three-seed baseline of 0.6060 ± 0.0084—i.e., the single-run values shown here",
    ),
    # Section 4.5, sentence 1
    (
        "so we repeated the two adopted models with three different seeds.",
        "so we repeated the baseline and the two adopted models with three different seeds.",
    ),
    # Section 4.5, numbers sentence
    (
        "M4 scores 0.5790 ± 0.0054 on validation and 0.5987 ± 0.0062 on test;",
        "The baseline scores 0.5822 ± 0.0087 on validation and 0.6060 ± 0.0084 on test "
        "(seed 0 exactly reproduces the 0.5964 single run reported in Table 3). "
        "M4 scores 0.5790 ± 0.0054 on validation and 0.5987 ± 0.0062 on test;",
    ),
    # Section 4.5, M5 verdict
    (
        "Against the baseline test value of 0.5964, the M5 difference (−0.006) lies within "
        "one standard deviation, so we report M5 as statistically comparable to the baseline "
        "rather than superior to it.",
        "Against the three-seed baseline test mean, the M5 difference (−0.016) amounts to "
        "about two standard errors of the seed-to-seed variation and is not significant at "
        "the 0.05 level (two-sample t-test, p ≈ 0.09), so we report M5 as statistically "
        "comparable to the baseline rather than superior to it.",
    ),
    # Section 4.5, M4 verdict
    (
        "The M4 test mean exceeds the baseline by only +0.002 overall—its real value,",
        "The M4 test mean sits within one baseline standard deviation (−0.007)—its real value,",
    ),
]


def main():
    doc = Document(PATH)
    hits = {i: 0 for i in range(len(REPLACEMENTS))}
    for p in doc.paragraphs:
        if len(p.runs) != 1:
            continue
        for i, (old, new) in enumerate(REPLACEMENTS):
            if old in p.runs[0].text:
                p.runs[0].text = p.runs[0].text.replace(old, new)
                hits[i] += 1
    for i, n in hits.items():
        status = "OK" if n == 1 else f"PROBLEM ({n} hits)"
        print(f"[{status}] replacement {i}: {REPLACEMENTS[i][0][:60]}...")
    if all(n == 1 for n in hits.values()):
        doc.save(PATH)
        print("saved:", PATH)
    else:
        print("NOT saved — fix anchors first")


if __name__ == "__main__":
    main()
