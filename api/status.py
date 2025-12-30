from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re

# ==================================================================
# 1. 등급 관련 설정 (성적평균용 & AP지급용)
# ==================================================================

# (1) 성적 평균용 점수 (GPA)
GPA_MAP = {
    'A+': 4.3, 'A0': 4.0, 'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B0': 3.0, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C0': 2.0, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D0': 1.0, 'D': 1.0, 'D-': 0.7,
    'F': 0.0
}

# (2) AP 지급용 점수 (보상)
# A=10, B=7, C=4, D=2, F=0 ( +는 +1, -는 -1 )
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
# 2. HUD 설정
# ==================================================================
ASSETS = {
    'academy': {
        'file': 'hud_bg.png', 
        'fields': [
            # [단순 텍스트]
            {'label': 'T ',     'param': 'turn',  'x': 40, 'y': 40, 'size': 35, 'color': '#58ACFA', 'mode': 'text'},
            {'label': '날짜|',  'param': 'date',  'x': 40, 'y': 90, 'size': 28, 'color': '#FFD700', 'mode': 'text'},
            {'label': '위치|',  'param': 'loc',   'x': 40, 'y': 130, 'size': 28, 'color': '#FFD700', 'mode': 'text'},
            {'label': '장면|',  'param': 'scene', 'x': 40, 'y': 170, 'size': 28, 'color': '#FFD700', 'mode': 'text'},
            {'label': '학년|',  'param': 'grade', 'x': 40, 'y': 210, 'size': 28, 'color': '#FFD700', 'mode': 'text'},
            {'label': '수업|',  'param': 'class', 'x': 40, 'y': 250, 'size': 28, 'color': '#FFD700', 'mode': 'text'},
            
            # [성적 평균] - 입력: score=수학A+,과학B
            {'label': '성적|',  'param': 'score', 'x': 40, 'y': 290, 'size': 28, 'color': '#FFD700', 'mode': 'grade_avg'},
            
            # [AP 자동계산] - 입력: spent=검10,포션5 (score는 알아서 참조함)
            {'label': 'AP|',    'param': 'spent', 'x': 40, 'y': 330, 'size': 28, 'color': '#FFD700', 'mode': 'ap_net'},
        ]
    }
}

# ==================================================================
# 3. 데이터 처리 로직 (핵심!)
# ==================================================================
def process_value(raw_val, mode, all_params):
    # 텍스트 전처리 (URL 인코딩된 것 복구)
    text_val = raw_val.replace('_', ' ')

    try:
        # [모드 1] 단순 텍스트
        if mode == 'text':
            return text_val if text_val else "-"

        # [모드 2] 성적 평균 (GPA)
        elif mode == 'grade_avg':
            if not text_val: return "-"
            items = text_val.split(',')
            total = 0
            count = 0
            for item in items:
                match = re.search(r'([A-DF][+-0]?)', item.upper())
                if match:
                    g = match.group(1)
                    if g not in GPA_MAP and len(g)==1 and g!='F': g+='0' # A -> A0
                    if g in GPA_MAP:
                        total += GPA_MAP[g]
                        count += 1
            if count == 0: return "-"
            return score_to_grade(total / count)

        # [모드 3] AP 순수익 계산 (수입 - 지출)
        elif mode == 'ap_net':
            # 1) 총 수입 계산 (score 파라미터를 가져와서 계산)
            score_history = all_params.get('score', [''])[0].replace('_', ' ')
            total_earned = 0
            
            if score_history:
                for item in score_history.split(','):
                    # 등급 찾기 (A, B, C...)
                    match = re.search(r'([A-DF])', item.upper())
                    if match:
                        letter = match.group(1)
                        points = AP_BASE_MAP.get(letter, 0)
                        
                        # 수정자 (+, -) 체크
                        if '+' in item: points += 1
                        if '-' in item: points -= 1
                        
                        total_earned += points

            # 2) 총 지출 계산 (현재 param인 'spent' 사용)
            # 입력예시: "검10, 포션5"
            total_spent = 0
            if text_val:
                # 문자열 내의 모든 숫자 추출해서 더하기
                costs = re.findall(r'\d+', text_val)
                total_spent = sum(int(c) for c in costs)
            
            # 3) 잔액 리턴
            balance = total_earned - total_spent
            return str(balance)

        else:
            return text_val

    except Exception as e:
        return "ERR"

# ==================================================================
# 4. 메인 핸들러
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

        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGBA")
        else:
            img = Image.new('RGB', (400, 600), color='#2E2E2E')

        draw = ImageDraw.Draw(img)

        for field in config['fields']:
            param_name = field['param']
            label = field['label']
            
            # 파라미터 값 가져오기
            raw_val = query_params.get(param_name, [''])[0]
            
            # ★ 여기서 전체 파라미터(query_params)를 같이 넘겨줌
            processed_val = process_value(raw_val, field['mode'], query_params)
            
            final_text = f"{label}{processed_val}"
            
            try: font = ImageFont.truetype(font_path, field['size'])
            except: font = ImageFont.load_default()
            
            x, y = field['x'], field['y']
            color = field['color']
            
            draw.text((x+1, y+1), final_text, font=font, fill="black")
            draw.text((x, y), final_text, font=font, fill=color)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
