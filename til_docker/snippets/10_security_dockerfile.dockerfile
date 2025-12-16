# ============================================
# Docker 보안 Best Practice Dockerfile
# 비-root 사용자, 최소 권한, 시크릿 관리
# ============================================

# syntax=docker/dockerfile:1.4


# ============================================
# 보안 위험: root로 실행 (사용하지 말 것)
# ============================================
# FROM python:3.12-slim
# WORKDIR /app
# COPY . .
# CMD ["python", "app.py"]
# 문제: 컨테이너가 root 권한으로 실행됨


# ============================================
# 안전: 비-root 사용자로 실행 (권장)
# ============================================
FROM python:3.12-slim AS secure-base

WORKDIR /app

# 필요한 패키지만 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 비-root 사용자 생성 및 권한 설정
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 비-root 사용자로 전환
USER appuser

CMD ["python", "app.py"]


# ============================================
# 최소 권한 원칙 적용
# ============================================
FROM python:3.12-slim AS minimal-permissions

WORKDIR /app

# 필요한 파일만 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ /app/

# 불필요한 권한 제거
RUN chmod 700 /app/scripts/*.sh 2>/dev/null || true && \
    chmod 600 /app/config/*.conf 2>/dev/null || true

# 비-root 사용자
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["python", "app.py"]


# ============================================
# 시크릿 관리 - 절대 하지 말아야 할 것
# ============================================
# 비밀번호가 이미지 레이어에 영구 저장됨 - 절대 금지!
# ENV DATABASE_PASSWORD=secret123
# COPY .env /app/.env


# ============================================
# 시크릿 관리 - 올바른 방법 1: 빌드 시크릿 사용
# ============================================
FROM python:3.12-slim AS with-build-secret

WORKDIR /app

COPY requirements.txt .

# 빌드 시크릿으로 Private PyPI 인증 (이미지에 저장되지 않음)
RUN --mount=type=secret,id=pip_conf,target=/root/.pip/pip.conf \
    pip install --no-cache-dir -r requirements.txt

# 또는 환경변수로 시크릿 사용
# RUN --mount=type=secret,id=db_password \
#     export DB_PASSWORD=$(cat /run/secrets/db_password) && \
#     echo "빌드 작업 수행"

COPY . .

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["python", "app.py"]

# 빌드 명령어:
# docker build --secret id=pip_conf,src=./pip.conf -t myapp .


# ============================================
# 프로덕션 보안 Dockerfile (종합)
# ============================================
FROM python:3.12-slim AS production-secure

# 메타데이터
LABEL maintainer="team@example.com"
LABEL version="1.0"

WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 것만 설치
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 의존성 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app/ /app/

# 비-root 사용자 생성
RUN useradd -m -u 1000 -s /bin/false appuser && \
    chown -R appuser:appuser /app

# 비-root 사용자로 전환
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]


# ============================================
# 베이스 이미지 선택 가이드
# ============================================
# python:3.12-slim     (~150MB) - Debian 기반, 균형 잡힌 선택
# python:3.12-alpine   (~50MB)  - Alpine Linux, 최소 크기
# gcr.io/distroless/python3 (~50MB) - Google Distroless, 셸 없음 (가장 안전)
# python:3.12          (~900MB) - 개발용, 디버깅 도구 포함


# ============================================
# 이미지 취약점 스캔 명령어
# ============================================
# docker scan myapp:latest           # Docker Hub
# trivy image myapp:latest           # Trivy (오픈소스)
# grype myapp:latest                 # Grype (오픈소스)
# snyk container test myapp:latest   # Snyk (상용)
