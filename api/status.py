# api/status.py 전체 코드
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re

# ==================================================================
# ★ 설정 및 데이터 (성적표, 등급표)
# ==================================================================

# 1. 등급 -> 점수 변환표
GRADE_TO_SCORE = {
    'A+': 4.3, 'A0': 4.0, 'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B0': 3.0, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C0': 2.0, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D0': 1.0, 'D': 1.0, 'D-': 0.7,
    'F': 0.0
}

# 2. 점수 -> 등급 역환산표 (평균 낼 때 사용)
def score_to_grade(score):
    if score >= 4.15: return 'A+'
    elif score >= 3.85: return 'A' # A0
    elif score >= 3.50: return 'A-'
    elif score >= 3.15: return 'B+'
    elif score >= 2.85: return 'B' # B0
    elif score >= 2.50: return 'B-'
    elif score >= 2.15: return 'C+'
    elif score >= 1.85: return 'C' # C0
    elif score >= 1.50: return 'C-'
    elif score >= 1.15: return 'D+'
    elif score >= 0.85: return 'D' # D0
    else: return 'F'

# ==================================================================
# ★ HUD 설정 (ASSETS)
# ==================================================================
ASSETS = {
    'academy': {
        'file': 'hud_bg.png', 
        'fields': [
            # 1. 턴수 (단순 텍스트)
            {'label': 'T ',     'param': 'turn',  'x': 40, 'y': 40, 'size': 35, 'color': '#58ACFA', 'mode': 'last'},
            
            # 2. 날짜
            {'label': '날짜|',  'param': 'date',  'x': 40, 'y': 90, 'size': 28, 'color': '#FFD700', 'mode': 'last'},
            
            # 3. 위치
            {'label': '위치|',  'param': 'loc',   'x': 40, 'y': 130, 'size': 28, 'color': '#FFD700', 'mode': 'last'},
            
            # 4. 장면
            {'label': '장면|',  'param': 'scene', 'x': 40, 'y': 170, 'size': 28, 'color': '#FFD700', 'mode': 'last'},
            
            # 5. 학년
            {'label': '학년|',  'param': 'grade', 'x': 40, 'y': 210, 'size': 28, 'color': '#FFD700', 'mode': 'last'},
            
            # 6. 수업 (단순 텍스트)
            {'label': '수업|',  'param': 'class', 'x': 40, 'y': 250, 'size': 28, 'color': '#FFD700', 'mode': 'last'},
            
            # 7. 성적 (★ 등급 변환 로직 적용)
            # 입력 예: "이론A+,전투B0" -> 평균내서 "B+" 출력
            {'label': '성적|',  'param': 'score', 'x': 40, 'y': 290, 'size': 28, 'color': '#FFD700', 'mode': 'grade_avg'},
            
            # 8. AP (★ 잔액 파싱 로직 적용)
            # 입력 예: "잔액:105;총획득:200;총사용:95" -> "105" 출력
            {'label': 'AP|',    'param': 'ap',    'x': 40, 'y': 330, 'size': 28, 'color': '#FFD700', 'mode': 'ap_balance'},
        ]
    }
}

# ==================================================================
# 데이터 처리 함수
# ==================================================================
def process_value(raw_value, mode):
    if not raw_value: return "-"
    
    # 콤마(,)로 들어온 히스토리 분리 (마지막 값 위주로 처리할 때 씀)
    # 근데 AP나 성적은 통짜 문자열로 올 수도 있으니 상황 봐서 처리
    items = [x.strip() for x in raw_value.replace('_', ' ').split(',')]

    try:
        # [모드 1] 단순 텍스트 (마지막 입력값 표시)
        if mode == 'last':
            return items[-1]

        # [모드 2] 성적 평균 계산 (A+ -> 4.3 -> 평균 -> B0)
        elif mode == 'grade_avg':
            total_score = 0
            count = 0
            
            # 모든 히스토리(예: 수학A+, 영어B-)를 다 훑어서 점수화
            for item in items:
                # 정규식으로 등급 문자만 추출 (A+, B-, F 등)
                match = re.search(r'([A-DF][+-0]?)', item.upper())
                if match:
                    grade_str = match.group(1)
                    # A만 있고 A0가 없을 경우 등 처리
                    if grade_str not in GRADE_TO_SCORE and len(grade_str) == 1:
                        if grade_str != 'F': grade_str += '0' # A -> A0 변환
                    
                    if grade_str in GRADE_TO_SCORE:
                        total_score += GRADE_TO_SCORE[grade_str]
                        count += 1
            
            if count == 0: return "-"
            avg = total_score / count
            return score_to_grade(avg) # 다시 문자로 변환해서 리턴

        # [모드 3] AP 잔액 추출
        # 입력 예: "잔액:105;총획득:200..."
        elif mode == 'ap_balance':
            last_entry = items[-1] # 가장 최신 로그만 보면 됨 (거기에 현재 잔액이 있으니까)
            
            # "잔액:숫자" 패턴 찾기
            match = re.search(r'잔액:(\d+)', last_entry)
            if match:
                return match.group(1) # 숫자만 리턴 (예: 105)
            
            # 만약 형식이 안 맞으면 그냥 숫자만이라도 찾아서 리턴 (비상용)
            numbers = re.findall(r'\d+', last_entry)
            if numbers: return numbers[0]
            
            return "0"

        else:
            return items[-1]

    except Exception:
        return "ERR"

# ==================================================================
# 메인 핸들러 (그리기)
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
            
            # URL 파라미터 가져오기
            raw_val = query_params.get(param_name, [''])[0]
            
            # 계산기로 값 가공
            processed_val = process_value(raw_val, field['mode'])
            
            final_text = f"{label}{processed_val}"
            
            try: font = ImageFont.truetype(font_path, field['size'])
            except: font = ImageFont.load_default()
            
            x, y = field['x'], field['y']
            color = field['color']
            
            # 그림자 + 본체 출력
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
