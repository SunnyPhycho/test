from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import textwrap

# ==========================================
# ★ 여기만 수정하면 이미지/좌표 관리 끝!
# ==========================================
ASSETS = {
    # '호출이름': {'파일': '파일명.png', 'x': 가로좌표, 'y': 세로좌표, '색': '글자색'}
    '류아': {'file': 'A.png', 'x': 600,  'y': 50, 'color': 'black'},
    '류안':   {'file': 'B.png',  'x': 600,  'y': 50, 'color': 'black'},  
    '에이드리안':   {'file': 'C.png',  'x': 600,  'y': 50, 'color': 'white'},  
    '서연':   {'file': 'D.png',  'x': 600,  'y': 50, 'color': 'white'},  
    '유진':   {'file': 'E.png',  'x': 600,  'y': 50, 'color': 'white'},  
    '로완':   {'file': 'R.png',  'x': 600,  'y': 50, 'color': 'white'},  
    '빈':   {'file': 'V.png',  'x': 600,  'y': 50, 'color': 'white'},  
    '소렌':   {'file': 'S.png',  'x': 600,  'y': 50, 'color': 'white'},  
    '제브릭':   {'file': 'Z.png',  'x': 600,  'y': 50, 'color': 'white'},  
    '라스':   {'file': 'L.png',  'x': 600,  'y': 50, 'color': 'white'},  
    '페이':   {'file': 'P.png',  'x': 600,  'y': 50, 'color': 'black'},  
}
# ==========================================

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. URL 파라미터 파싱
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # 텍스트 가져오기
        text_input = query_params.get('text', ['내용 없음'])[0].replace('_', ' ')
        
        # 이미지 타입 가져오기 (없으면 'default' 사용)
        img_type = query_params.get('type', ['default'])[0]
        
        # 설정 불러오기 (없는 타입을 요청하면 강제로 default로 설정)
        if img_type not in ASSETS:
            img_type = 'default'
            
        config = ASSETS[img_type]
        
        # 2. 파일 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, config['file'])
        font_path = os.path.join(current_dir, 'yuna.ttf')

        # 3. 이미지 로드
        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGBA")
        else:
            # 이미지가 서버에 없을 때 비상용 (빨간화면)
            img = Image.new('RGB', (500, 300), color='darkred')

        draw = ImageDraw.Draw(img)

        # 4. 폰트 로드
        try:
            font = ImageFont.truetype(font_path, 60)
        except:
            font = ImageFont.load_default()

        # 5. 텍스트 그리기 (설정된 좌표 사용)
        max_text_width = 23
        lines = textwrap.wrap(text_input, width=max_text_width)
        
        text_x = config['x']
        text_y = config['y']
        text_color = config['color']
        line_height = 66

        for line in lines:
            # 외곽선 (검은색 고정)
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                draw.text((text_x+dx, text_y+dy), line, font=font, fill="black")
            
            # 글자 본체 (설정된 색상)
            draw.text((text_x, text_y), line, font=font, fill=text_color)
            
            text_y += line_height

        # 6. 전송
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
