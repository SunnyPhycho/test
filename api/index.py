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
    '류아': {'file': 'A.png', 'x': 600, 'y': 300, 'color': 'black'},
    '류안': {'file': 'B.png', 'x': 600, 'y': 300, 'color': 'black'},  
    '에이드리안': {'file': 'C.png', 'x': 600, 'y': 300, 'color': 'white'},  
    '서연': {'file': 'D.png', 'x': 600, 'y': 300, 'color': 'white'},  
    '유진': {'file': 'E.png', 'x': 600, 'y': 300, 'color': 'white'},  
    '로완': {'file': 'R.png', 'x': 600, 'y': 300, 'color': 'white'},  
    '빈':   {'file': 'V.png', 'x': 600, 'y': 300, 'color': 'white'},  
    '소렌': {'file': 'S.png', 'x': 600, 'y': 300, 'color': 'white'},  
    '제브릭': {'file': 'Z.png', 'x': 600, 'y': 300, 'color': 'white'},  
    '라스': {'file': 'L.png', 'x': 600, 'y': 300, 'color': 'white'},  
    '페이': {'file': 'P.png', 'x': 600, 'y': 300, 'color': 'black'},  
    'default': {'file': 'hud_bg.png', 'x': 50, 'y': 50, 'color': 'white'}
}

# ==========================================
# 색상 팔레트 정의 (동화풍 파스텔 톤)
# ==========================================

# [학문] 지성, 탐구, 빛 (노랑 -> 주황 -> 빨강 계열)
# 0~20: Cream (부드러운 크림색)
# 20~40: Butter (따뜻한 버터색)
# 40~60: Apricot (살구색)
# 60~80: Coral (산호색)
# 80~100: Sunset (강렬한 노을색)
PALETTE_ACADEMIC = ['#F0F4F8', '#D9E2EC', '#9FB3C8', '#486581', '#102A43']

# [사적] 애정, 설렘, 무드 (분홍 -> 보라 계열)
# 0~20: Misty Rose (안개 낀 장미)
# 20~40: Pink (베이비 핑크)
# 40~60: Hot Pink (진분홍)
# 60~80: Orchid (연보라)
# 80~100: Plum (자두색)
PALETTE_PERSONAL = ['#FFF0F3', '#FFCCD5', '#FF8FA3', '#FF4D6D', '#A4133C']

# [마이너스] 혐오, 오해, 차가움 (회색 -> 검정 계열)
# 점점 색이 빠지고 차가워지는 느낌
PALETTE_NEGATIVE = ['#EDEDED', '#BFBFBF', '#7D7D7D', '#474747', '#000000'] 

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
        font_path02 = os.path.join(current_dir, 'HLB.ttf')
        font_path03 = os.path.join(current_dir, 'NEB.ttf')

        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGBA")
        else:
            img = Image.new('RGB', (800, 400), color='darkred')

        draw = ImageDraw.Draw(img)

        # 폰트 로드 (대사 / 게이지 별도 분리)
        try:
            font_main = ImageFont.truetype(font_path01, 60) # 대사 폰트 크기 60
            font_rel = ImageFont.truetype(font_path02, 24)  # 게이지 폰트 크기 16
            font_icon = ImageFont.truetype(font_path03, 40)  # 게이지 폰트 크기 16
        except:
            font_main = ImageFont.load_default()
            font_rel = ImageFont.load_default()

        text_x = config['x']
        # [수정 전]
        # text_y = config['y'] 
        
        # [수정 후] ▼ 아래 코드로 교체하세요
        center_y = config['y'] # 설정된 Y좌표를 중앙점으로 인식
        total_text_height = len(lines) * line_height # 전체 텍스트 높이 계산
        text_y = center_y - (total_text_height // 2) # 시작 Y좌표 = 중앙 - (높이/2)
        text_color = config['color']

        # ==========================================================
        # 호감도 그리기
        # ==========================================================
        if rel_input and ':' in rel_input:
            try:
                parts = rel_input.split(':')
                ac_score = int(parts[0])
                pr_score = int(parts[1])
                
                # 좌표 조정 
                gauge_y = 600
                gauge_x = 800
                
                draw_gauge(gauge_x, gauge_y, ac_score, 'ac')
                draw_gauge(gauge_x, gauge_y+60, pr_score, 'pr')
            except:
                pass

        # 대사 그리기 (수정된 설정 반영)
        max_text_width = 23 # 글자수 23
        lines = textwrap.wrap(text_input, width=max_text_width)
        line_height = 66    # 줄간격 66

        for line in lines:
            draw.text((text_x, current_y), line, font=font_main, fill=text_color)
            text_y += line_height

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
