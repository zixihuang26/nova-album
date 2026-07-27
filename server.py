#!/usr/bin/env python3
"""Nova 相册服务器 - 所有访客共享同一份数据"""
import http.server
import json
import os
import re
import base64
import time
from urllib.parse import urlparse, parse_qs

PORT = 8080
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared_data.json')
PHOTOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared_photos')

os.makedirs(PHOTOS_DIR, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'photos': [],        # {id, cat, date, caption, emoji, filename}
        'timeline': [],      # {icon, date, title, desc}
        'funFacts': [],      # {emoji, title, desc}
        'weights': [],       # {date, weight}
        'loves': {},         # {photo_id: count}
        'messages': [],      # {text, avatar, time}
        'spankCount': 0,
        'familyMembers': [],
        'nextPhotoId': 1
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class NovaHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API: get all state
        if path == '/api/state':
            data = load_data()
            # Strip base64 avatars to reduce response size
            for m in data.get('familyMembers', []):
                if m.get('avatar', '').startswith('data:'):
                    m['hasAvatar'] = True
                    m['avatar'] = ''
            self._send_json(data)
            return

        # API: get a specific photo file
        if path.startswith('/api/photo/'):
            photo_id = path.split('/')[-1]
            photo_path = os.path.join(PHOTOS_DIR, f'{photo_id}.jpg')
            if os.path.exists(photo_path):
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Cache-Control', 'public, max-age=3600')
                self.end_headers()
                with open(photo_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self._send_error('Photo not found', 404)
            return

        # API: get family avatar
        if path.startswith('/api/family-avatar/'):
            member_id = path.split('/')[-1]
            for ext in ['.jpg', '.png', '.jpeg']:
                avatar_path = os.path.join(PHOTOS_DIR, f'avatar_{member_id}{ext}')
                if os.path.exists(avatar_path):
                    self.send_response(200)
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Cache-Control', 'public, max-age=3600')
                    self.end_headers()
                    with open(avatar_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            self._send_error('Avatar not found', 404)
            return

        # Default: serve static files
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b'{}'
        try:
            payload = json.loads(body) if body else {}
        except:
            payload = {}

        data = load_data()

        # Add photo
        if path == '/api/photos':
            photo_id = data['nextPhotoId']
            data['nextPhotoId'] += 1

            # Save base64 image to file
            img_b64 = payload.get('src', '')
            if img_b64 and ',' in img_b64:
                img_bytes = base64.b64decode(img_b64.split(',')[1])
                with open(os.path.join(PHOTOS_DIR, f'{photo_id}.jpg'), 'wb') as f:
                    f.write(img_bytes)

            data['photos'].append({
                'id': photo_id,
                'cat': payload.get('cat', 'cute'),
                'date': payload.get('date', ''),
                'caption': payload.get('caption', ''),
                'emoji': payload.get('emoji', '🐱')
            })
            save_data(data)
            self._send_json({'ok': True, 'photo': data['photos'][-1]})
            print(f"📸 照片已添加: {payload.get('caption', '')}")
            return

        # Delete photo
        if path == '/api/photos/delete':
            photo_id = payload.get('id')
            data['photos'] = [p for p in data['photos'] if p['id'] != photo_id]
            # Delete photo file
            photo_path = os.path.join(PHOTOS_DIR, f'{photo_id}.jpg')
            if os.path.exists(photo_path):
                os.remove(photo_path)
            # Clean loves
            data['loves'].pop(str(photo_id), None)
            save_data(data)
            self._send_json({'ok': True})
            print(f"🗑️ 照片已删除: {photo_id}")
            return

        # Love a photo
        if path == '/api/love':
            photo_id = str(payload.get('id', ''))
            data['loves'][photo_id] = data['loves'].get(photo_id, 0) + 1
            save_data(data)
            self._send_json({'ok': True, 'count': data['loves'][photo_id]})
            return

        # Add message
        if path == '/api/messages':
            data['messages'].append({
                'text': payload.get('text', ''),
                'avatar': payload.get('avatar', '🐱'),
                'time': payload.get('time', time.strftime('%Y-%m-%d %H:%M:%S'))
            })
            if len(data['messages']) > 50:
                data['messages'] = data['messages'][-50:]
            save_data(data)
            self._send_json({'ok': True})
            print(f"💬 新留言: {payload.get('text', '')[:30]}")
            return

        # Add timeline entry
        if path == '/api/timeline':
            data['timeline'].append({
                'icon': payload.get('icon', '🐾'),
                'date': payload.get('date', ''),
                'title': payload.get('title', ''),
                'desc': payload.get('desc', '')
            })
            data['timeline'].sort(key=lambda x: x['date'])
            save_data(data)
            self._send_json({'ok': True})
            return

        # Delete timeline entry
        if path == '/api/timeline/delete':
            idx = payload.get('index', -1)
            if 0 <= idx < len(data['timeline']):
                data['timeline'].pop(idx)
                save_data(data)
            self._send_json({'ok': True})
            return

        # Add fun fact
        if path == '/api/facts':
            data['funFacts'].append({
                'emoji': payload.get('emoji', '🐱'),
                'title': payload.get('title', ''),
                'desc': payload.get('desc', '')
            })
            save_data(data)
            self._send_json({'ok': True})
            return

        # Delete fun fact
        if path == '/api/facts/delete':
            idx = payload.get('index', -1)
            if 0 <= idx < len(data['funFacts']):
                data['funFacts'].pop(idx)
                save_data(data)
            self._send_json({'ok': True})
            return

        # Add weight
        if path == '/api/weights':
            data['weights'].append({
                'date': payload.get('date', ''),
                'weight': payload.get('weight', 0)
            })
            data['weights'].sort(key=lambda x: x['date'])
            save_data(data)
            self._send_json({'ok': True})
            return

        # Delete weight
        if path == '/api/weights/delete':
            idx = payload.get('index', -1)
            if 0 <= idx < len(data['weights']):
                data['weights'].pop(idx)
                save_data(data)
            self._send_json({'ok': True})
            return

        # Spank
        if path == '/api/spank':
            data['spankCount'] = data.get('spankCount', 0) + 1
            save_data(data)
            self._send_json({'ok': True, 'count': data['spankCount']})
            return

        # Save family members
        if path == '/api/family':
            members = payload.get('family', [])
            for m in members:
                avatar_b64 = m.get('avatar', '')
                if avatar_b64 and avatar_b64.startswith('data:'):
                    # Save avatar to file
                    try:
                        header, b64data = avatar_b64.split(',', 1)
                        ext = '.png' if 'png' in header else '.jpg'
                        with open(os.path.join(PHOTOS_DIR, f'avatar_{m["id"]}{ext}'), 'wb') as f:
                            f.write(base64.b64decode(b64data))
                        m['hasAvatar'] = True
                    except:
                        m['hasAvatar'] = False
                    m['avatar'] = ''
                elif m.get('hasAvatar'):
                    m['avatar'] = ''
            data['familyMembers'] = members
            save_data(data)
            self._send_json({'ok': True})
            return

        self._send_error('Unknown API endpoint', 404)

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, msg, code=400):
        body = json.dumps({'error': msg}).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    print(f"🐱 Nova 相册服务器启动")
    print(f"   本地: http://localhost:{PORT}")
    print(f"   数据目录: {PHOTOS_DIR}")
    print(f"   数据文件: {DATA_FILE}")
    print()
    http.server.HTTPServer(('0.0.0.0', PORT), NovaHandler).serve_forever()
