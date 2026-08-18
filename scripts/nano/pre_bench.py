# Nano CPU 侧 preprocess 计时（PIL：JPEG 解码 + letterbox 缩放 + 填充）
# 用法: python3 pre_bench.py /tmp/bench.jpg 640
import sys, time, json
from PIL import Image

path, S = sys.argv[1], int(sys.argv[2])
reps = 100

def t(fn, n=reps):
    fn()  # warm
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000

def decode():
    im = Image.open(path)
    im.load()
    return im

im0 = decode()
w, h = im0.size
r = min(S / w, S / h)
nw, nh = int(round(w * r)), int(round(h * r))

def resize():
    return im0.resize((nw, nh), Image.BILINEAR)

im1 = resize()

def pad():
    canvas = Image.new('RGB', (S, S), (114, 114, 114))
    canvas.paste(im1, ((S - nw) // 2, (S - nh) // 2))
    return canvas

out = {
    'image': path.split('/')[-1], 'orig': '%dx%d' % (w, h), 'size': S,
    'decode_ms': round(t(decode), 3),
    'resize_ms': round(t(resize), 3),
    'pad_ms': round(t(pad), 3),
}
out['preprocess_total_ms'] = round(out['decode_ms'] + out['resize_ms'] + out['pad_ms'], 3)
print(json.dumps(out))
