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
# 색상 팔레트 정의 (동화풍 파스텔 톤)
# ==========================================

# [학문] 지성, 탐구, 빛 (노랑 -> 주황 -> 빨강 계열)
# 0~20: Cream (부드러운 크림색)
# 20~40: Butter (따뜻한 버터색)
# 40~60: Apricot (살구색)
# 60~80: Coral (산호색)
# 80~100: Sunset (강렬한 노을색)
PALETTE_ACADEMIC = ['#FFFACD', '#FFD700', '#FFB347', '#FF7F50', '#FF4500']

# [사적] 애정, 설렘, 무드 (분홍 -> 보라 계열)
# 0~20: Misty Rose (안개 낀 장미)
# 20~40: Pink (베이비 핑크)
# 40~60: Hot Pink (진분홍)
# 60~80: Orchid (연보라)
# 80~100: Plum (자두색)
PALETTE_PERSONAL = ['#FFE4E1', '#FFB6C1', '#FF69B4', '#DA70D6', '#DDA0DD']

# [마이너스] 혐오, 오해, 차가움 (회색 -> 검정 계열)
# 점점 색이 빠지고 차가워지는 느낌
PALETTE_NEGATIVE = ['#F0F8FF', '#B0C4DE', '#778899', '#4B0082', '#000000'] 

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

        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGBA")
        else:
            img = Image.new('RGB', (800, 400), color='darkred')

        draw = ImageDraw.Draw(img)

        # 폰트 로드 (대사 / 게이지 별도 분리)
        try:
            font_main = ImageFont.truetype(font_path01, 60) # 대사 폰트 크기 60
            font_rel = ImageFont.truetype(font_path02, 24)  # 게이지 폰트 크기 16
        except:
            font_main = ImageFont.load_default()
            font_rel = ImageFont.load_default()

        text_x = config['x']
        text_y = config['y']
        text_color = config['color']

        # ==========================================================
        # ★ 예쁜 게이지 그리기 함수 (Rounded + Glossy)
        # ==========================================================
        def draw_gauge(start_x, start_y, score, mode='ac'):
            bar_w = 450
            bar_h = 50
            corner_r = 10 # 모서리 둥글기 반지름
            
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
            
            # 1. 배경 (둥근 사각형)
            draw.rounded_rectangle([(start_x, start_y), (start_x + bar_w, start_y + bar_h)], radius=corner_r, fill=bg_color, outline=bg_color, width=2)
            
            # 2. 채움 바 (둥근 사각형 + 마스크 처리)
            # 채워지는 부분도 둥글게 보여야 하므로 별도 이미지로 그려서 합성하거나
            # 간단하게는 그냥 둥근 사각형을 그리되, 꽉 찼을 때만 둥글게 처리
            # (복잡한 마스킹 없이 "채워지는 막대"를 그립니다)
            
            fill_w = int(bar_w * fill_ratio)
            if fill_w > 0:
                # 너무 짧으면 둥근게 깨지므로 최소 너비 보정
                safe_w = max(fill_w, corner_r * 2) 
                
                # 채움 영역의 좌표
                fill_box = [(start_x+2, start_y+2), (start_x + fill_w - 2, start_y + bar_h - 2)]
                
                # 100%가 아니면 오른쪽 끝은 직각이어야 자연스럽지만,
                # 코드로 간단히 구현하기 위해 그냥 둥근 사각형으로 채웁니다.
                # (오버레이 방식이라 크게 어색하지 않음)
                if fill_w < bar_w:
                     # 꽉 안 찼을 때는 왼쪽만 둥글게 그리기 어려우니 
                     # 그냥 일반 사각형 그리고 왼쪽 둥근 부분은 덧칠하는 꼼수 대신
                     # 심플하게 내부를 꽉 채우는 둥근 사각형을 그립니다.
                     draw.rounded_rectangle(fill_box, radius=corner_r-2, fill=fg_color)
                else:
                     # 100%일 때
                     draw.rounded_rectangle(fill_box, radius=corner_r-2, fill=fg_color)

            # 3. ★ 경계선 아이콘 (슬라이더)
            # 채워진 너비(fill_w)가 있으면 그 끝에 아이콘 표시
            if fill_w > 0:
                # 아이콘 선택
                icon_char = "❂" if mode == 'ac' else "❦" # 하트나 책
                
                # 좌표: 채워진 바의 오른쪽 끝
                # 약간 겹치게(왼쪽으로) 혹은 바로 옆에(오른쪽으로)
                icon_x = start_x + fill_w - 8 # 바 끝에 걸치게
                icon_y = start_y - 6 # 바보다 살짝 위로 튀어나오게
                
                # 그리기 (색상은 흰색이나 눈에 띄는 색)
                # 이모지가 폰트 미지원으로 깨질 수 있으니, 안전하게는 '●' 같은 특수문자 추천
                # 여기선 일단 요청하신 이모지로 시도
                draw.text((icon_x, icon_y), icon_char, font=font_rel, fill="white")

            # 4. 중앙 텍스트 (기존 점수 표시)
            info_text = f"{score}"
            text_w = font_rel.getlength(info_text)
            tx = start_x + (bar_w - text_w) // 2
            ty = start_y + (bar_h - 30) // 2 # 중앙 정렬 보정 (폰트크기 고려)
            
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                draw.text((tx+dx, ty+dy), info_text, font=font_rel, fill="white")
            draw.text((tx, ty), info_text, font=font_rel, fill="black")

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
