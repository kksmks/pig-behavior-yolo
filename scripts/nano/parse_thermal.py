# 解析 tegrastats 日志：温度/频率/功耗时序 + 节流事件
# 用法：python scripts/nano/parse_thermal.py results/deploy/thermal/thermal.log
import re, sys, json
from pathlib import Path

p = Path(sys.argv[1])
lines = p.read_text(errors='replace').splitlines()
print('行数:', len(lines))

gpu_freq, gpu_temp, cpu_temp, vin_mw, gpu_pct = [], [], [], [], []
for ln in lines:
    m = re.search(r'GR3D_FREQ (\d+)%(?:@(\d+))?', ln)
    if m:
        gpu_pct.append(int(m.group(1)))
        gpu_freq.append(int(m.group(2)) if m.group(2) else None)
    m = re.search(r'GPU@([\d.]+)C', ln)
    if m: gpu_temp.append(float(m.group(1)))
    m = re.search(r'CPU@([\d.]+)C', ln)
    if m: cpu_temp.append(float(m.group(1)))
    m = re.search(r'VDD_IN (\d+)mW', ln)
    if m: vin_mw.append(int(m.group(1)))

def stats(v, name, unit=''):
    if not v or v[0] is None: return f'{name}: 无数据'
    v2 = [x for x in v if x is not None]
    return (f'{name}: 首 {v2[0]}{unit} → 末 {v2[-1]}{unit} | '
            f'min {min(v2)} / mean {sum(v2)/len(v2):.1f} / max {max(v2)}{unit}')

print(stats(gpu_pct, 'GPU 利用率', '%'))
print(stats(gpu_freq, 'GPU 频率', 'MHz'))
print(stats(gpu_temp, 'GPU 温度', '°C'))
print(stats(cpu_temp, 'CPU 温度', '°C'))
print(stats(vin_mw, 'VDD_IN 整机功耗', 'mW'))

# 节流判读：频率显著下降或利用率跌破 90%
throttle_lines = [ln for ln in lines if 'throttle' in ln.lower() or 'EDP' in ln]
print('显式 throttle/EDP 事件行数:', len(throttle_lines))
if gpu_freq and gpu_freq[0]:
    f0 = gpu_freq[0]
    dips = sum(1 for f in gpu_freq if f and f < f0 * 0.9)
    print(f'GPU 频率低于初始 90% 的采样点数: {dips}/{len(gpu_freq)}')
out = {
    'samples': len(lines),
    'gpu_temp_first': gpu_temp[0] if gpu_temp else None,
    'gpu_temp_last': gpu_temp[-1] if gpu_temp else None,
    'gpu_temp_max': max(gpu_temp) if gpu_temp else None,
    'cpu_temp_max': max(cpu_temp) if cpu_temp else None,
    'vin_mw_mean': round(sum(vin_mw)/len(vin_mw)) if vin_mw else None,
    'vin_mw_max': max(vin_mw) if vin_mw else None,
}
Path(str(p) + '.summary.json').write_text(json.dumps(out, indent=1))
print(json.dumps(out, ensure_ascii=False))
