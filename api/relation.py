from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==================================================================
# 1. 캐릭터 설정 (파일, 테마색) - 기존 유지
# ==================================================================
ASSETS = {
    # 이름: {파일명, 고유색상(점 찍을 때 사용)}
    '류아': {'file': 'Al.png', 'color': '#be9d8c'},      # 아이보리 계열
    '류안': {'file': 'Bl.png', 'color': '#372c32'},      # 검정 계열
    '에이드리안': {'file': 'Cl.png', 'color': '#3a675f'}, # 초록 계열
    '서연': {'file': 'Dl.png', 'color': '#a91410'},      # 빨강
    '유진': {'file': 'El.png', 'color': '#bfa6ec'},      # 연보라
    '로완': {'file': 'Rl.png', 'color': '#bfa6ec'},      # 연보라
    '라스': {'file': 'Ll.png', 'color': '#bfa6ec'},      # 연보라
    '빈': {'file': 'Vl.png', 'color': '#bfa6ec'},      # 연보라
    '제브릭': {'file': 'Zl.png', 'color': '#bfa6ec'},      # 연보라
    '소렌': {'file': 'Sl.png', 'color': '#bfa6ec'},      # 연보라
    # 이미지가 없는 캐릭터를 위한 기본값
    'default': {'file': 'hud_bg.png', 'color': '#CCCCCC'} 
}

# ==================================================================
# 2. 캔버스 설정 (와이드형)
# ==================================================================
CANVAS_W = 800
CANVAS_H = 300  # 높이를 절반으로 줄임
GRAPH_W = 300   # 그래프 영역 너비 (오른쪽 끝)
CHAR_AREA_W = CANVAS_W - GRAPH_W # 캐릭터 영역 (왼쪽 500px)

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
        if not char_list:
            char_list.append({'name': '류아', 'x': 0, 'y': 0})

        # 2. 캔버스 생성
        base_img = Image.new('RGB', (CANVAS_W, CANVAS_H), color='#202020')
        draw = ImageDraw.Draw(base_img)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'font.ttf')
        try:
            font_s = ImageFont.truetype(font_path, 16) # 폰트 크기 축소
            font_m = ImageFont.truetype(font_path, 20)
        except:
            font_s = ImageFont.load_default()
            font_m = ImageFont.load_default()

        # 3. [왼쪽] 캐릭터 스탠딩 (가로 일렬 배치)
        # 최대 4명까지 표시한다고 가정
        display_chars = char_list[:4]
        count = len(display_chars)
        
        # 각 캐릭터가 차지할 너비
        slot_w = CHAR_AREA_W // max(1, count)
        
        for i, char_info in enumerate(display_chars):
            name = char_info['name']
            conf = ASSETS.get(name, ASSETS['default'])
            img_path = os.path.join(current_dir, conf['file'])
            
            if os.path.exists(img_path):
                char_img = Image.open(img_path).convert("RGBA")
                
                # 리사이즈 (높이 기준 맞춤)
                # 약간의 여백(padding)을 위해 높이 90% 사용
                target_h = int(CANVAS_H * 0.9)
                ratio = target_h / char_img.height
                target_w = int(char_img.width * ratio)
                
                # 만약 너비가 슬롯보다 넓으면 너비 기준으로 재조정
                if target_w > slot_w:
                    target_w = slot_w
                    target_h = int(slot_w / (char_img.width / char_img.height))
                
                char_img = char_img.resize((target_w, target_h))
                
                # 위치 계산 (슬롯 중앙 하단 정렬)
                x_pos = (i * slot_w) + (slot_w - target_w) // 2
                y_pos = CANVAS_H - target_h # 바닥에 붙이기
                
                base_img.paste(char_img, (x_pos, y_pos), char_img)

        # 4. [오른쪽] 미니 좌표계
        gx_start = CHAR_AREA_W
        gy_start = 0
        gw = GRAPH_W
        gh = CANVAS_H
        
        center_x = gx_start + (gw // 2)
        center_y = gy_start + (gh // 2)
        
        # 배경 박스 (약간 더 어둡게)
        draw.rectangle([(gx_start, gy_start), (CANVAS_W, CANVAS_H)], fill='#1A1A1A', outline='#555555')
        
        # 십자선
        draw.line([(gx_start, center_y), (CANVAS_W, center_y)], fill='#444444', width=1)
        draw.line([(center_x, gy_start), (center_x, CANVAS_H)], fill='#444444', width=1)
        
        # 축 라벨 (간소화)
        draw.text((gx_start + 5, center_y + 2), "-학", font=font_s, fill='#888888')
        draw.text((CANVAS_W - 30, center_y + 2), "+학", font=font_s, fill='#888888')
        draw.text((center_x + 2, gy_start + 5), "+사", font=font_s, fill='#888888')
        draw.text((center_x + 2, CANVAS_H - 20), "-사", font=font_s, fill='#888888')

        # 5. 점 찍기
        max_val = 100
        # 스케일: 그래프 크기의 80% 정도만 쓰도록 (여백)
        scale_x = (gw // 2) * 0.8
        scale_y = (gh // 2) * 0.8
        
        for char_info in char_list:
            name = char_info['name']
            val_x = char_info['x']
            val_y = char_info['y']
            
            conf = ASSETS.get(name, ASSETS['default'])
            color = conf['color']

            plot_x = center_x + (val_x / max_val * scale_x)
            plot_y = center_y - (val_y / max_val * scale_y)
            
            # 클램핑 (그래프 영역 밖으로 안 나가게)
            plot_x = max(gx_start + 5, min(CANVAS_W - 5, plot_x))
            plot_y = max(gy_start + 5, min(CANVAS_H - 5, plot_y))
            
            # 점
            r = 5
            draw.ellipse([(plot_x-r, plot_y-r), (plot_x+r, plot_y+r)], fill=color, outline='white')
            
            # 이름 (점 바로 위)
            draw.text((plot_x - 10, plot_y - 20), name, font=font_s, fill=color)

        img_byte_arr = io.BytesIO()
        base_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
