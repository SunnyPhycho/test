FROM python:3.10-slim

# nginx + envsubst
RUN apt-get update && apt-get install -y --no-install-recommends nginx gettext-base \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# pillow 설치
RUN pip install --no-cache-dir -r requirements.txt

# start.sh 실행권한
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
