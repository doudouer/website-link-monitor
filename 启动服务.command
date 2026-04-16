#!/bin/bash
cd /Users/wangjiuchen/Documents/trae_projects

echo "=========================================="
echo "    友谊链接监控系统 启动中..."
echo "=========================================="
echo ""
echo "启动后请访问: http://127.0.0.1:5001"
echo ""
echo "按 Ctrl+C 可停止服务"
echo ""

sleep 3 && open http://127.0.0.1:5001 &

python3 web_app_complete.py
