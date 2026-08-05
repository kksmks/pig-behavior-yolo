#!/bin/bash
# AutoDL 环境准备：解压数据集 + 安装依赖
# 用法：bash setup.sh
set -e
cd /root/autodl-tmp

if [ -f dataset.zip ]; then
    mkdir -p dataset
    unzip -q -o dataset.zip -d dataset/
    echo "✅ 数据集解压完成: $(find dataset -name data.yaml)"
else
    echo "❌ 未找到 /root/autodl-tmp/dataset.zip，请先在 JupyterLab 上传"
    exit 1
fi

pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple ultralytics
python -c "import ultralytics; print('✅ ultralytics', ultralytics.__version__)"
echo "✅ 环境就绪，运行: nohup python m2_train.py > m2.log 2>&1 &"
