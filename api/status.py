from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re

# ==================================================================
# 1. 등급/점수 계산 로직
# ==================================================================
GPA_MAP = {
    'A+': 4.3, 'A0': 4.0, 'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B0': 3.0, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C0': 2.0, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D0': 1.0, 'D': 1.0, 'D-': 0.7,
    'F': 0.0
}
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
# 2. HUD 좌표 설정
# ==================================================================
TEXT_COLOR = '#FFFFFF' 

ASSETS = {
    'academy': {
        'file': 'hud_bg.png', 
        'fields': [
            # [중앙 상단] T
            {'param': 'turn',  'x': 800, 'y': 160, 'size': 75, 'color': TEXT_COLOR, 'mode': 'text'},

            # [왼쪽 컬럼]
            {'param': 'date',  'x': 400, 'y': 330, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},
            {'param': 'loc',   'x': 400, 'y': 420, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},
            {'param': 'scene', 'x': 400, 'y': 510, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},
            {'param': 'grade', 'x': 400, 'y': 600, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},

            # [오른쪽 컬럼]
            {'param': 'class', 'x': 1000, 'y': 330, 'size': 40, 'color': TEXT_COLOR, 'mode': 'text'},
            {'param': 'score', 'x': 1000, 'y': 420, 'size': 40, 'color': TEXT_COLOR, 'mode': 'grade_avg'},
            {'param': 'spent', 'x': 1000, 'y': 510, 'size': 40, 'color': TEXT_COLOR, 'mode': 'ap_net'},
        ]
    }
}

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
            img = Image.new('RGB', (1200, 800), color='#000033')

        draw = ImageDraw.Draw(img)

        # 1. 기본 필드 그리기
        for field in config['fields']:
            param_name = field['param']
            raw_val = query_params.get(param_name, [''])[0]
            processed_val = process_value(raw_val, field['mode'], query_params)
            final_text = processed_val
            
            try: font = ImageFont.truetype(font_path, field['size'])
            except: font = ImageFont.load_default()
            
            x, y = field['x'], field['y']
            color = field['color']
            
            stroke_width = 2
            for dx in range(-stroke_width, stroke_width+1):
                for dy in range(-stroke_width, stroke_width+1):
                    draw.text((x+dx, y+dy), final_text, font=font, fill="black")
            draw.text((x, y), final_text, font=font, fill=color)

        # ==========================================================
        # 2. 시간표 (Schedule) 그리기 (좌우 분할 정렬)
        # ==========================================================
        sch_data = query_params.get('sch', [''])[0].replace('_', ' ')
        
        if sch_data:
            # 1) 요일 이름이 시작할 X좌표 (왼쪽 정렬 기준)
            left_align_x = 540
            
            # 2) 과목 목록이 끝날 X좌표 (오른쪽 정렬 기준)
            # 전체 너비가 1200이고, 깃털 장식 고려하여 1150 정도를 끝으로 설정
            right_align_x = 1150
            
            start_y = 575
            line_height = 60
            
            try: sch_font = ImageFont.truetype(font_path, 36)
            except: sch_font = ImageFont.load_default()

            days = sch_data.split(',')
            for i, day_info in enumerate(days):
                if i >= 5: break 
                
                parts = day_info.split(':')
                if len(parts) < 2: continue
                
                day_name = parts[0]
                class_list = parts[1].split('/')
                while len(class_list) < 3: class_list.append("공강")
                
                # --- [왼쪽] 요일 텍스트 ---
                day_text = f"[{day_name}]"
                
                # --- [오른쪽] 과목 텍스트 ---
                class_text = f"{class_list[0]} | {class_list[1]} | {class_list[2]}"
                
                # 과목 텍스트의 길이를 계산하여 X좌표 역산
                class_text_width = sch_font.getlength(class_text)
                class_x = right_align_x - class_text_width
                
                current_y = start_y + (i * line_height)
                
                # 1. 요일 그리기 (왼쪽 정렬)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        draw.text((left_align_x+dx, current_y+dy), day_text, font=sch_font, fill="black")
                draw.text((left_align_x, current_y), day_text, font=sch_font, fill='#FFD700') # 요일은 금색 강조
                
                # 2. 과목 그리기 (오른쪽 정렬)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        draw.text((class_x+dx, current_y+dy), class_text, font=sch_font, fill="black")
                draw.text((class_x, current_y), class_text, font=sch_font, fill='#E0E0E0') # 과목은 은색

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
