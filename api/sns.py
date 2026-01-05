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
        
        # 1. 데이터 수신
        title = query_params.get('title', ['무제'])[0].replace('_', ' ')
        raw_body = query_params.get('body', ['내용 없음'])[0].replace('_', ' ')
        body_lines = raw_body.replace('\\n', '\n').split('\n')
        
        author_tag = query_params.get('tag', ['[공통학부]'])[0].replace('_', ' ')
        
        raw_cmt = query_params.get('cmt', [''])[0].replace('_', ' ')
        comments = raw_cmt.replace('\\n', '\n').split('|') if raw_cmt else []
        
        raw_ctags = query_params.get('ctags', [''])[0].replace('_', ' ')
        comment_tags = raw_ctags.split('|') if raw_ctags else []
        
        likes = query_params.get('likes', [str(random.randint(10, 999))])[0]

        # ----------------------------------------------------
        # 2. 높이 계산 (모든 수치를 2배로 계산)
        # ----------------------------------------------------
        # ★ 기준 너비: 1200px (기존 600의 2배)
        TOTAL_W = 1200
        base_h = 400 # 헤더 영역
        
        # 본문 (글자수는 그대로 유지하되 폰트가 커짐)
        body_wrapped = []
        for bl in body_lines:
            # width는 글자 수 기준이므로 비슷하게 유지하거나 약간 조정
            body_wrapped.extend(textwrap.wrap(bl, width=20)) 
        body_h = len(body_wrapped) * 80 + 100 # 줄간격 80px
        
        # 댓글
        cmt_wrapped_list = []
        cmt_h = 0
        for c in comments:
            w_lines = textwrap.wrap(c, width=25)
            cmt_wrapped_list.append(w_lines)
            cmt_h += 80 + (len(w_lines) * 100) + 40 # 작성자줄 + 본문줄 + 여백
            
        TOTAL_H = base_h + body_h + cmt_h + 40
        
        # ----------------------------------------------------
        # 3. 그리기 (2x Scale)
        # ----------------------------------------------------
        img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'font.ttf')
        font_path02 = os.path.join(current_dir, 'NEB.ttf')
        
        # 폰트 크기 2배로 증가
        try:
            f_title = ImageFont.truetype(font_path, 72)
            f_body = ImageFont.truetype(font_path, 64)
            f_cmt = ImageFont.truetype(font_path, 56)
            f_small = ImageFont.truetype(font_path, 40)
            f_tag = ImageFont.truetype(font_path, 44)
            f_icon = ImageFont.truetype(font_path02, 40) # 아이콘
        except:
            f_title = f_body = f_cmt = f_small = f_tag = f_icon = ImageFont.load_default()

        # [헤더]
        draw.rectangle([(0,0), (TOTAL_W, 160)], fill='#C62917')
        draw.text((40, 40), "ETHER-NET", font=f_title, fill='white')
        draw.text((TOTAL_W-120, 50), "🔍", font=f_icon, fill='white')

        cur_y = 220
        
        # [작성자 정보]
        draw.text((60, cur_y), author_tag, font=f_tag, fill='#C62917')
        draw.text((300, cur_y), "· 익명", font=f_small, fill='#888888')
        cur_y += 80
        
        # [제목]
        draw.text((60, cur_y), title, font=f_title, fill='black')
        cur_y += 100
        
        # [본문]
        for line in body_wrapped:
            draw.text((60, cur_y), line, font=f_body, fill='#333333')
            cur_y += 80
            
        cur_y += 40
        
        # [정보: 좋아요/댓글/스크랩] (좌표 간격 2배)
        # 1. 좋아요
        draw.text((60, cur_y), "👍", font=f_icon, fill='#C62917')
        draw.text((110, cur_y+4), f"{likes}", font=f_small, fill='#C62917')
        
        # 2. 댓글
        draw.text((220, cur_y), "💬", font=f_icon, fill='#4ECDC4')
        draw.text((270, cur_y+4), f"{len(comments)}", font=f_small, fill='#4ECDC4')
        
        # 3. 스크랩
        draw.text((360, cur_y), "⭐", font=f_icon, fill='#FFD700')
        draw.text((410, cur_y+4), "scrap 5", font=f_small, fill='#888888')
        
        cur_y += 80
        
        draw.line([(0, cur_y), (TOTAL_W, cur_y)], fill='#EEEEEE', width=4)
        cur_y += 40
        
        # [댓글 목록]
        for i, lines in enumerate(cmt_wrapped_list):
            if i < len(comment_tags): tag_text = comment_tags[i]
            else: tag_text = "[공통학부]"
            
            color = "#C62917" if tag_text == "글쓴이" else "#555555"
            
            # 태그
            draw.text((60, cur_y), tag_text, font=f_tag, fill=color)
            draw.text((320, cur_y+4), "익명", font=f_small, fill='#AAAAAA')
            draw.text((TOTAL_W-120, cur_y), "👍", font=f_icon, fill='#CCCCCC')
            
            cur_y += 70
            
            # 내용
            for line in lines:
                draw.text((60, cur_y), line, font=f_cmt, fill='black')
                cur_y += 70
            
            cur_y += 10
            draw.text((60, cur_y), f"{random.randint(1,59)}분 전", font=f_small, fill='#CCCCCC')
            
            cur_y += 50
            draw.line([(60, cur_y), (TOTAL_W-60, cur_y)], fill='#F5F5F5', width=2)
            cur_y += 40

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
