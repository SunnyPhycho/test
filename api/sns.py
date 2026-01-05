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
        
        # 작성자 태그 (입력 없으면 기본값)
        author_tag = query_params.get('tag', ['[공통학부]'])[0].replace('_', ' ')
        
        # 댓글 내용 & 태그
        raw_cmt = query_params.get('cmt', [''])[0].replace('_', ' ')
        comments = raw_cmt.replace('\\n', '\n').split('|') if raw_cmt else []
        
        raw_ctags = query_params.get('ctags', [''])[0].replace('_', ' ')
        comment_tags = raw_ctags.split('|') if raw_ctags else []
        
        likes = query_params.get('likes', [str(random.randint(10, 999))])[0]

        # ----------------------------------------------------
        # 2. 높이 계산
        # ----------------------------------------------------
        base_h = 200
        
        body_wrapped = []
        for bl in body_lines:
            body_wrapped.extend(textwrap.wrap(bl, width=28))
        body_h = len(body_wrapped) * 40 + 20
        
        cmt_wrapped_list = []
        cmt_h = 0
        for c in comments:
            w_lines = textwrap.wrap(c, width=32)
            cmt_wrapped_list.append(w_lines)
            cmt_h += 40 + (len(w_lines) * 35) + 20
            
        TOTAL_W = 600
        TOTAL_H = base_h + body_h + cmt_h + 50
        
        # ----------------------------------------------------
        # 3. 그리기
        # ----------------------------------------------------
        img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'font.ttf')
        font_path02 = os.path.join(current_dir, 'NEB.ttf')
        
        try:
            f_title = ImageFont.truetype(font_path, 40)
            f_body = ImageFont.truetype(font_path, 32)
            f_cmt = ImageFont.truetype(font_path, 28)
            f_small = ImageFont.truetype(font_path, 20)
            f_se = ImageFont.truetype(font_path02, 20)
            f_tag = ImageFont.truetype(font_path, 22)
            f_emoji = ImageFont.truetype(font_path02, 40)
        except:
            f_title = f_body = f_cmt = f_small = f_tag = ImageFont.load_default()

        # [헤더]
        draw.rectangle([(0,0), (TOTAL_W, 80)], fill='#C62917')
        draw.text((20, 20), "Ether-net", font=f_title, fill='white')
        draw.text((TOTAL_W-60, 25), "🔍", font=f_emoji, fill='white')

        cur_y = 110
        
        # [작성자 정보 (입력받은 태그 사용)]
        draw.text((30, cur_y), author_tag, font=f_tag, fill='#C62917')
        draw.text((150, cur_y), "· 익명", font=f_small, fill='#888888')
        cur_y += 40
        
        # [제목]
        draw.text((30, cur_y), title, font=f_title, fill='black')
        cur_y += 50
        
        # [본문]
        for line in body_wrapped:
            draw.text((30, cur_y), line, font=f_body, fill='#333333')
            cur_y += 40
            
        cur_y += 20
        # [정보]
        info_str = f"👍 {likes}    💬 {len(comments)}    📔 5"
        draw.text((30, cur_y), info_str, font=f_se, fill='#888888')
        cur_y += 40
        
        draw.line([(0, cur_y), (TOTAL_W, cur_y)], fill='#EEEEEE', width=2)
        cur_y += 20
        
        # [댓글 목록]
        for i, lines in enumerate(cmt_wrapped_list):
            # 태그 가져오기 (없으면 공통학부 처리)
            if i < len(comment_tags):
                tag_text = comment_tags[i]
            else:
                tag_text = "[공통학부]"
            
            # 글쓴이는 빨간색, 나머지는 회색
            color = "#C62917" if tag_text == "글쓴이" else "#555555"
            
            # 소속 태그
            draw.text((30, cur_y), tag_text, font=f_tag, fill=color)
            draw.text((160, cur_y+2), "익명", font=f_small, fill='#AAAAAA')
            draw.text((TOTAL_W-60, cur_y), "👍", font=f_se, fill='#CCCCCC')
            
            cur_y += 35
            
            # 내용
            for line in lines:
                draw.text((30, cur_y), line, font=f_cmt, fill='black')
                cur_y += 35
            
            cur_y += 5
            draw.text((30, cur_y), f"{random.randint(1,59)}분 전", font=f_small, fill='#CCCCCC')
            
            cur_y += 25
            draw.line([(30, cur_y), (TOTAL_W-30, cur_y)], fill='#F5F5F5', width=1)
            cur_y += 20

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
