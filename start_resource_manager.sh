#!/bin/bash

# 启动PSM资源管理系统增强版

echo "正在启动PSM资源管理系统增强版..."
echo "请确保已安装所有必要的依赖包: pandas, openpyxl, flask, numpy"

# 检查Python版本
echo "Python版本:"
python --version

# 确保uploads目录存在
if [ ! -d "uploads" ]; then
    echo "创建uploads目录..."
    mkdir -p uploads
fi

# 启动Flask应用
echo "启动Flask服务，访问地址: http://localhost:8888"
echo "按 Ctrl+C 停止服务"

python app_enhanced.py