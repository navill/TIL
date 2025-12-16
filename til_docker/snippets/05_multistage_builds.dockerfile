# ============================================
# 멀티 스테이지 빌드 템플릿
# 빌드 환경과 런타임 환경을 분리하여 이미지 크기 50-90% 감소
# ============================================

# syntax=docker/dockerfile:1.4


# ============================================
# 기본 멀티 스테이지 빌드
# ============================================

# Stage 1: 빌드 환경 (빌드 도구 포함)
FROM python:3.12 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .

# Stage 2: 런타임 환경 (최소 이미지)
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]

# 결과: 빌드 이미지(900MB) → 런타임 이미지(150MB)


# ============================================
# Python 프로덕션 빌드 (권장 패턴)
# ============================================

# Stage 1: 베이스 런타임
FROM python:3.12-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 2: 빌드 환경
FROM base AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 의존성 파일만 복사 (캐시 최적화)
COPY requirements.txt .

# 가상환경 생성 및 의존성 설치
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 3: 최종 런타임
FROM base AS production

# 빌드 스테이지에서 가상환경만 복사
COPY --from=builder /opt/venv /opt/venv

# PATH 설정
ENV PATH="/opt/venv/bin:$PATH"

# 애플리케이션 코드 복사
COPY . /app/

# 비-root 사용자 생성 (보안)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "app.py"]


# ============================================
# 공통 레이어 재사용 (여러 서비스가 같은 의존성 공유)
# ============================================

# Stage 1: 베이스 이미지
# FROM python:3.12-slim AS base-shared
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends curl && \
#     rm -rf /var/lib/apt/lists/*
# WORKDIR /app

# Stage 2: 공통 의존성
# FROM base-shared AS dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: 웹 서버
# FROM dependencies AS web
# COPY web/ /app/
# USER nobody
# CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]

# Stage 4: 워커
# FROM dependencies AS worker
# COPY worker/ /app/
# USER nobody
# CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]

# Stage 5: 스케줄러
# FROM dependencies AS scheduler
# COPY scheduler/ /app/
# USER nobody
# CMD ["celery", "-A", "tasks", "beat", "--loglevel=info"]

# 빌드 방법:
# docker build --target web -t myapp:web .
# docker build --target worker -t myapp:worker .
# docker build --target scheduler -t myapp:scheduler .


# ============================================
# 개발/프로덕션 환경 분리
# ============================================

# FROM python:3.12-slim AS env-base
# WORKDIR /app
# COPY requirements.txt .

# 개발 환경
# FROM env-base AS development
# RUN pip install -r requirements.txt && \
#     pip install debugpy pytest pytest-cov
# COPY . .
# CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "app.py"]

# 프로덕션 환경
# FROM env-base AS prod-env
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# RUN useradd -m appuser && chown -R appuser:appuser /app
# USER appuser
# CMD ["gunicorn", "app:app"]

# 빌드 방법:
# docker build --target development -t myapp:dev .
# docker build --target prod-env -t myapp:prod .
