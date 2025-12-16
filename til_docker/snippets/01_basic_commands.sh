#!/bin/bash
# ============================================
# Docker 기본 명령어 모음
# 자주 사용하는 Docker CLI 명령어 스니펫
# ============================================

# ------------------------------
# 이미지 관련 명령어
# ------------------------------

# 이미지 목록 확인
docker images

# 이미지 빌드
docker build -t myapp:latest .

# 이미지 태그 추가
docker tag myapp:latest myapp:1.0.0

# 이미지 삭제
docker rmi myimage:latest

# 사용하지 않는 이미지 정리
docker image prune -a

# ------------------------------
# 컨테이너 관련 명령어
# ------------------------------

# 컨테이너 실행 (백그라운드)
docker run -d --name myapp myimage:latest

# 컨테이너 실행 (포트 매핑 + 환경변수)
docker run -d \
    --name myapp \
    -p 8080:8080 \
    -e DEBUG=true \
    --env-file .env \
    myimage:latest

# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인 (중지된 컨테이너 포함)
docker ps -a

# 컨테이너 로그 확인
docker logs myapp

# 컨테이너 로그 실시간 확인
docker logs -f myapp

# 컨테이너 중지
docker stop myapp

# 컨테이너 재시작
docker restart myapp

# 컨테이너 삭제
docker rm myapp

# 컨테이너 강제 삭제 (실행 중이어도)
docker rm -f myapp

# 컨테이너 내부 접속
docker exec -it myapp /bin/bash

# 컨테이너 내부에서 명령 실행
docker exec myapp ls -la /app

# ------------------------------
# Docker Compose 명령어
# ------------------------------

# 서비스 시작 (백그라운드)
docker-compose up -d

# 서비스 로그 확인
docker-compose logs -f web

# 서비스 중지
docker-compose stop

# 서비스 제거 (컨테이너 삭제)
docker-compose down

# 서비스 제거 (볼륨까지 삭제)
docker-compose down -v

# 특정 서비스만 재시작
docker-compose restart web

# 스케일 조정
docker-compose up -d --scale web=3

# 이미지 Pull 후 컨테이너 재시작
docker-compose pull && docker-compose up -d

# 환경별 Compose 파일 사용
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 프로필 활성화
docker-compose --profile dev up -d
docker-compose --profile dev --profile monitoring up -d

# 환경변수 파일 지정
docker-compose --env-file .env.dev up -d

# ------------------------------
# 네트워크 관련 명령어
# ------------------------------

# 네트워크 목록 확인
docker network ls

# 네트워크 생성
docker network create mynetwork

# 네트워크 상세 정보 확인
docker network inspect mynetwork

# 컨테이너를 네트워크에 연결하여 실행
docker run -d --name web --network mynetwork nginx

# 네트워크 삭제
docker network rm mynetwork

# ------------------------------
# 볼륨 관련 명령어
# ------------------------------

# 볼륨 목록 확인
docker volume ls

# 볼륨 생성
docker volume create mydata

# 볼륨 상세 정보 확인
docker volume inspect mydata

# 볼륨 삭제
docker volume rm mydata

# 사용하지 않는 볼륨 정리
docker volume prune

# Named Volume으로 컨테이너 실행
docker run -d \
    --name db \
    -v mydata:/var/lib/postgresql/data \
    postgres

# Bind Mount로 컨테이너 실행
docker run -d \
    --name dev \
    -v $(pwd):/app \
    myapp

# 읽기 전용 마운트
docker run -d \
    --name web \
    -v /host/config:/etc/config:ro \
    nginx

# ------------------------------
# 시스템 정리 명령어
# ------------------------------

# 중지된 컨테이너 삭제
docker container prune

# 사용하지 않는 이미지 삭제
docker image prune -a

# 사용하지 않는 볼륨 삭제
docker volume prune

# 사용하지 않는 네트워크 삭제
docker network prune

# 전체 시스템 정리 (주의!)
docker system prune -a --volumes

# 디스크 사용량 확인
docker system df
