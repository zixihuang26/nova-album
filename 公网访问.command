#!/bin/bash
cd "$(dirname "$0")"

# Start local server if not running
if ! lsof -i :8080 | grep -q LISTEN; then
  echo "🐱 启动本地服务器..."
  python3 -m http.server 8080 &
  sleep 1
fi

SSH_KEY="$HOME/.ssh/serveo_key"

# Auto-reconnect loop
echo ""
echo "🌐 Nova 相册 - 公网隧道（固定链接）"
echo "   断开后会自动重连，保持这个窗口打开即可"
echo ""

while true; do
  echo "🔗 正在连接..."
  LINK=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R 80:localhost:8080 serveo.net 2>&1 | grep -oE 'https://[a-zA-Z0-9.-]+\.serveo(usercontent)?\.com' | head -1)
  if [ -n "$LINK" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 公网地址: $LINK"
    echo "   （每次重连都是同一个链接！）"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    open "$LINK"
  fi
  echo "⏳ 断开，3秒后重连..."
  sleep 3
done
