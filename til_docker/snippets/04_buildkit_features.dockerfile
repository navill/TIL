# ============================================
# BuildKit 고급 기능 템플릿
# 캐시 마운트, 시크릿 마운트, SSH 마운트
# ============================================

# syntax=docker/dockerfile:1.4

# ------------------------------
# BuildKit 활성화 방법
# ------------------------------
# export DOCKER_BUILDKIT=1
# export COMPOSE_DOCKER_CLI_BUILD=1


# ============================================
# 캐시 마운트 (Cache Mount)
# 패키지 매니저 캐시를 빌드 간 공유하여 빌드 시간 50-80% 단축
# ============================================

# [APT 캐시 마운트] Debian/Ubuntu 패키지 관리자
# RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
#     --mount=type=cache,target=/var/lib/apt,sharing=locked \
#     apt-get update && apt-get install -y curl wget

# [PIP 캐시 마운트] Python 패키지 관리자
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install -r requirements.txt

# [Poetry 캐시 마운트] Python Poetry 패키지 관리자
# RUN --mount=type=cache,target=/root/.cache/pypoetry \
#     poetry install --no-dev


# ============================================
# Python 프로젝트 캐시 마운트 예제
# ============================================
FROM python:3.12-slim AS with-cache

WORKDIR /app

COPY requirements.txt .

# pip 캐시 마운트로 의존성 설치 최적화
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .


# ============================================
# 시크릿 마운트 (Secret Mount)
# 인증 정보를 이미지에 포함시키지 않고 빌드 시에만 사용
# ============================================

# [기본 시크릿 마운트]
# RUN --mount=type=secret,id=pip_conf,target=/root/.pip/pip.conf \
#     pip install -r requirements.txt

# [환경변수로 시크릿 사용]
# RUN --mount=type=secret,id=db_password \
#     export DB_PASSWORD=$(cat /run/secrets/db_password) && \
#     echo "빌드 작업 수행"

# 빌드 명령어:
# docker build --secret id=pip_conf,src=./pip.conf -t myapp .
# echo "$SECRET_VALUE" | docker build --secret id=secret_name,src=- -t myapp .


# ============================================
# Private PyPI 인증 예제
# ============================================
FROM python:3.12-slim AS with-secret

WORKDIR /app

COPY requirements.txt .

# 시크릿 마운트로 Private PyPI 인증
RUN --mount=type=secret,id=pip_conf,target=/root/.pip/pip.conf \
    pip install -r requirements.txt

COPY . .


# ============================================
# SSH 마운트 (SSH Mount)
# Private Git 저장소 접근 시 유용
# ============================================

# [SSH 마운트로 private repo 클론]
# RUN --mount=type=ssh \
#     git clone git@github.com:private/repo.git

# 빌드 명령어:
# eval $(ssh-agent -s)
# ssh-add ~/.ssh/id_rsa
# docker build --ssh default -t myapp .


# ============================================
# SSH 마운트 예제 (Private Repository 클론)
# ============================================
FROM python:3.12-slim AS with-ssh

WORKDIR /app

# SSH 마운트로 private repo 클론
RUN --mount=type=ssh \
    git clone git@github.com:private/repo.git /app/private-lib

COPY . .


# ============================================
# 복합 마운트 예제 (캐시 + 시크릿)
# ============================================
FROM python:3.12-slim AS combined

WORKDIR /app

COPY requirements.txt .

# 캐시 마운트와 시크릿 마운트를 함께 사용
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=secret,id=pip_conf,target=/root/.pip/pip.conf \
    pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
