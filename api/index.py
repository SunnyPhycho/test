from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import textwrap

# ==========================================
# 캐릭터 설정 (좌표 y=100)
# ==========================================
ASSETS = {
    '류아': {'file': 'A.png', 'x': 600, 'y': 100, 'color': 'black'},
    '류안': {'file': 'B.png', 'x': 600, 'y': 100, 'color': 'black'},  
    '에이드리안': {'file': 'C.png', 'x': 600, 'y': 100, 'color': 'white'},  
    '서연': {'file': 'D.png', 'x': 600, 'y': 100, 'color': 'white'},  
    '유진': {'file': 'E.png', 'x': 600, 'y': 100, 'color': 'white'},  
    '로완': {'file': 'R.png', 'x': 600, 'y': 100, 'color': 'white'},  
    '빈':   {'file': 'V.png', 'x': 600, 'y': 100, 'color': 'white'},  
    '소렌': {'file': 'S.png', 'x': 600, 'y': 100, 'color': 'white'},  
    '제브릭': {'file': 'Z.png', 'x': 600, 'y': 100, 'color': 'white'},  
    '라스': {'file': 'L.png', 'x': 600, 'y': 100, 'color': 'white'},  
    '페이': {'file': 'P.png', 'x': 600, 'y': 100, 'color': 'black'},  
    'default': {'file': 'hud_bg.png', 'x': 50, 'y': 50, 'color': 'white'}
}

# ==========================================
# 색상 팔레트 정의
# ==========================================
PALETTE_ACADEMIC = ['#D3D3D3', '#87CEEB', '#1E90FF', '#000080', '#FFD700'] 
PALETTE_PERSONAL = ['#D3D3D3', '#FFB6C1', '#FF69B4', '#DC143C', '#8A2BE2'] 
PALETTE_NEGATIVE = ['#A9A9A9', '#696969', '#5D4037', '#800000', '#000000'] 

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # 텍스트 가져오기 (언더바 치환 적용)
        text_input = query_params.get('text', ['내용 없음'])[0].replace('_', ' ')
        img_type = query_params.get('type', ['default'])[0]
        rel_input = query_params.get('rel', [''])[0]

        if img_type not in ASSETS: img_type = 'default'
        config = ASSETS[img_type]
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, config['file'])
        font_path01 = os.path.join(current_dir, 'yuna.ttf')
        font_path02 = os.path.join(current_dir, 'HLR.ttf')

        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGBA")
        else:
            img = Image.new('RGB', (800, 400), color='darkred')

        draw = ImageDraw.Draw(img)

        # 폰트 로드 (대사 / 게이지 별도 분리)
        try:
            font_main = ImageFont.truetype(font_path01, 60) # 대사 폰트 크기 60
            font_rel = ImageFont.truetype(font_path02, 32)  # 게이지 폰트 크기 16
        except:
            font_main = ImageFont.load_default()
            font_rel = ImageFont.load_default()

        text_x = config['x']
        text_y = config['y']
        text_color = config['color']
        
        # ==========================================================
        # 게이지 그리기 함수
        # ==========================================================
        def draw_gauge(start_x, start_y, score, mode='ac'):
            bar_w = 480
            bar_h = 40
            
            abs_score = abs(score)
            tier = min(int(abs_score // 20), 4)
            
            if score >= 0:
                colors = PALETTE_ACADEMIC if mode == 'ac' else PALETTE_PERSONAL
            else:
                colors = PALETTE_NEGATIVE

            if abs_score == 0:
                bg_color = "#333333"
                fg_color = colors[0]
                fill_ratio = 0
            else:
                if tier == 0:
                    bg_color = "#333333"
                    fg_color = colors[0]
                else:
                    bg_color = colors[tier - 1]
                    fg_color = colors[tier]
                
                if abs_score % 20 == 0 and abs_score > 0:
                    bg_color = colors[min(tier - 1, 3)] 
                    fg_color = colors[min(tier, 4)]
                    fill_ratio = 1.0
                else:
                    fill_ratio = (abs_score % 20) / 20.0
            
            draw.rectangle([(start_x, start_y), (start_x + bar_w, start_y + bar_h)], fill=bg_color, outline='black')
            
            fill_w = int(bar_w * fill_ratio)
            if fill_w > 0:
                draw.rectangle([(start_x, start_y), (start_x + fill_w, start_y + bar_h)], fill=fg_color)
            
            # 게이지 텍스트 (font_rel 사용)
            info_text = f"{score}"
            text_w = font_rel.getlength(info_text)
            tx = start_x + (bar_w - text_w) // 2
            ty = start_y - 2 
            
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                draw.text((tx+dx, ty+dy), info_text, font=font_rel, fill="black")
            draw.text((tx, ty), info_text, font=font_rel, fill="white")

        # ==========================================================
        # 호감도 그리기
        # ==========================================================
        if rel_input and ':' in rel_input:
            try:
                parts = rel_input.split(':')
                ac_score = int(parts[0])
                pr_score = int(parts[1])
                
                # 좌표 조정 (대사 위쪽)
                gauge_y = 650
                gauge_x = 820
                
                draw_gauge(gauge_x, gauge_y, ac_score, 'ac')
                draw_gauge(gauge_x, gauge_y+60, pr_score, 'pr')
            except:
                pass

        # 대사 그리기 (수정된 설정 반영)
        max_text_width = 23 # 글자수 23
        lines = textwrap.wrap(text_input, width=max_text_width)
        line_height = 66    # 줄간격 66

        for line in lines:
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                draw.text((text_x+dx, text_y+dy), line, font=font_main, fill="black")
            draw.text((text_x, text_y), line, font=font_main, fill=text_color)
            text_y += line_height

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
