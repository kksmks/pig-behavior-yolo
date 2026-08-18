// Nano CPU 侧计时：normalize+CHW 内存通道 与 NMS 后处理（纯 C，gcc -O2）
// 用法: gcc -O2 -o post_bench post_bench.c && ./post_bench 640
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now_ms(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

int main(int argc, char **argv) {
    int S = argc > 1 ? atoi(argv[1]) : 640;
    int reps = 200;

    /* ---------- normalize + CHW 通道 ---------- */
    size_t px = (size_t)S * S;
    unsigned char *hwc = malloc(px * 3);
    float *chw = malloc(px * 3 * sizeof(float));
    memset(hwc, 128, px * 3);
    double t0 = now_ms();
    for (int r = 0; r < reps; r++) {
        for (size_t i = 0; i < px; i++) {
            chw[i]           = hwc[i * 3]     / 255.0f;
            chw[px + i]      = hwc[i * 3 + 1] / 255.0f;
            chw[2 * px + i]  = hwc[i * 3 + 2] / 255.0f;
        }
    }
    double norm_ms = (now_ms() - t0) / reps;

    /* ---------- NMS（YOLO 8400 候选，真实稀疏度模拟） ---------- */
    int N = 8400, C = 10;
    float *pred = malloc((4 + C) * N * sizeof(float)); /* cx,cy,w,h + 10 类分 */
    srand48(1234);
    /* 真实稀疏分布：每框抽一个 r，score=r^32 赋给随机一类（真实帧仅一个主类），
       过 0.25 阈值约 300–400 候选，接近 2–3 猪/帧的实际 */
    for (int j = 0; j < N; j++) {
        pred[0 * N + j] = (float)drand48() * S; pred[1 * N + j] = (float)drand48() * S;
        pred[2 * N + j] = 20 + (float)drand48() * 200; pred[3 * N + j] = 20 + (float)drand48() * 200;
        for (int c = 0; c < C; c++) pred[(4 + c) * N + j] = 0.01f;
        float r = (float)drand48();
        float r2 = r * r, r4 = r2 * r2, r8 = r4 * r4, r16 = r8 * r8;
        int hc = (int)(drand48() * C); if (hc >= C) hc = C - 1;
        pred[(4 + hc) * N + j] = r16 * r16 * 1.02f;  /* r^32 */
    }
    float *x1 = malloc(N * 4), *y1 = malloc(N * 4), *x2 = malloc(N * 4), *y2 = malloc(N * 4);
    float *conf = malloc(N * 4); int *cls = malloc(N * 4), *keep = malloc(N * 4);
    int cand_total = 0, keep_total = 0;
    t0 = now_ms();
    for (int r = 0; r < reps; r++) {
        /* decode + 阈值过滤 */
        int nc = 0;
        for (int j = 0; j < N; j++) {
            float best = 0; int bc = 0;
            for (int c = 0; c < C; c++) {
                float s = pred[(4 + c) * N + j];
                if (s > best) { best = s; bc = c; }
            }
            if (best < 0.25f) continue;
            float cx = pred[j], cy = pred[N + j], w = pred[2 * N + j], h = pred[3 * N + j];
            x1[nc] = cx - w / 2; y1[nc] = cy - h / 2;
            x2[nc] = cx + w / 2; y2[nc] = cy + h / 2;
            conf[nc] = best; cls[nc] = bc; nc++;
        }
        cand_total += nc;
        /* 逐类贪心 NMS */
        int nk = 0;
        for (int c = 0; c < C; c++) {
            for (int i = 0; i < nc; i++) {
                if (cls[i] != c || conf[i] < 0) continue;
                keep[nk++] = i;
                if (nk >= 300) break;
                for (int j = i + 1; j < nc; j++) {
                    if (cls[j] != c || conf[j] < 0) continue;
                    float xx1 = x1[i] > x1[j] ? x1[i] : x1[j];
                    float yy1 = y1[i] > y1[j] ? y1[i] : y1[j];
                    float xx2 = x2[i] < x2[j] ? x2[i] : x2[j];
                    float yy2 = y2[i] < y2[j] ? y2[i] : y2[j];
                    float inter = (xx2 - xx1) * (yy2 - yy1);
                    if (inter <= 0) continue;
                    float ai = (x2[i] - x1[i]) * (y2[i] - y1[i]);
                    float aj = (x2[j] - x1[j]) * (y2[j] - y1[j]);
                    if (inter / (ai + aj - inter) > 0.45f) conf[j] = -1;
                }
            }
            if (nk >= 300) break;
        }
        keep_total += nk;
    }
    double nms_ms = (now_ms() - t0) / reps;

    printf("{\n  \"size\": %d,\n  \"normalize_chw_ms\": %.3f,\n"
           "  \"nms_ms\": %.3f,\n  \"nms_candidates_avg\": %.1f,\n"
           "  \"nms_kept_avg\": %.1f\n}\n",
           S, norm_ms, nms_ms,
           (double)cand_total / reps, (double)keep_total / reps);
    return 0;
}
