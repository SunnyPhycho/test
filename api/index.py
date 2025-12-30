from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. URL에서 텍스트 꺼내기 (?text=내용)
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        # 텍스트가 없으면 기본값 출력
        text = query_params.get('text', ['텍스트를 입력하세요'])[0]

        # 2. 이미지 그리기 (메모리 상에서 처리)
        # 배경 (검은색, 800x400)
        img = Image.new('RGB', (800, 400), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 폰트 설정 (서버 기본 폰트 사용, 한글 깨질 수 있으니 나중에 폰트 파일 추가 권장)
        try:
            # 리눅스 서버용 경로 (Vercel은 리눅스 기반)
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()

        # 3. 텍스트 줄바꿈 및 그리기 로직 (아까랑 비슷)
        # (간단하게 중앙 정렬만 구현)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (800 - text_width) / 2
        y = (400 - text_height) / 2
        
        draw.text((x, y), text, font=font, fill=(255, 255, 255))

        # 4. 이미지를 파일이 아닌 '바이트(데이터)'로 변환
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # 5. 브라우저한테 "이거 PNG 이미지야!" 하고 던져주기
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
