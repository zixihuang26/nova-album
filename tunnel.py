#!/usr/bin/env python3
"""保持在线 - 永不超时的公网隧道"""
import subprocess
import time
import os
import re

LINK_FILE = os.path.expanduser("~/Desktop/Nova分享链接.txt")

def get_link(output):
    m = re.search(r'https://[a-zA-Z0-9.-]+\.serveousercontent\.com', output)
    return m.group(0) if m else None

def save_link(url):
    with open(LINK_FILE, 'w') as f:
        f.write(f"Nova 相册分享链接\n更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{url}\n\n每次打开这个文件获取最新链接\n")

print("🐱 Nova 相册 - 公网隧道（永不断线）")
print("   链接会存到桌面 Nova分享链接.txt")
print()

attempt = 0
while True:
    attempt += 1
    print(f"🔗 第 {attempt} 次连接...")
    try:
        proc = subprocess.Popen(
            ['ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'ServerAliveInterval=15',
             '-o', 'ServerAliveCountMax=3',
             '-o', 'ConnectTimeout=10',
             '-R', '80:localhost:8080', 'serveo.net'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        output = ''
        start = time.time()
        link_found = None

        while True:
            line = proc.stdout.readline()
            if not line:
                break
            output += line
            if not link_found:
                link = get_link(line)
                if link:
                    link_found = link
                    print(f"✅ 链接: {link}")
                    save_link(link)

        proc.wait()
        elapsed = time.time() - start

        if elapsed < 10:
            print(f"⚠️ 快速断开，5秒后重试...")
            time.sleep(5)
        else:
            print(f"⏳ 连接持续 {int(elapsed)} 秒，立即重连...")

    except KeyboardInterrupt:
        print("\n👋 已停止")
        break
    except Exception as e:
        print(f"❌ 错误: {e}，3秒后重试...")
        time.sleep(3)
