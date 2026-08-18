# Nano 延迟三段分解（preprocess / inference / postprocess）
# 用法（Nano 上 python3.6）：python3 breakdown_nano.py --engine m5_fp16.engine --imgs /tmp/bench_imgs --size 640
import argparse, glob, json, time
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--engine', required=True)
ap.add_argument('--imgs', default='/tmp/bench_imgs')
ap.add_argument('--size', type=int, default=640)
ap.add_argument('--warm', type=int, default=50)
ap.add_argument('--iters', type=int, default=200)
a = ap.parse_args()

res = {'engine': a.engine, 'size': a.size}

# ---------- Stage 1: preprocess（CPU：解码+letterbox+归一化+排布） ----------
import cv2
paths = sorted(glob.glob(a.imgs + '/*.*'))[:8]
assert paths, 'no images in ' + a.imgs

def letterbox(im, new):
    h, w = im.shape[:2]
    r = min(new / h, new / w)
    nh, nw = int(round(h * r)), int(round(w * r))
    im2 = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LINEAR)
    out = np.full((new, new, 3), 114, np.uint8)
    top, left = (new - nh) // 2, (new - nw) // 2
    out[top:top + nh, left:left + nw] = im2
    return out

# 预热
for p in paths:
    im = cv2.imread(p)
    x = letterbox(im, a.size)[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
t0 = time.perf_counter()
n = 0
for _ in range(100):
    for p in paths:
        im = cv2.imread(p)
        x = letterbox(im, a.size)[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        n += 1
pre_ms = (time.perf_counter() - t0) / n * 1000
res['preprocess_ms'] = round(pre_ms, 2)
img = np.ascontiguousarray(x)

# ---------- Stage 2: inference（GPU：TRT 引擎前向） ----------
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit  # noqa

log = trt.Logger(trt.Logger.ERROR)
with open(a.engine, 'rb') as f:
    engine = trt.Runtime(log).deserialize_cuda_engine(f.read())
ctx = engine.create_execution_context()
ins, outs, bufs, ptrs = [], [], [], []
for i in range(engine.num_bindings):
    shp = tuple(ctx.get_binding_shape(i))
    mem = cuda.mem_alloc(int(np.prod(shp)) * 4)
    ptrs.append(int(mem))
    (ins if engine.binding_is_input(i) else outs).append(mem)
    bufs.append(np.empty(shp, np.float32))
stream = cuda.Stream()
out_shape = tuple(ctx.get_binding_shape(1 if not engine.binding_is_input(1) else 0))

def infer(x):
    cuda.memcpy_htod_async(ins[0], np.ascontiguousarray(x).ravel(), stream)
    ctx.execute_v2(ptrs)
    cuda.memcpy_dtoh_async(bufs[1], outs[0], stream)
    stream.synchronize()
    return bufs[1]

for _ in range(a.warm):
    infer(img)
t0 = time.perf_counter()
for _ in range(a.iters):
    out = infer(img)
inf_ms = (time.perf_counter() - t0) / a.iters * 1000
res['inference_ms'] = round(inf_ms, 2)

# ---------- Stage 3: postprocess（CPU：阈值过滤+NMS） ----------
# 用真实输出形状（[1,84,8400]），分布不影响计时
pred = out.reshape(out.shape[0], out.shape[1], -1) if out.ndim == 3 else out
if pred.shape[1] != 84 and pred.shape[-1] == 84:
    pred = pred.transpose(0, 2, 1)

def nms_numpy(p, conf_th=0.25, iou_th=0.45, max_det=300):
    # p: [1,84,8400] -> 常规 YOLO decode + 逐类 NMS（numpy 实现）
    p = p[0]  # [84,8400]
    boxes, scores = p[:4].T, p[4:]
    cls = scores.argmax(1)
    conf = scores.max(1)
    m = conf > conf_th
    boxes, conf, cls = boxes[m], conf[m], cls[m]
    x1, y1 = boxes[:, 0] - boxes[:, 2] / 2, boxes[:, 1] - boxes[:, 3] / 2
    x2, y2 = boxes[:, 0] + boxes[:, 2] / 2, boxes[:, 1] + boxes[:, 3] / 2
    keep = []
    for c in np.unique(cls):
        idx = np.where(cls == c)[0]
        idx = idx[np.argsort(-conf[idx])]
        while len(idx):
            i = idx[0]
            keep.append(i)
            if len(keep) >= max_det or len(idx) == 1:
                break
            xx1 = np.maximum(x1[i], x1[idx[1:]]); yy1 = np.maximum(y1[i], y1[idx[1:]])
            xx2 = np.minimum(x2[i], x2[idx[1:]]); yy2 = np.minimum(y2[i], y2[idx[1:]])
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            iou = inter / ((x2[i]-x1[i])*(y2[i]-y1) + (x2[idx[1:]]-x1[idx[1:]])*(y2[idx[1:]]-y1[idx[1:]]) - inter + 1e-9)
            idx = idx[1:][iou < iou_th]
    return keep

for _ in range(10):
    nms_numpy(pred)
t0 = time.perf_counter()
for _ in range(100):
    nms_numpy(pred)
post_ms = (time.perf_counter() - t0) / 100 * 1000
res['postprocess_ms'] = round(post_ms, 2)
res['total_ms'] = round(pre_ms + inf_ms + post_ms, 2)
res['fps_est'] = round(1000 / res['total_ms'], 1)
print(json.dumps(res, ensure_ascii=False))
