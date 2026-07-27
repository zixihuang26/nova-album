#!/bin/bash
cd "$(dirname "$0")"
if ! lsof -i :8080 | grep -q LISTEN; then
  echo "🐱 启动共享服务器..."
  python3 server.py &
  sleep 1
fi
open http://localhost:8080/
echo "📸 Nova 相册已打开！"
