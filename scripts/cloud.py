#!/usr/bin/env python3
"""AutoDL 云端操控助手（paramiko）。

用法（密码通过环境变量传入，不写入文件）：
  CLOUD_PASS=xxx python scripts/cloud.py status                    # 训练状态速览
  CLOUD_PASS=xxx python scripts/cloud.py exec "任意shell命令"        # 云端执行
  CLOUD_PASS=xxx python scripts/cloud.py pull <云端文件> <本地路径>   # 下载
  CLOUD_PASS=xxx python scripts/cloud.py push <本地文件> <云端路径>   # 上传
实例更换时可用 CLOUD_HOST / CLOUD_PORT 覆盖默认值。
"""
import os
import sys

import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = os.environ.get('CLOUD_HOST', 'connect.nmb2.seetacloud.com')
PORT = int(os.environ.get('CLOUD_PORT', '39793'))
USER = 'root'
PASS = os.environ.get('CLOUD_PASS')
if not PASS:
    sys.exit('缺少 CLOUD_PASS 环境变量')


def conn():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS, timeout=20)
    return c


def run(c, cmd):
    _, stdout, stderr = c.exec_command(cmd, timeout=600)
    out = stdout.read().decode(errors='replace').replace('\r', '\n')
    err = stderr.read().decode(errors='replace').replace('\r', '\n')
    return out + (f'[stderr] {err}' if err.strip() else '')


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'
    c = conn()
    if action == 'status':
        print(run(c, "ps aux | grep -E 'python.*train' | grep -v grep | head -3;"
                     "echo '--- GPU ---'; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null;"
                     "echo '--- 最新日志 ---'; for f in /root/autodl-tmp/m4.log /root/autodl-tmp/m3b.log /root/autodl-tmp/baseline200.log; do [ -f $f ] && echo \"== $f ==\" && tail -4 $f; done"))
    elif action == 'exec':
        print(run(c, sys.argv[2]))
    elif action == 'pull':
        sftp = c.open_sftp()
        sftp.get(sys.argv[2], sys.argv[3])
        print(f'已下载 {sys.argv[2]} → {sys.argv[3]}')
    elif action == 'push':
        sftp = c.open_sftp()
        sftp.put(sys.argv[2], sys.argv[3])
        print(f'已上传 {sys.argv[2]} → {sys.argv[3]}')
    c.close()


if __name__ == '__main__':
    main()
