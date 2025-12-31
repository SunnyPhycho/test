from http.server import BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==================================================================
# ★ 매점 카탈로그 설정 (여기서 메뉴 수정 가능)
# ==================================================================
SHOP_ITEMS = [
    {"tag": "[소모품]", "name": "카페인 앰플 / 야식 세트", "price": "1~5 AP", "desc": "RP용 지문 강화, 피로 회복"},
    {"tag": "[선물]",   "name": "수제 장식 / 기호품",      "price": "5~15 AP", "desc": "대상 사적 호감도 보정 (+)"},
    {"tag": "[학업]",   "name": "기출 족보 / 논문 요약",   "price": "10~20 AP", "desc": "수업 평가 유리 보정 (Advantage)"},
    {"tag": "[특수]",   "name": "위조 사유서 / 진단서",    "price": "20~30 AP", "desc": "결석/지각 패널티 무효화"},
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. 캔버스 설정 (세로형 메뉴판 600x500)
        W, H = 600, 500
        # 배경: 아주 어두운 남색/검정 (공학적 느낌)
        img = Image.new('RGB', (W, H), color='#151520')
        draw = ImageDraw.Draw(img)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'font.ttf')
        
        try:
            font_title = ImageFont.truetype(font_path, 40)
            font_item = ImageFont.truetype(font_path, 24)
            font_desc = ImageFont.truetype(font_path, 18)
        except:
            font_title = ImageFont.load_default()
            font_item = ImageFont.load_default()
            font_desc = ImageFont.load_default()

        # 2. 테두리 장식 (네온 느낌)
        draw.rectangle([(10, 10), (W-10, H-10)], outline='#4ECDC4', width=3)
        draw.rectangle([(15, 15), (W-15, H-15)], outline='#4ECDC4', width=1)

        # 3. 타이틀 출력
        title = "PEI'S SECRET SHOP"
        draw.text((40, 40), title, font=font_title, fill='#4ECDC4') # 민트색 타이틀
        
        # 구분선
        draw.line([(40, 90), (W-40, 90)], fill='#555555', width=2)

        # 4. 리스트 출력
        start_y = 120
        row_height = 85
        
        for i, item in enumerate(SHOP_ITEMS):
            y = start_y + (i * row_height)
            
            # 태그 (색상 다르게)
            # 소모품(노랑), 선물(분홍), 학업(파랑), 특수(빨강)
            tag_colors = ["#FFE66D", "#FF6B6B", "#4D96FF", "#FF4040"]
            tag_color = tag_colors[i % 4]
            
            draw.text((40, y), item['tag'], font=font_item, fill=tag_color)
            
            # 이름
            draw.text((140, y), item['name'], font=font_item, fill='white')
            
            # 가격 (우측 정렬 느낌으로)
            price_text = item['price']
            px = W - 40 - 100 # 대략적 위치
            draw.text((px, y), price_text, font=font_item, fill='#FFD700') # 금색
            
            # 설명 (아래 작은 글씨)
            draw.text((40, y + 35), f"> {item['desc']}", font=font_desc, fill='#AAAAAA')

        # 5. 하단 안내
        draw.text((40, H - 50), "※ 환불 불가. 비밀 엄수.", font=font_desc, fill='#555555')

        # 6. 출력
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
