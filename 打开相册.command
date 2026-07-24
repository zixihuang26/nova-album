#!/bin/bash
cd "$(dirname "$0")"
echo "🐱 正在启动 Nova 的相册..."
echo ""
echo "   👉 浏览器打开后访问: http://localhost:8080"
echo ""
echo "   看完后回到这里按 Ctrl+C 关闭服务器"
echo ""
sleep 1
open http://localhost:8080
python3 -m http.server 8080
