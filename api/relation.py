from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==================================================================
# 1. 캐릭터 설정 (업데이트됨)
# ==================================================================
ASSETS = {
    '류아': {'file': 'Al.png', 'color': '#be9d8c'},      # 아이보리 계열
    '류안': {'file': 'Bl.png', 'color': '#372c32'},      # 검정 계열
    '에이드리안': {'file': 'Cl.png', 'color': '#3a675f'}, # 초록 계열
    '서연': {'file': 'Dl.png', 'color': '#a91410'},      # 빨강
    '유진': {'file': 'El.png', 'color': '#bfa6ec'},      # 연보라
    '로완': {'file': 'Rl.png', 'color': '#bfa6ec'},      
    '라스': {'file': 'Ll.png', 'color': '#bfa6ec'},      
    '빈':   {'file': 'Vl.png', 'color': '#bfa6ec'},      
    '제브릭': {'file': 'Zl.png', 'color': '#bfa6ec'},      
    '소렌': {'file': 'Sl.png', 'color': '#bfa6ec'},      
    '페이': {'file': 'Pl.png', 'color': '#bfa6ec'},      
    'default': {'file': 'hud_bg.png', 'color': '#CCCCCC'} 
}

# ==================================================================
# 2. 캔버스 설정 (초슬림 와이드형)
# ==================================================================
CANVAS_W = 800
CANVAS_H = 100   # 높이 100px 고정
GRAPH_W = 200    # 그래프 영역 너비 (오른쪽 1/4)
CHAR_AREA_W = CANVAS_W - GRAPH_W # 캐릭터 영역 (왼쪽 600px)
BG_COLOR = '#2E2E2E' # 검회색

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        # 1. 데이터 파싱
        raw_data = query_params.get('data', [''])[0]
        char_list = []
        if raw_data:
            entries = raw_data.split('|')
            for entry in entries:
                parts = entry.split(':')
                if len(parts) >= 3:
                    name = parts[0]
                    try:
                        x = int(parts[1])
                        y = int(parts[2])
                        char_list.append({'name': name, 'x': x, 'y': y})
                    except: continue
        
        # 데이터 없으면 기본값 (테스트용)
        if not char_list:
            char_list.append({'name': '류아', 'x': 0, 'y': 0})

        # 2. 캔버스 생성
        base_img = Image.new('RGB', (CANVAS_W, CANVAS_H), color=BG_COLOR)
        draw = ImageDraw.Draw(base_img)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'font.ttf')
        
        # 높이가 좁으므로 폰트는 작게 설정
        try:
            font_s = ImageFont.truetype(font_path, 12) # 아주 작은 폰트
        except:
            font_s = ImageFont.load_default()

        # 3. [왼쪽] 캐릭터 스탠딩 (가로 일렬)
        # 좁은 높이에 맞춰 자동 리사이징
        display_chars = char_list[:6] # 공간상 최대 6명 정도까지 권장
        count = len(display_chars)
        
        if count > 0:
            slot_w = CHAR_AREA_W // count
            
            for i, char_info in enumerate(display_chars):
                name = char_info['name']
                conf = ASSETS.get(name, ASSETS['default'])
                img_path = os.path.join(current_dir, conf['file'])
                
                if os.path.exists(img_path):
                    char_img = Image.open(img_path).convert("RGBA")
                    
                    # 높이 기준 리사이즈 (상하 여백 5px씩 -> 90px)
                    target_h = 90
                    ratio = target_h / char_img.height
                    target_w = int(char_img.width * ratio)
                    
                    # 만약 캐릭터가 너무 뚱뚱해서 슬롯을 넘어가면 너비 기준 리사이즈
                    if target_w > slot_w - 10:
                        target_w = slot_w - 10
                        target_h = int(target_w / (char_img.width / char_img.height))
                    
                    char_img = char_img.resize((target_w, target_h))
                    
                    # 위치: 슬롯 중앙, 바닥 정렬
                    x_pos = (i * slot_w) + (slot_w - target_w) // 2
                    y_pos = (CANVAS_H - target_h) // 2 # 세로 중앙 정렬
                    
                    base_img.paste(char_img, (x_pos, y_pos), char_img)

        # 4. [오른쪽] 미니 좌표계
        gx_start = CHAR_AREA_W
        gy_start = 0
        gw = GRAPH_W
        gh = CANVAS_H
        
        center_x = gx_start + (gw // 2)
        center_y = gy_start + (gh // 2)
        
        # 그래프 배경 (약간 더 어둡게 구분)
        draw.rectangle([(gx_start, gy_start), (CANVAS_W, CANVAS_H)], fill='#1F1F1F', outline='#444444')
        
        # 십자선 (중앙)
        draw.line([(gx_start, center_y), (CANVAS_W, center_y)], fill='#555555', width=1)
        draw.line([(center_x, gy_start), (center_x, CANVAS_H)], fill='#555555', width=1)
        
        # 축 라벨 (공간이 좁으니 약어 사용)
        # 학문(X), 사적(Y)
        draw.text((gx_start + 5, center_y + 2), "-학", font=font_s, fill='#666666')
        draw.text((CANVAS_W - 20, center_y + 2), "+학", font=font_s, fill='#666666')
        draw.text((center_x + 2, gy_start + 2), "+사", font=font_s, fill='#666666')
        draw.text((center_x + 2, CANVAS_H - 15), "-사", font=font_s, fill='#666666')

        # 5. 점 찍기
        max_val = 100
        # 스케일: 높이가 100px이니 반지름 40px 정도가 한계 (여백 고려)
        scale_size = 40 
        
        for char_info in char_list:
            name = char_info['name']
            val_x = char_info['x']
            val_y = char_info['y']
            
            conf = ASSETS.get(name, ASSETS['default'])
            color = conf['color']

            plot_x = center_x + (val_x / max_val * scale_size)
            plot_y = center_y - (val_y / max_val * scale_size) # Y축은 위가 +
            
            # 클램핑
            plot_x = max(gx_start + 5, min(CANVAS_W - 5, plot_x))
            plot_y = max(gy_start + 5, min(CANVAS_H - 5, plot_y))
            
            # 점 그리기 (작게)
            r = 3
            draw.ellipse([(plot_x-r, plot_y-r), (plot_x+r, plot_y+r)], fill=color, outline=None)
            
            # 이름 (점 바로 옆에 작게)
            draw.text((plot_x + 4, plot_y - 6), name, font=font_s, fill=color)

        img_byte_arr = io.BytesIO()
        base_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
