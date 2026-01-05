from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import textwrap
import random

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # 1. 데이터 수신 ( \n 처리 )
        # 공백(_) 치환 후, \n은 실제 줄바꿈 문자로 변환
        title = query_params.get('title', ['무제'])[0].replace('_', ' ')
        
        raw_body = query_params.get('body', ['내용 없음'])[0].replace('_', ' ')
        body_lines = raw_body.replace('\\n', '\n').split('\n')
        
        raw_cmt = query_params.get('cmt', [''])[0].replace('_', ' ')
        comments = raw_cmt.replace('\\n', '\n').split('|') if raw_cmt else []
        
        likes = query_params.get('likes', [str(random.randint(10, 999))])[0]

        # ----------------------------------------------------
        # 2. 높이 미리 계산 (Dynamic Height)
        # ----------------------------------------------------
        # 기본 헤더 + 제목 + 정보 + 좋아요바
        base_h = 250 
        
        # 본문 높이 계산 (줄당 35px)
        body_wrapped = []
        for bl in body_lines:
            body_wrapped.extend(textwrap.wrap(bl, width=30))
        body_h = len(body_wrapped) * 35 + 20
        
        # 댓글 높이 계산 (개당 약 80px + 내용길이)
        cmt_wrapped_list = []
        cmt_h = 60 # 댓글 헤더
        for c in comments:
            w_lines = textwrap.wrap(c, width=35)
            cmt_wrapped_list.append(w_lines)
            cmt_h += 30 + (len(w_lines) * 30) + 20 # 작성자줄 + 본문줄 + 여백
            
        TOTAL_W = 600
        TOTAL_H = base_h + body_h + cmt_h + 50 # 여유분
        
        # ----------------------------------------------------
        # 3. 그리기
        # ----------------------------------------------------
        img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='#121212')
        draw = ImageDraw.Draw(img)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'font.ttf')
        
        try:
            f_head = ImageFont.truetype(font_path, 24)
            f_title = ImageFont.truetype(font_path, 36)
            f_body = ImageFont.truetype(font_path, 28)
            f_cmt = ImageFont.truetype(font_path, 24)
            f_small = ImageFont.truetype(font_path, 18)
        except:
            f_head = f_title = f_body = f_cmt = f_small = ImageFont.load_default()

        # 상단바
        draw.rectangle([(0,0), (TOTAL_W,60)], fill='#1E1E1E')
        draw.text((20, 15), "Ether-Net 📡", font=f_head, fill='#4ECDC4')
        draw.text((TOTAL_W-80, 20), "HOT", font=f_small, fill='#FF6B6B')

        cur_y = 90
        
        # 제목
        draw.text((30, cur_y), title, font=f_title, fill='white')
        cur_y += 50
        
        # 정보
        draw.text((30, cur_y), f"익명 · 조회 {int(likes)*7} · {random.randint(1,59)}분 전", font=f_small, fill='#888888')
        cur_y += 40
        draw.line([(30, cur_y), (TOTAL_W-30, cur_y)], fill='#333333', width=1)
        cur_y += 30
        
        # 본문
        for line in body_wrapped:
            draw.text((30, cur_y), line, font=f_body, fill='#E0E0E0')
            cur_y += 35
            
        cur_y += 20
        # 좋아요 박스
        draw.rectangle([(30, cur_y), (130, cur_y+35)], fill='#252525', outline='#444444')
        draw.text((45, cur_y+8), f"👍 {likes}", font=f_small, fill='#FF6B6B')
        
        cur_y += 70
        
        # 댓글 영역
        draw.rectangle([(0, cur_y), (TOTAL_W, TOTAL_H)], fill='#181818')
        draw.text((30, cur_y+15), f"전체 댓글 {len(comments)}", font=f_head, fill='white')
        cur_y += 60
        
        for i, lines in enumerate(cmt_wrapped_list):
            # 익명 번호 부여 (작성자는 글쓴이 표시)
            writer = "글쓴이" if i==0 and random.random()>0.7 else f"익명{random.randint(1,99)}"
            color = "#4ECDC4" if writer=="글쓴이" else "#AAAAAA"
            
            draw.text((30, cur_y), writer, font=f_small, fill=color)
            cur_y += 25
            
            for line in lines:
                draw.text((30, cur_y), line, font=f_cmt, fill='#DDDDDD')
                cur_y += 30
            
            cur_y += 15 # 댓글 간격
            draw.line([(30, cur_y), (TOTAL_W-30, cur_y)], fill='#252525', width=1)
            cur_y += 15

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
