import sys
import os
import re
from PIL import Image, ImageDraw, ImageFont

# 1. 입력값 받기
try:
    text_input = sys.argv[1]
except IndexError:
    print("텍스트가 입력되지 않았습니다.")
    sys.exit(1)

# 설정
base_image_path = "template.png"  # 원본 이미지
result_dir = "public/result"             # 저장될 폴더
font_path = "NanumGothic.ttf"     # 폰트 파일 (없으면 기본 폰트 사용하지만 한글 깨짐 주의)
font_size = 40
max_width_padding = 40            # 좌우 여백 합계

# 2. 파일명 생성 로직 ('원본명_텍스트.png' 형식)
# 파일명에 쓸 수 없는 특수문자 제거 및 공백을 언더바(_)로 변경
base_name = os.path.splitext(os.path.basename(base_image_path))[0]
safe_text = re.sub(r'[\\/*?:"<>|]', "", text_input).strip().replace(" ", "_")
# 파일명이 너무 길면 잘라냄 (선택사항)
safe_text = safe_text[:30] 
output_filename = f"{base_name}_{safe_text}.png"
output_path = os.path.join(result_dir, output_filename)

os.makedirs(result_dir, exist_ok=True)

# 3. 이미지 및 폰트 로드
img = Image.open(base_image_path)
draw = ImageDraw.Draw(img)
image_width, image_height = img.size

try:
    font = ImageFont.truetype(font_path, font_size)
except IOError:
    print("폰트 파일을 찾을 수 없어 기본 폰트를 사용합니다. (한글 깨짐 가능성 있음)")
    font = ImageFont.load_default()

# 4. 자동 줄바꿈 로직 (Text Wrapping)
lines = []
words = text_input.split() # 띄어쓰기 기준으로 단어 분리
current_line = []

for word in words:
    # 현재 줄에 단어를 추가했을 때의 길이를 계산
    test_line = ' '.join(current_line + [word])
    # bbox를 통해 텍스트의 너비(width) 구하기
    bbox = draw.textbbox((0, 0), test_line, font=font)
    text_width = bbox[2] - bbox[0]
    
    # 이미지 너비에서 여백을 뺀 것보다 길면 줄바꿈
    if text_width < (image_width - max_width_padding):
        current_line.append(word)
    else:
        lines.append(' '.join(current_line))
        current_line = [word]
lines.append(' '.join(current_line)) # 마지막 줄 추가

# 5. 텍스트 그리기 (중앙 정렬)
# 전체 텍스트 높이 계산하여 수직 중앙 정렬하기
line_height = bbox[3] - bbox[1] + 15 # 줄 간격 15px
total_text_height = len(lines) * line_height
current_y = (image_height - total_text_height) // 2 

for line in lines:
    # 수평 중앙 정렬 계산
    bbox = draw.textbbox((0, 0), line, font=font)
    text_width = bbox[2] - bbox[0]
    current_x = (image_width - text_width) // 2
    
    # 글자 쓰기 (검은 테두리 + 흰 글씨 효과 예시)
    draw.text((current_x-1, current_y), line, font=font, fill="black")
    draw.text((current_x+1, current_y), line, font=font, fill="black")
    draw.text((current_x, current_y-1), line, font=font, fill="black")
    draw.text((current_x, current_y+1), line, font=font, fill="black")
    draw.text((current_x, current_y), line, font=font, fill="white")
    
    current_y += line_height

# 저장
img.save(output_path)
print(f"생성된 파일: {output_path}")
