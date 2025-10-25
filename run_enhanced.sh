#!/bin/bash

echo "PSM多资源池分析工具 - 增强版启动器"
echo "=================================="
echo ""
echo "请选择运行模式:"
echo "1. 命令行模式"
echo "2. Web应用模式"
echo "3. 查看使用说明"
echo ""
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo "启动命令行模式..."
        python3 main_enhanced.py
        ;;
    2)
        echo "启动Web应用模式..."
        echo "访问地址: http://localhost:8889"
        python3 app_enhanced.py
        ;;
    3)
        echo "查看使用说明..."
        cat README_ENHANCED.md | less
        ;;
    *)
        echo "无效选项，请重新运行"
        ;;
esac
