# Docker 스니펫 라이브러리

실무에서 바로 활용 가능한 Docker 코드 스니펫 모음집입니다. 개발부터 프로덕션 배포, 보안, CI/CD까지 Docker 운영의 모든 측면을 다룹니다.

---

## 목차

1. [파일 목록](#파일-목록)
2. [각 파일 상세 설명](#각-파일-상세-설명)
3. [빠른 참조 가이드](#빠른-참조-가이드)
4. [활용 워크플로우](#활용-워크플로우)

---

## 파일 목록

| 파일명 | 설명 | 난이도 |
|--------|------|--------|
| `01_basic_commands.sh` | Docker CLI 기본 명령어 모음 | 초급 |
| `02_dockerfile_basic.dockerfile` | Dockerfile 기본 템플릿 | 초급 |
| `03_compose_basic.yml` | Docker Compose 기본 구성 | 초급 |
| `04_buildkit_features.dockerfile` | BuildKit 캐시 및 시크릿 마운트 | 중급 |
| `05_multistage_builds.dockerfile` | 멀티 스테이지 빌드 패턴 | 중급 |
| `06_compose_environments.yml` | 환경별 Compose 설정 분리 | 중급 |
| `07_network_examples.yml` | 네트워크 격리 및 보안 계층 | 중급 |
| `08_volume_examples.yml` | 볼륨 영속화 및 백업 전략 | 중급 |
| `09_deploy_scripts.sh` | 배포 및 롤백 스크립트 | 고급 |
| `10_security_dockerfile.dockerfile` | 보안 Best Practice | 고급 |
| `11_github_actions_cicd.yml` | GitHub Actions CI/CD 파이프라인 | 고급 |
| `12_ecr_lifecycle_policy.json` | AWS ECR 이미지 수명 주기 정책 | 고급 |
| `13_dockerignore.txt` | .dockerignore 템플릿 | 초급 |

---

## 각 파일 상세 설명

### 01_basic_commands.sh - Docker CLI 기본 명령어

**설명:**
Docker 명령어의 모든 것을 담은 치트시트. 이미지, 컨테이너, 네트워크, 볼륨, Docker Compose 명령어를 체계적으로 정리했습니다.

**사용 상황:**
- Docker 명령어를 잊어버렸을 때 빠르게 참조
- 팀원에게 Docker 명령어 가이드 제공
- 스크립트 작성 시 참조 자료

**주요 섹션:**
- **이미지 관리**: `docker build`, `docker tag`, `docker rmi`, `docker image prune`
- **컨테이너 관리**: `docker run`, `docker ps`, `docker logs`, `docker exec`
- **Compose 관리**: `docker-compose up`, `docker-compose logs`, `docker-compose down`
- **시스템 정리**: `docker system prune`, `docker system df`

**활용 예시:**
```bash
# 파일을 소스하여 명령어 실행
source 01_basic_commands.sh

# 또는 필요한 명령어만 복사하여 사용
docker ps -a
docker logs -f myapp
docker exec -it myapp /bin/bash
```

**팁:**
- `docker system df`로 디스크 사용량을 주기적으로 체크
- `docker-compose --profile dev up -d`로 선택적 서비스 실행 가능

---

### 02_dockerfile_basic.dockerfile - Dockerfile 기본 템플릿

**설명:**
Python 애플리케이션용 기본 Dockerfile 템플릿. 레이어 캐싱 최적화 원칙을 적용한 표준 구조입니다.

**사용 상황:**
- 새 프로젝트 시작 시 Dockerfile 기본 뼈대
- Dockerfile 명령어 참조 가이드
- 초급 개발자를 위한 교육 자료

**사용 방법:**
```bash
# 1. 프로젝트 루트에 복사
cp 02_dockerfile_basic.dockerfile Dockerfile

# 2. 필요에 맞게 수정
# - 베이스 이미지 버전
# - 환경변수
# - 실행 명령어

# 3. 빌드
docker build -t myapp:latest .
```

**주요 명령어 설명:**
- `FROM`: 베이스 이미지 지정 (예: `python:3.12-slim`)
- `WORKDIR`: 작업 디렉토리 설정
- `COPY requirements.txt .`: 의존성 파일만 먼저 복사 (캐싱 최적화)
- `RUN pip install`: 의존성 설치
- `COPY . .`: 애플리케이션 코드 복사
- `CMD`: 컨테이너 시작 시 실행 명령

**최적화 팁:**
- 자주 변경되지 않는 레이어(의존성)를 먼저 작성
- `--no-cache-dir` 플래그로 불필요한 캐시 방지
- 한 줄에 여러 명령을 `&&`로 연결하여 레이어 최소화

---

### 03_compose_basic.yml - Docker Compose 기본 구성

**설명:**
웹 + DB + Redis 구성을 담은 프로덕션급 Compose 템플릿. 서비스 간 의존성, 네트워크, 볼륨 설정이 포함되어 있습니다.

**사용 상황:**
- 로컬 개발 환경 구축
- 마이크로서비스 아키텍처 기본 구성
- 헬스체크 및 재시작 정책이 필요한 서비스

**사용 방법:**
```bash
# 1. 프로젝트 루트에 복사
cp 03_compose_basic.yml docker-compose.yml

# 2. 서비스 설정 커스터마이징
# - 환경변수
# - 포트 매핑
# - 볼륨 경로

# 3. 실행
docker-compose up -d

# 4. 로그 확인
docker-compose logs -f web
```

**주요 구성 요소:**
```yaml
services:
  web:
    build: .
    ports: ["8000:8000"]
    depends_on: [db, redis]  # 시작 순서 보장
    volumes: ["./app:/app"]  # 코드 핫 리로드
    restart: unless-stopped  # 자동 재시작

  db:
    image: postgres:15-alpine
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine

networks:
  backend:
    driver: bridge

volumes:
  postgres_data:
```

**헬스체크 예시:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

### 04_buildkit_features.dockerfile - BuildKit 고급 기능

**설명:**
Docker BuildKit의 강력한 기능인 캐시 마운트, 시크릿 마운트, SSH 마운트를 활용한 고급 빌드 템플릿. 빌드 시간을 50-80% 단축할 수 있습니다.

**사용 상황:**
- Private PyPI 서버나 NPM 레지스트리 인증
- Private Git 저장소 클론
- 빌드 시간 최적화

**활성화 방법:**
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

**캐시 마운트 (빌드 시간 50-80% 단축):**
```dockerfile
# pip 캐시를 빌드 간 공유
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

**시크릿 마운트 (인증 정보 보안):**
```dockerfile
# Private PyPI 인증 (이미지에 저장되지 않음!)
RUN --mount=type=secret,id=pip_conf,target=/root/.pip/pip.conf \
    pip install -r requirements.txt
```

빌드 명령어:
```bash
docker build --secret id=pip_conf,src=./pip.conf -t myapp .
```

**SSH 마운트 (Private Git 저장소):**
```dockerfile
RUN --mount=type=ssh \
    git clone git@github.com:private/repo.git
```

빌드 명령어:
```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa
docker build --ssh default -t myapp .
```

**실전 적용:**
```bash
# 1. BuildKit 활성화
export DOCKER_BUILDKIT=1

# 2. 시크릿 파일 준비
echo "[global]
index-url = https://user:pass@pypi.example.com/simple" > pip.conf

# 3. 빌드
docker build --secret id=pip_conf,src=./pip.conf -t myapp .

# 4. pip.conf는 이미지에 남지 않음 (안전!)
```

---

### 05_multistage_builds.dockerfile - 멀티 스테이지 빌드

**설명:**
빌드 환경과 런타임 환경을 분리하여 이미지 크기를 50-90% 감소시키는 멀티 스테이지 빌드 패턴.

**사용 상황:**
- 프로덕션 이미지 크기 최적화
- 빌드 도구는 필요하지만 런타임에는 불필요한 경우
- 여러 서비스가 공통 의존성을 공유하는 경우

**기본 패턴:**
```dockerfile
# Stage 1: 빌드 환경 (900MB)
FROM python:3.12 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .

# Stage 2: 런타임 환경 (150MB)
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /root/.local /root/.local  # 빌드 결과물만 복사
COPY --from=builder /app .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

**프로덕션 권장 패턴:**
```dockerfile
# Stage 1: 베이스 런타임
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: 빌드
FROM base AS builder
RUN apt-get update && apt-get install -y build-essential
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install -r requirements.txt

# Stage 3: 최종 런타임
FROM base AS production
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY . /app/
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
CMD ["python", "app.py"]
```

**특정 스테이지만 빌드:**
```bash
# 웹 서버 이미지
docker build --target web -t myapp:web .

# 워커 이미지
docker build --target worker -t myapp:worker .

# 개발 이미지 (디버거 포함)
docker build --target development -t myapp:dev .
```

**효과:**
- 빌드 이미지: 900MB → 런타임 이미지: 150MB (83% 감소)
- 배포 속도 향상
- 보안 강화 (빌드 도구 제거)

---

### 06_compose_environments.yml - 환경별 Compose 설정

**설명:**
개발, 스테이징, 프로덕션 환경별로 Compose 설정을 분리하는 패턴. 프로필 기능으로 선택적 서비스 실행도 지원합니다.

**사용 상황:**
- 환경별 다른 설정이 필요한 경우
- 개발 환경에서만 디버거, 모니터링 툴 실행
- 프로덕션에서 리소스 제한 적용

**디렉토리 구조:**
```
project/
├── docker-compose.yml          # 베이스 설정
├── docker-compose.dev.yml      # 개발 환경
└── docker-compose.prod.yml     # 프로덕션 환경
```

**개발 환경 (docker-compose.dev.yml):**
```yaml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app:cached       # 코드 핫 리로드
      - /app/.venv          # 가상환경은 컨테이너 내 유지
    ports:
      - "5678:5678"         # 디버거 포트
    environment:
      - DEBUG=true
```

**프로덕션 환경 (docker-compose.prod.yml):**
```yaml
services:
  web:
    image: myregistry.com/myapp:${VERSION}
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**사용법:**
```bash
# 개발 환경
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 프로덕션 환경
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**프로필 활용 (선택적 서비스 실행):**
```yaml
services:
  web:
    image: myapp
    # 항상 실행

  debug:
    image: myapp:dev
    profiles: ["dev"]
    # 개발 시에만 실행

  prometheus:
    image: prom/prometheus
    profiles: ["monitoring"]
    # 모니터링 프로필 활성화 시에만 실행
```

실행:
```bash
# 기본 서비스만
docker-compose up -d

# 개발 프로필 포함
docker-compose --profile dev up -d

# 여러 프로필 동시
docker-compose --profile dev --profile monitoring up -d
```

---

### 07_network_examples.yml - 네트워크 격리 및 보안

**설명:**
마이크로서비스 아키텍처를 위한 네트워크 격리 패턴. DMZ, 애플리케이션 계층, 데이터 계층을 분리하여 보안을 강화합니다.

**사용 상황:**
- 마이크로서비스 간 통신 제어
- 데이터베이스 외부 접근 차단
- 보안 계층 분리 (DMZ, App, Data)

**기본 네트워크 격리:**
```yaml
services:
  web:
    networks:
      - frontend
      - backend

  api:
    networks:
      - backend

  db:
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # 외부 접근 차단
```

**보안 계층 분리 (3-Tier Architecture):**
```yaml
services:
  # DMZ (인터넷 접근)
  nginx:
    networks: [dmz]
    ports: ["80:80", "443:443"]

  # 애플리케이션 계층
  web:
    networks: [dmz, app-tier]

  api:
    networks: [app-tier, data-tier]

  # 데이터 계층 (완전 격리)
  db:
    networks: [data-tier]

networks:
  dmz:
    driver: bridge
  app-tier:
    driver: bridge
    internal: true
  data-tier:
    driver: bridge
    internal: true
```

**포트 노출 설정:**
```yaml
services:
  web:
    ports:
      - "80:80"                    # 모든 인터페이스
      - "127.0.0.1:8080:8080"     # 로컬만 접근 가능

  api:
    expose:
      - "3000"                     # 컨테이너 간 통신만
```

**네트워크 별칭 (Service Discovery):**
```yaml
services:
  web:
    networks:
      backend:
        aliases:
          - webserver
          - frontend  # api 서비스가 'frontend' 이름으로 접근 가능
```

---

### 08_volume_examples.yml - 볼륨 영속화 및 백업

**설명:**
데이터 영속화를 위한 볼륨 전략. Named Volume, Bind Mount, tmpfs 사용법과 백업/복구 명령어를 포함합니다.

**사용 상황:**
- 데이터베이스 데이터 영속화
- 개발 환경 코드 핫 리로드
- 컨테이너 간 데이터 공유

**Named Volume (프로덕션 권장):**
```yaml
services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - postgres_backup:/backup

volumes:
  postgres_data:
    driver: local
```

**Bind Mount (개발 환경):**
```yaml
services:
  web:
    volumes:
      - ./app:/app:cached      # 읽기 성능 우선
      - ./config:/config:ro    # 읽기 전용
      - /app/.venv             # 가상환경 제외
```

마운트 옵션:
- `cached`: 호스트 → 컨테이너 (읽기 성능 우선)
- `delegated`: 컨테이너 → 호스트 (쓰기 성능 우선)
- `ro`: 읽기 전용
- `rw`: 읽기/쓰기 (기본값)

**tmpfs (메모리 기반 임시 저장소):**
```yaml
services:
  cache:
    image: redis
    tmpfs:
      - /data:size=2G  # 메모리 기반 (최고 성능, 재시작 시 소멸)
```

**볼륨 백업:**
```bash
docker run --rm \
  -v mydata:/data \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/backup-$(date +%Y%m%d).tar.gz -C /data .
```

**볼륨 복구:**
```bash
docker run --rm \
  -v mydata:/data \
  -v $(pwd):/backup \
  alpine \
  sh -c "cd /data && tar xzf /backup/backup-20250112.tar.gz"
```

**볼륨 복제:**
```bash
docker run --rm \
  -v source_volume:/from \
  -v target_volume:/to \
  alpine \
  sh -c "cp -av /from/. /to/"
```

---

### 09_deploy_scripts.sh - 배포 및 롤백 스크립트

**설명:**
프로덕션 배포를 위한 실전 스크립트 모음. 기본 배포, 롤백, Blue-Green 배포, 자동 태그 생성 기능을 제공합니다.

**사용 상황:**
- 프로덕션 서버 무중단 배포
- 배포 실패 시 자동 롤백
- Blue-Green 배포로 안전한 릴리스

**기본 배포:**
```bash
source 09_deploy_scripts.sh

# 버전 1.2.3 배포
deploy 1.2.3

# 자동으로 수행되는 단계:
# 1. 레지스트리 로그인
# 2. 이미지 Pull
# 3. 기존 컨테이너 정지
# 4. 새 컨테이너 시작
# 5. 헬스체크 (30초 동안 시도)
```

**롤백 시나리오:**
```bash
# 1. 배포 전 상태 저장
save_deployment_state

# 2. 배포 실행
deploy 2.0.0

# 3. 문제 발생 시 롤백
rollback
# → 이전 이미지로 자동 복구
```

**Blue-Green 배포:**
```bash
blue_green_deploy

# 동작 원리:
# 1. 새 환경(Green) 시작
# 2. 헬스체크 통과 확인
# 3. 로드밸런서 전환
# 4. 이전 환경(Blue) 정리
# 5. 현재 환경 업데이트
```

**자동 태그 생성:**
```bash
generate_tags

# 브랜치별 태그 전략:
# main/master   → prod-1.0.0
# dev/develop   → dev-20250116-abc123
# staging       → staging-1.0.0-rc20250116
# feature/auth  → feature-auth-abc123
```

**Docker Compose 배포:**
```bash
compose_deploy 1.2.3

# 이미지 pull 및 재시작
# 무중단 배포 (웹 서비스만):
# VERSION=1.2.3 docker-compose up -d --no-deps --build web
```

---

### 10_security_dockerfile.dockerfile - 보안 Best Practice

**설명:**
Docker 보안 권장 사항을 모두 적용한 프로덕션급 Dockerfile. 비-root 사용자, 최소 권한, 시크릿 관리를 포함합니다.

**사용 상황:**
- 프로덕션 환경 이미지 빌드
- 보안 감사 통과가 필요한 경우
- 최소 권한 원칙 적용

**절대 하지 말아야 할 것:**
```dockerfile
# ❌ 절대 금지!
ENV DATABASE_PASSWORD=secret123
COPY .env /app/.env

# 문제: 비밀번호가 이미지 레이어에 영구 저장됨
```

**올바른 방법:**
```dockerfile
# ✅ 비-root 사용자로 실행 (권장)
FROM python:3.12-slim

WORKDIR /app

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
```

**시크릿 관리 (BuildKit Secret Mount):**
```dockerfile
# Private PyPI 인증 (이미지에 저장되지 않음)
RUN --mount=type=secret,id=pip_conf,target=/root/.pip/pip.conf \
    pip install -r requirements.txt
```

빌드:
```bash
docker build --secret id=pip_conf,src=./pip.conf -t myapp .
```

**프로덕션 종합 Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY app/ /app/

# 비-root 사용자
RUN useradd -m -u 1000 -s /bin/false appuser && \
    chown -R appuser:appuser /app
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
```

**베이스 이미지 선택 가이드:**
- `python:3.12-slim` (~150MB): Debian 기반, 균형 잡힌 선택
- `python:3.12-alpine` (~50MB): Alpine Linux, 최소 크기
- `gcr.io/distroless/python3` (~50MB): Google Distroless, 가장 안전 (셸 없음)

**취약점 스캔:**
```bash
docker scan myapp:latest
trivy image myapp:latest
```

---

### 11_github_actions_cicd.yml - GitHub Actions CI/CD

**설명:**
GitHub Actions를 사용한 Docker 이미지 빌드 및 배포 파이프라인. 멀티 아키텍처 빌드, ECR 푸시, 레지스트리 캐싱을 지원합니다.

**사용 상황:**
- GitHub 저장소에서 자동 빌드 및 배포
- 멀티 아키텍처 이미지 (AMD64, ARM64)
- 프로덕션 배포 자동화

**워크플로우 파일 위치:**
```
.github/workflows/docker.yml
```

**기본 워크플로우:**
```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [main, dev]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: myregistry.com
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: myregistry.com/myapp:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**멀티 아키텍처 빌드 (AMD64 + ARM64):**
```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: myregistry.com/myapp:latest
```

**AWS ECR 로그인:**
```yaml
- name: Login to AWS ECR
  uses: aws-actions/amazon-ecr-login@v2
  env:
    AWS_REGION: ${{ secrets.AWS_REGION }}
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

**GitHub Container Registry 로그인:**
```yaml
- name: Login to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

**시크릿을 사용한 빌드:**
```yaml
- name: Build with secrets
  uses: docker/build-push-action@v5
  with:
    secrets: |
      pip_conf=${{ secrets.PIP_CONF }}
```

**필요한 GitHub Secrets 설정:**
1. `Settings` → `Secrets and variables` → `Actions`
2. 추가할 시크릿:
   - `REGISTRY_USERNAME`
   - `REGISTRY_PASSWORD`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`

---

### 12_ecr_lifecycle_policy.json - AWS ECR 수명 주기 정책

**설명:**
AWS ECR에서 오래된 이미지를 자동으로 삭제하여 스토리지 비용을 절감하는 정책 템플릿.

**사용 상황:**
- ECR 스토리지 비용 최적화
- 오래된 개발/테스트 이미지 자동 정리
- 프로덕션 이미지는 보존하면서 불필요한 이미지 삭제

**정책 내용:**
- **프로덕션 이미지**: 최근 10개만 유지
- **개발 이미지**: 7일 후 삭제
- **스테이징 이미지**: 14일 후 삭제
- **Feature 브랜치 이미지**: 3일 후 삭제
- **태그 없는 이미지**: 1일 후 삭제

**정책 적용:**
```bash
# 정책 적용
aws ecr put-lifecycle-policy \
  --repository-name myapp \
  --lifecycle-policy-text file://12_ecr_lifecycle_policy.json

# 정책 확인
aws ecr get-lifecycle-policy --repository-name myapp

# 정책 삭제
aws ecr delete-lifecycle-policy --repository-name myapp
```

**예상 효과:**
- 개발 이미지가 하루 3개씩 쌓인다면: 7일 후부터 자동 정리
- 월 100개 이미지 축적 → 월 20개로 감소
- 스토리지 비용 약 80% 절감

**정책 커스터마이징:**
```json
{
  "rulePriority": 1,
  "description": "프로덕션 이미지 최근 10개만 유지",
  "selection": {
    "tagStatus": "tagged",
    "tagPrefixList": ["prod"],  // 태그 접두사
    "countType": "imageCountMoreThan",
    "countNumber": 10  // 유지할 이미지 개수
  },
  "action": {
    "type": "expire"
  }
}
```

---

### 13_dockerignore.txt - .dockerignore 템플릿

**설명:**
빌드 컨텍스트 크기를 40-70% 감소시키는 .dockerignore 템플릿. 불필요한 파일을 제외하여 빌드 속도를 향상시킵니다.

**사용 상황:**
- 모든 프로젝트의 Dockerfile과 함께 사용
- 빌드 컨텍스트가 느릴 때
- 시크릿 파일이 실수로 이미지에 포함되는 것을 방지

**사용 방법:**
```bash
# 프로젝트 루트에 복사
cp 13_dockerignore.txt .dockerignore

# 프로젝트에 맞게 커스터마이징
# - 특정 파일 추가/제외
# - 예외 규칙 설정
```

**주요 제외 항목:**
```
# 버전 관리
.git
.gitignore

# Python 캐시 및 빌드
__pycache__
*.pyc
.pytest_cache
dist/
build/

# 가상환경
.venv
venv

# 환경 설정 (시크릿)
.env
.env.*
secrets/
*.pem
*.key

# IDE
.vscode
.idea

# 테스트
tests/
test_*.py

# 문서
*.md
!README.md  # README만 포함

# Docker 관련
Dockerfile*
docker-compose*.yml
```

**효과 확인:**
```bash
docker build . -t test --no-cache

# 적용 전: Sending build context to Docker daemon  150MB
# 적용 후: Sending build context to Docker daemon  45MB
```

**예외 규칙 설정:**
```
# 모든 .md 파일 제외
*.md

# README.md만 포함
!README.md
```

---

## 빠른 참조 가이드

### 상황별 파일 선택

#### 1. 프로젝트 초기 설정
**"새 프로젝트를 Docker화하고 싶어요"**
```
순서:
1. 13_dockerignore.txt → .dockerignore 복사
2. 02_dockerfile_basic.dockerfile → Dockerfile 생성
3. 03_compose_basic.yml → docker-compose.yml 생성
4. docker-compose up -d 실행
```

#### 2. 개발 환경 구축
**"로컬 개발 환경을 만들고 싶어요"**
```
필요한 파일:
- 03_compose_basic.yml: 기본 서비스 구성
- 06_compose_environments.yml: 개발 환경 설정
- 08_volume_examples.yml: 코드 핫 리로드 볼륨

실행:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

#### 3. 프로덕션 배포
**"프로덕션에 안전하게 배포하고 싶어요"**
```
필요한 파일:
- 05_multistage_builds.dockerfile: 최적화된 이미지
- 10_security_dockerfile.dockerfile: 보안 강화
- 09_deploy_scripts.sh: 배포 스크립트
- 11_github_actions_cicd.yml: CI/CD 파이프라인

단계:
1. Dockerfile 작성 (05, 10 참조)
2. CI/CD 설정 (11)
3. 배포 스크립트로 실행 (09)
```

#### 4. 빌드 시간 최적화
**"Docker 빌드가 너무 느려요"**
```
해결 방법:
- 13_dockerignore.txt: 불필요한 파일 제외 (40-70% 개선)
- 04_buildkit_features.dockerfile: 캐시 마운트 (50-80% 개선)
- 05_multistage_builds.dockerfile: 레이어 캐싱

실행:
export DOCKER_BUILDKIT=1
docker build --cache-from type=registry,ref=myapp:cache .
```

#### 5. 보안 강화
**"Docker 이미지 보안을 강화하고 싶어요"**
```
필요한 파일:
- 10_security_dockerfile.dockerfile: 비-root 사용자, 최소 권한
- 04_buildkit_features.dockerfile: 시크릿 마운트
- 07_network_examples.yml: 네트워크 격리

체크리스트:
✓ 비-root 사용자로 실행
✓ .env 파일 이미지에 포함 금지
✓ 데이터베이스 외부 접근 차단
✓ 취약점 스캔 (trivy, docker scan)
```

#### 6. 마이크로서비스 아키텍처
**"여러 서비스를 Docker로 구성하고 싶어요"**
```
필요한 파일:
- 07_network_examples.yml: 네트워크 격리
- 08_volume_examples.yml: 데이터 공유
- 05_multistage_builds.dockerfile: 공통 레이어 재사용

구조:
services:
  frontend → public 네트워크
  api-gateway → public + internal 네트워크
  auth-service → internal 네트워크
  db → database 네트워크 (완전 격리)
```

#### 7. CI/CD 구축
**"자동 빌드/배포를 구축하고 싶어요"**
```
필요한 파일:
- 11_github_actions_cicd.yml: GitHub Actions 워크플로우
- 09_deploy_scripts.sh: 배포 스크립트
- 12_ecr_lifecycle_policy.json: ECR 이미지 정리

단계:
1. .github/workflows/docker.yml 생성 (11)
2. GitHub Secrets 설정
3. ECR 라이프사이클 정책 적용 (12)
4. 배포 스크립트 구성 (09)
```

#### 8. 비용 최적화
**"Docker 이미지 스토리지 비용을 줄이고 싶어요"**
```
해결 방법:
- 05_multistage_builds.dockerfile: 이미지 크기 50-90% 감소
- 13_dockerignore.txt: 빌드 컨텍스트 40-70% 감소
- 12_ecr_lifecycle_policy.json: ECR 스토리지 80% 절감

예상 효과:
빌드 이미지 900MB → 런타임 150MB
월 스토리지 비용 $50 → $10
```

---

## 활용 워크플로우

### Workflow 1: 새 프로젝트 시작

```bash
# 1. .dockerignore 설정
cp claudedocs/dockers/13_dockerignore.txt .dockerignore

# 2. Dockerfile 생성
cp claudedocs/dockers/02_dockerfile_basic.dockerfile Dockerfile

# 3. docker-compose.yml 생성
cp claudedocs/dockers/03_compose_basic.yml docker-compose.yml

# 4. 개발 환경 실행
docker-compose up -d

# 5. 로그 확인
docker-compose logs -f web
```

### Workflow 2: 프로덕션 배포 준비

```bash
# 1. 멀티 스테이지 Dockerfile 작성
참조: 05_multistage_builds.dockerfile

# 2. 보안 강화
참조: 10_security_dockerfile.dockerfile

# 3. BuildKit 캐시 활성화
export DOCKER_BUILDKIT=1
docker build --cache-from type=registry,ref=myregistry.com/myapp:cache \
             --cache-to type=registry,ref=myregistry.com/myapp:cache \
             -t myregistry.com/myapp:1.0.0 .

# 4. 배포
source claudedocs/dockers/09_deploy_scripts.sh
deploy 1.0.0

# 5. 롤백 준비
save_deployment_state
```

### Workflow 3: CI/CD 파이프라인 구축

```bash
# 1. GitHub Actions 워크플로우 생성
mkdir -p .github/workflows
cp claudedocs/dockers/11_github_actions_cicd.yml .github/workflows/docker.yml

# 2. GitHub Secrets 설정
# Settings → Secrets and variables → Actions
# - REGISTRY_USERNAME
# - REGISTRY_PASSWORD
# - AWS_ACCESS_KEY_ID (ECR 사용 시)
# - AWS_SECRET_ACCESS_KEY (ECR 사용 시)

# 3. ECR 라이프사이클 정책 적용
aws ecr put-lifecycle-policy \
  --repository-name myapp \
  --lifecycle-policy-text file://claudedocs/dockers/12_ecr_lifecycle_policy.json

# 4. 코드 푸시로 자동 빌드 트리거
git add .
git commit -m "Add CI/CD pipeline"
git push origin main
```

### Workflow 4: 환경별 배포

```bash
# 1. 환경별 Compose 파일 준비
docker-compose.yml              # 베이스
docker-compose.dev.yml          # 개발
docker-compose.prod.yml         # 프로덕션

# 2. 개발 환경 실행
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 3. 프로덕션 환경 실행
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. 프로필 활용
docker-compose --profile dev --profile monitoring up -d
```

### Workflow 5: Blue-Green 배포

```bash
# 1. 배포 스크립트 로드
source claudedocs/dockers/09_deploy_scripts.sh

# 2. 배포 전 상태 저장
save_deployment_state

# 3. Blue-Green 배포 실행
blue_green_deploy

# 4. 문제 발생 시 롤백
rollback
```

---

## 부록: Docker 명령어 치트시트

### 이미지 관련
```bash
docker images                          # 이미지 목록
docker build -t myapp:latest .        # 이미지 빌드
docker tag myapp:latest myapp:1.0.0   # 태그 추가
docker rmi myimage:latest             # 이미지 삭제
docker image prune -a                 # 사용하지 않는 이미지 정리
```

### 컨테이너 관련
```bash
docker ps                              # 실행 중인 컨테이너
docker ps -a                           # 모든 컨테이너
docker run -d --name myapp myimage    # 컨테이너 실행
docker stop myapp                      # 컨테이너 중지
docker rm myapp                        # 컨테이너 삭제
docker logs -f myapp                   # 로그 확인
docker exec -it myapp /bin/bash       # 컨테이너 접속
```

### Docker Compose 관련
```bash
docker-compose up -d                   # 서비스 시작
docker-compose down                    # 서비스 중지 및 삭제
docker-compose logs -f web            # 로그 확인
docker-compose restart web            # 서비스 재시작
docker-compose pull && docker-compose up -d  # 이미지 업데이트
```

### 네트워크 관련
```bash
docker network ls                      # 네트워크 목록
docker network create mynetwork       # 네트워크 생성
docker network inspect mynetwork      # 네트워크 상세 정보
```

### 볼륨 관련
```bash
docker volume ls                       # 볼륨 목록
docker volume create mydata           # 볼륨 생성
docker volume inspect mydata          # 볼륨 상세 정보
docker volume prune                   # 사용하지 않는 볼륨 정리
```

### 시스템 정리
```bash
docker system df                       # 디스크 사용량 확인
docker system prune -a --volumes      # 전체 정리 (주의!)
```
