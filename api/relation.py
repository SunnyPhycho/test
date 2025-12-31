from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ==================================================================
# 1. 캐릭터 설정 (파일, 테마색)
# ==================================================================
ASSETS = {
    # 이름: {파일명, 고유색상(점 찍을 때 사용)}
    '류아': {'file': 'Al.png', 'color': '#FF6B6B'},      # 빨강 계열
    '류안': {'file': 'Bl.png', 'color': '#4ECDC4'},      # 민트 계열
    '에이드리안': {'file': 'Cl.png', 'color': '#FFE66D'}, # 노랑 계열
    '서연': {'file': 'Dl.png', 'color': '#1A535C'},      # 짙은 청록
    '유진': {'file': 'El.png', 'color': '#FF9F1C'},      # 주황
    # 이미지가 없는 캐릭터를 위한 기본값
    'default': {'file': 'hud_bg.png', 'color': '#CCCCCC'} 
}

# ==================================================================
# 2. 좌표계 설정
# ==================================================================
GRAPH_CONFIG = {
    'width': 400,       # 그래프 영역 너비 (이미지 오른쪽 절반)
    'height': 600,      # 그래프 영역 높이
    'range': 100,       # 좌표 범위 (-100 ~ 100)
    'axis_labels': ['학문적 호감도 (X)', '개인적 호감도 (Y)']
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        # ---------------------------------------------------------
        # 1. 데이터 파싱
        # 입력 예시: ?data=류아:50:30|서연:-20:80
        # (이름:X좌표:Y좌표, 파이프(|)로 인물 구분)
        # ---------------------------------------------------------
        raw_data = query_params.get('data', [''])[0]
        
        # 파싱된 데이터를 담을 리스트: [{'name': '류아', 'x': 50, 'y': 30}, ...]
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
                    except:
                        continue
        
        # 데이터가 없으면 기본값 (류아 0,0)
        if not char_list:
            char_list.append({'name': '류아', 'x': 0, 'y': 0})

        # ---------------------------------------------------------
        # 2. 캔버스 준비 (전체 800 x 600)
        # 왼쪽 400: 스탠딩 이미지 / 오른쪽 400: 그래프
        # ---------------------------------------------------------
        TOTAL_W, TOTAL_H = 800, 600
        base_img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='#2E2E2E')
        draw = ImageDraw.Draw(base_img)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'font.ttf')
        try:
            # 폰트 로드 (그래프 라벨용 작게, 이름용 크게)
            font_s = ImageFont.truetype(font_path, 20)
            font_m = ImageFont.truetype(font_path, 28)
        except:
            font_s = ImageFont.load_default()
            font_m = ImageFont.load_default()

        # ---------------------------------------------------------
        # 3. [왼쪽 영역] 캐릭터 스탠딩 배치 (자동 리사이징)
        # ---------------------------------------------------------
        left_area_w = 400
        left_area_h = 600
        count = len(char_list)

        # 배치 전략 설정
        # 1명: 꽉 채움 (1x1)
        # 2명: 위/아래 2분할 (1x2)
        # 3~4명: 2x2 그리드
        # 그 이상: 4명까지만 그림 (또는 로직 추가 가능)
        
        layout = [] # (x, y, w, h)
        
        if count == 1:
            layout.append((0, 0, left_area_w, left_area_h))
        elif count == 2:
            layout.append((0, 0, left_area_w, left_area_h // 2))
            layout.append((0, left_area_h // 2, left_area_w, left_area_h // 2))
        else: # 3명 이상은 2x2 그리드
            half_w = left_area_w // 2
            half_h = left_area_h // 2
            layout.append((0, 0, half_w, half_h))            # 좌상
            layout.append((half_w, 0, half_w, half_h))      # 우상
            layout.append((0, half_h, half_w, half_h))      # 좌하
            layout.append((half_w, half_h, half_w, half_h)) # 우하

        # 이미지 붙여넣기
        for i, char_info in enumerate(char_list):
            if i >= 4: break # 4명 초과는 생략 (공간 부족)
            
            name = char_info['name']
            conf = ASSETS.get(name, ASSETS['default'])
            img_path = os.path.join(current_dir, conf['file'])
            
            if os.path.exists(img_path):
                char_img = Image.open(img_path).convert("RGBA")
                
                # 배치할 영역 (x, y, w, h)
                dest_x, dest_y, dest_w, dest_h = layout[i]
                
                # 비율 유지하며 리사이즈 (fit)
                # 원본 비율 계산
                img_ratio = char_img.width / char_img.height
                dest_ratio = dest_w / dest_h
                
                if img_ratio > dest_ratio:
                    # 이미지가 더 납작함 -> 너비 기준
                    new_w = dest_w
                    new_h = int(dest_w / img_ratio)
                else:
                    # 이미지가 더 길쭉함 -> 높이 기준
                    new_h = dest_h
                    new_w = int(dest_h * img_ratio)
                
                char_img = char_img.resize((new_w, new_h))
                
                # 영역 중앙 정렬 좌표
                paste_x = dest_x + (dest_w - new_w) // 2
                paste_y = dest_y + (dest_h - new_h) // 2
                
                base_img.paste(char_img, (paste_x, paste_y), char_img)

        # ---------------------------------------------------------
        # 4. [오른쪽 영역] 좌표계 그리기
        # ---------------------------------------------------------
        gx_start = 400
        gy_start = 0
        gw = 400
        gh = 600
        
        center_x = gx_start + (gw // 2)
        center_y = gy_start + (gh // 2)
        
        # (1) 배경 박스
        draw.rectangle([(gx_start, gy_start), (gx_start+gw, gy_start+gh)], fill='#202020', outline='white')
        
        # (2) 십자선 (X축, Y축)
        draw.line([(gx_start, center_y), (gx_start+gw, center_y)], fill='gray', width=2) # 가로선
        draw.line([(center_x, gy_start), (center_x, gy_start+gh)], fill='gray', width=2) # 세로선
        
        # (3) 축 라벨
        draw.text((gx_start + 10, center_y + 5), "-학문", font=font_s, fill='gray')
        draw.text((gx_start + gw - 50, center_y + 5), "+학문", font=font_s, fill='gray')
        draw.text((center_x + 5, gy_start + 10), "+개인", font=font_s, fill='gray')
        draw.text((center_x + 5, gy_start + gh - 30), "-개인", font=font_s, fill='gray')

        # ---------------------------------------------------------
        # 5. [오른쪽 영역] 점 찍기
        # ---------------------------------------------------------
        max_val = 100 # 좌표계 최대값
        scale = 180   # 그래프 상에서 100점이 차지할 픽셀 반경 (200이 최대지만 여백 둠)

        for char_info in char_list:
            name = char_info['name']
            val_x = char_info['x']
            val_y = char_info['y']
            
            conf = ASSETS.get(name, ASSETS['default'])
            color = conf['color']

            # 좌표 변환
            # X: 중앙 + (값/최대값 * 스케일)
            # Y: 중앙 - (값/최대값 * 스케일) -> Y는 위로 갈수록 값이 작아지므로 빼야 함
            plot_x = center_x + (val_x / max_val * scale)
            plot_y = center_y - (val_y / max_val * scale)
            
            # 범위 제한 (그래프 밖으로 안 튀어나가게)
            plot_x = max(gx_start + 10, min(gx_start + gw - 10, plot_x))
            plot_y = max(gy_start + 10, min(gy_start + gh - 10, plot_y))
            
            # 점 그리기 (반지름 6)
            r = 6
            draw.ellipse([(plot_x-r, plot_y-r), (plot_x+r, plot_y+r)], fill=color, outline='white')
            
            # 이름표 (점 옆에)
            label_text = f"{name}({val_x},{val_y})"
            draw.text((plot_x + 10, plot_y - 10), label_text, font=font_s, fill=color)

        # ---------------------------------------------------------
        # 6. 이미지 출력
        # ---------------------------------------------------------
        img_byte_arr = io.BytesIO()
        base_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
