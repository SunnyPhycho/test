# api/status.py 전체 코드
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==================================================================
# ★ HUD 설정 (배경 이미지랑 좌표만 수정하세요)
# ==================================================================
ASSETS = {
    'main': {
        'file': 'hud_bg.png', 
        'fields': [
            # mode: text(그냥출력), sum(합계), avg(평균), last(마지막값)
            {'param': 'name', 'x': 50,  'y': 50,  'color': 'white', 'size': 40, 'mode': 'text'},
            {'param': 'hp',   'x': 200, 'y': 100, 'color': 'red',   'size': 50, 'mode': 'sum'},
            {'param': 'gold', 'x': 200, 'y': 160, 'color': 'yellow','size': 50, 'mode': 'sum'},
            {'param': 'rank', 'x': 50,  'y': 250, 'color': 'cyan',  'size': 30, 'mode': 'last'},
        ]
    }
}

# 계산기 함수
def process_value(raw_value, mode):
    if not raw_value: return ""
    items = [x.strip() for x in raw_value.replace('_', ' ').split(',')]
    try:
        if mode == 'text': return " ".join(items)
        elif mode == 'last': return items[-1]
        elif mode == 'sum':
            numbers = [float(x) for x in items if x.replace('.', '', 1).lstrip('-').isdigit()]
            return str(int(sum(numbers)))
        elif mode == 'avg':
            numbers = [float(x) for x in items if x.replace('.', '', 1).lstrip('-').isdigit()]
            if not numbers: return "0"
            return str(int(sum(numbers) / len(numbers)))
        else: return items[-1]
    except: return "ERR"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        hud_type = query_params.get('hud', ['main'])[0]
        if hud_type not in ASSETS: hud_type = 'main'
        config = ASSETS[hud_type]
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, config['file'])
        font_path = os.path.join(current_dir, 'font.ttf')

        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGBA")
        else:
            img = Image.new('RGB', (500, 500), color='black')

        draw = ImageDraw.Draw(img)

        for field in config['fields']:
            param_name = field['param']
            raw_val = query_params.get(param_name, [''])[0]
            final_text = process_value(raw_val, field['mode'])
            
            try: font = ImageFont.truetype(font_path, field['size'])
            except: font = ImageFont.load_default()
            
            x, y = field['x'], field['y']
            color = field['color']
            
            # 테두리 + 글자
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                draw.text((x+dx, y+dy), final_text, font=font, fill="black")
            draw.text((x, y), final_text, font=font, fill=color)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
