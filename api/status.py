from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re

# ==================================================================
# 1. 등급/점수 계산 로직 (기존과 동일)
# ==================================================================

# (1) 성적 평균용 점수 (GPA)
GPA_MAP = {
    'A+': 4.3, 'A0': 4.0, 'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B0': 3.0, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C0': 2.0, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D0': 1.0, 'D': 1.0, 'D-': 0.7,
    'F': 0.0
}

# (2) AP 지급용 점수
AP_BASE_MAP = {'A': 10, 'B': 7, 'C': 4, 'D': 2, 'F': 0}

def score_to_grade(score):
    if score >= 4.15: return 'A+'
    elif score >= 3.85: return 'A'
    elif score >= 3.50: return 'A-'
    elif score >= 3.15: return 'B+'
    elif score >= 2.85: return 'B'
    elif score >= 2.50: return 'B-'
    elif score >= 2.15: return 'C+'
    elif score >= 1.85: return 'C'
    elif score >= 1.50: return 'C-'
    elif score >= 1.15: return 'D+'
    elif score >= 0.85: return 'D'
    else: return 'F'

# ==================================================================
# 2. HUD 좌표 설정 (★ 여기를 이미지에 맞춰 수정!)
# ==================================================================
# 색상은 배경이 어두우니 'White'나 밝은 금색 '#FFFACD' 추천
TEXT_COLOR = '#FFFFFF' 

ASSETS = {
    'academy': {
        'file': 'hud_bg.png', 
        'fields': [
            # -----------------------------------------------------------
            # [중앙 상단] T (Turn)
            # -----------------------------------------------------------
            # 예상: T| 옆이니까 중앙에서 약간 오른쪽
            {'param': 'turn',  'x': 700, 'y': 150, 'size': 45, 'color': TEXT_COLOR, 'mode': 'text'},

            # -----------------------------------------------------------
            # [왼쪽 컬럼] 날짜, 위치, 장면, 학년
            # -----------------------------------------------------------
            # x좌표는 동일하게 맞추고 y좌표만 내림
            {'param': 'date',  'x': 400, 'y': 310, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},
            {'param': 'loc',   'x': 400, 'y': 390, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},
            {'param': 'scene', 'x': 400, 'y': 470, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},
            {'param': 'grade', 'x': 400, 'y': 550, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},

            # -----------------------------------------------------------
            # [오른쪽 컬럼] 수업, 성적, AP
            # -----------------------------------------------------------
            # x좌표를 오른쪽으로 이동
            {'param': 'class', 'x': 900, 'y': 310, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},
            
            # 성적 (자동계산)
            {'param': 'score', 'x': 900, 'y': 390, 'size': 40, 'color': TEXT_COLOR, 'mode': 'grade_avg'},
            
            # AP (자동계산)
            {'param': 'spent', 'x': 900, 'y': 470, 'size': 40, 'color': TEXT_COLOR, 'mode': 'ap_net'},
        ]
    }
}

# ==================================================================
# 3. 데이터 처리 로직 (이전과 동일)
# ==================================================================
def process_value(raw_val, mode, all_params):
    text_val = raw_val.replace('_', ' ')
    try:
        if mode == 'text':
            return text_val if text_val else "-"
        elif mode == 'grade_avg':
            if not text_val: return "-"
            items = text_val.split(',')
            total = 0; count = 0
            for item in items:
                match = re.search(r'([A-DF][+-0]?)', item.upper())
                if match:
                    g = match.group(1)
                    if g not in GPA_MAP and len(g)==1 and g!='F': g+='0'
                    if g in GPA_MAP:
                        total += GPA_MAP[g]; count += 1
            if count == 0: return "-"
            return score_to_grade(total / count)
        elif mode == 'ap_net':
            score_history = all_params.get('score', [''])[0].replace('_', ' ')
            total_earned = 0
            if score_history:
                for item in score_history.split(','):
                    match = re.search(r'([A-DF])', item.upper())
                    if match:
                        letter = match.group(1)
                        points = AP_BASE_MAP.get(letter, 0)
                        if '+' in item: points += 1
                        if '-' in item: points -= 1
                        total_earned += points
            total_spent = 0
            if text_val:
                costs = re.findall(r'\d+', text_val)
                total_spent = sum(int(c) for c in costs)
            return str(total_earned - total_spent)
        else:
            return text_val
    except:
        return "ERR"

# ==================================================================
# 4. 핸들러 (라벨 그리는 부분 삭제됨)
# ==================================================================
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        hud_type = query_params.get('hud', ['academy'])[0]
        if hud_type not in ASSETS: hud_type = 'academy'
        config = ASSETS[hud_type]
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, config['file'])
        font_path = os.path.join(current_dir, 'font.ttf')

        # 이미지 로드
        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGBA")
        else:
            # 이미지가 없을 때 임시 캔버스 (크기 추정 1200x800)
            img = Image.new('RGB', (1200, 800), color='#000033')

        draw = ImageDraw.Draw(img)

        for field in config['fields']:
            param_name = field['param']
            
            # 값 가져오기 & 처리
            raw_val = query_params.get(param_name, [''])[0]
            processed_val = process_value(raw_val, field['mode'], query_params)
            
            # ★ 라벨(label) 없이 값(processed_val)만 그립니다.
            final_text = processed_val
            
            try: font = ImageFont.truetype(font_path, field['size'])
            except: font = ImageFont.load_default()
            
            x, y = field['x'], field['y']
            color = field['color']
            
            # 외곽선 (가독성 향상) - 검은색
            stroke_width = 2
            for dx in range(-stroke_width, stroke_width+1):
                for dy in range(-stroke_width, stroke_width+1):
                    draw.text((x+dx, y+dy), final_text, font=font, fill="black")
            
            # 본문 텍스트 - 설정된 색(흰색)
            draw.text((x, y), final_text, font=font, fill=color)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
