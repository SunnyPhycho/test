#!/usr/bin/env sh
set -e

# 6개 엔드포인트를 각각 내부 포트에서 실행
PORT=8001 python api/index.py &
PORT=8002 python api/status.py &
PORT=8003 python api/sns.py &
PORT=8004 python api/order.py &
PORT=8005 python api/relation.py &
PORT=8006 python api/shop.py &

# Nginx가 Render가 준 PORT로 listen 하도록 치환
envsubst '$PORT' < nginx.conf.template > /etc/nginx/nginx.conf

# 포그라운드로 실행 (Render는 포그라운드 프로세스 1개 필요)
nginx -g "daemon off;"
