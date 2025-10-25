#!/bin/bash

# PSM双资源池部署分析工具启动脚本

echo "正在启动PSM双资源池部署分析工具..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3命令"
    echo "请安装Python 3.x后再试"
    exit 1
fi

# 检查依赖包
echo "检查依赖包..."
python3 -m pip install -r requirements.txt

# 启动Web应用
echo "启动Web应用..."
echo "应用将在 http://localhost:5000 运行"
python3 app.py