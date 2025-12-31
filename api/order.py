from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # 파라미터 받기 (기본값 설정)
        item_text = query_params.get('item', ['Unknown'])[0]
        price_text = query_params.get('price', ['?'])[0]
        
        # 1. 캔버스 (가로형 작업지시서 600x300)
        W, H = 600, 300
        # 배경: 짙은 회색 (현장 느낌)
        img = Image.new('RGB', (W, H), color='#252525')
        draw = ImageDraw.Draw(img)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'font.ttf')
        
        try:
            font_head = ImageFont.truetype(font_path, 32)
            font_label = ImageFont.truetype(font_path, 20)
            font_val = ImageFont.truetype(font_path, 28)
            font_stamp = ImageFont.truetype(font_path, 40)
        except:
            font_head = ImageFont.load_default()
            font_label = ImageFont.load_default()
            font_val = ImageFont.load_default()
            font_stamp = ImageFont.load_default()

        # 2. 디자인 요소 (Warning Stripe - 윗부분 띠)
        # 빗금 무늬 대신 심플하게 노란/검정 띠
        draw.rectangle([(0, 0), (W, 20)], fill='#FFD700') # 노랑
        for i in range(0, W, 40):
            draw.polygon([(i, 0), (i+20, 0), (i+10, 20), (i-10, 20)], fill='black')

        # 3. 헤더
        draw.text((30, 40), "SPECIAL WORK ORDER", font=font_head, fill='#FFD700')
        draw.line([(30, 80), (W-30, 80)], fill='#555555', width=2)

        # 4. 내용 (표 형식)
        # REQUEST
        draw.text((30, 100), "REQUEST ITEM:", font=font_label, fill='#AAAAAA')
        draw.text((30, 130), item_text, font=font_val, fill='white')
        
        # COST
        draw.text((30, 180), "AGREED COST:", font=font_label, fill='#AAAAAA')
        draw.text((30, 210), f"{price_text} AP", font=font_val, fill='#FF6B6B') # 가격은 붉은색

        # 5. 페이의 도장 (비스듬하게)
        # 투명 레이어 생성해서 회전
        stamp_img = Image.new('RGBA', (200, 100), (0,0,0,0))
        stamp_draw = ImageDraw.Draw(stamp_img)
        
        # 도장 테두리 및 글씨
        stamp_color = (255, 100, 100, 200) # 반투명 빨강
        stamp_draw.rectangle([(5, 5), (190, 90)], outline=stamp_color, width=5)
        stamp_draw.text((25, 25), "ACCEPTED", font=font_stamp, fill=stamp_color)
        stamp_draw.text((100, 65), " - Pei -", font=font_label, fill=stamp_color)
        
        # 회전 후 합성
        rotated_stamp = stamp_img.rotate(15, expand=1)
        img.paste(rotated_stamp, (350, 120), rotated_stamp)

        # 6. 하단 경고문
        draw.text((30, H-30), "Caution: No guarantee of safety for custom requests.", font=font_label, fill='#555555')

        # 출력
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
