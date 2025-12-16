#!/bin/bash
# ============================================
# Docker 배포 스크립트 모음
# 기본 배포, 롤백, Blue-Green 배포
# ============================================


# ============================================
# 기본 배포 스크립트
# ============================================
deploy() {
    local REGISTRY="${REGISTRY:-myregistry.com}"
    local APP_NAME="${APP_NAME:-myapp}"
    local VERSION="${1:-latest}"

    echo "Deploying ${APP_NAME}:${VERSION}..."

    # 1. 레지스트리 로그인
    docker login ${REGISTRY}

    # 2. 이미지 Pull
    docker pull ${REGISTRY}/${APP_NAME}:${VERSION}

    # 3. 기존 컨테이너 정지
    docker stop ${APP_NAME} 2>/dev/null || true
    docker rm ${APP_NAME} 2>/dev/null || true

    # 4. 새 컨테이너 시작
    docker run -d \
        --name ${APP_NAME} \
        --restart unless-stopped \
        -p 8080:8080 \
        --env-file .env \
        ${REGISTRY}/${APP_NAME}:${VERSION}

    # 5. 헬스체크
    for i in {1..30}; do
        if curl -f http://localhost:8080/health; then
            echo "Deployment successful!"
            return 0
        fi
        sleep 2
    done

    echo "Health check failed!"
    return 1
}


# ============================================
# 롤백 스크립트
# ============================================
DEPLOYMENT_STATE_FILE=".last_deployment"

# 배포 전 상태 저장
save_deployment_state() {
    local current_image=$(docker inspect --format='{{.Config.Image}}' myapp)
    echo "LAST_IMAGE=${current_image}" > ${DEPLOYMENT_STATE_FILE}
    echo "TIMESTAMP=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> ${DEPLOYMENT_STATE_FILE}
    echo "Deployment state saved: ${current_image}"
}

# 롤백 실행
rollback() {
    if [ ! -f "$DEPLOYMENT_STATE_FILE" ]; then
        echo "No deployment state found"
        return 1
    fi

    source ${DEPLOYMENT_STATE_FILE}

    echo "Rolling back to ${LAST_IMAGE}..."

    docker stop myapp
    docker rm myapp
    docker run -d --name myapp ${LAST_IMAGE}

    echo "Rollback completed"
}


# ============================================
# Blue-Green 배포 스크립트
# ============================================
blue_green_deploy() {
    local BLUE_PORT=8080
    local GREEN_PORT=8081
    local CURRENT=$(cat current_env.txt 2>/dev/null || echo "blue")

    if [ "$CURRENT" = "blue" ]; then
        local NEW="green"
        local NEW_PORT=$GREEN_PORT
        local OLD="blue"
        local OLD_PORT=$BLUE_PORT
    else
        local NEW="blue"
        local NEW_PORT=$BLUE_PORT
        local OLD="green"
        local OLD_PORT=$GREEN_PORT
    fi

    echo "Deploying to ${NEW} environment..."

    # 새 환경 시작
    docker run -d \
        --name myapp-${NEW} \
        -p ${NEW_PORT}:8080 \
        myapp:latest

    # 헬스체크
    sleep 10
    if curl -f http://localhost:${NEW_PORT}/health; then
        echo "${NEW} environment is healthy"

        # 로드밸런서 전환 (예: nginx reload)
        # nginx -s reload

        # 이전 환경 정리
        docker stop myapp-${OLD} 2>/dev/null || true
        docker rm myapp-${OLD} 2>/dev/null || true

        # 현재 환경 업데이트
        echo "${NEW}" > current_env.txt

        echo "Blue-Green deployment successful"
    else
        echo "Health check failed, rolling back"
        docker stop myapp-${NEW}
        docker rm myapp-${NEW}
        return 1
    fi
}


# ============================================
# 자동 태그 생성 스크립트
# ============================================
generate_tags() {
    # Git 정보 추출
    local GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    local GIT_SHA=$(git rev-parse --short HEAD)
    local GIT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
    local DATE_TAG=$(date +'%Y%m%d')

    # 브랜치별 태그 전략
    case $GIT_BRANCH in
        main|master)
            VERSION=$GIT_TAG
            ENV="prod"
            ;;
        dev|develop)
            VERSION="${DATE_TAG}-${GIT_SHA}"
            ENV="dev"
            ;;
        staging)
            VERSION="${GIT_TAG}-rc${DATE_TAG}"
            ENV="staging"
            ;;
        feature/*)
            local FEATURE_NAME=$(echo $GIT_BRANCH | sed 's/feature\///' | sed 's/\//-/g')
            VERSION="${FEATURE_NAME}-${GIT_SHA}"
            ENV="feature"
            ;;
        *)
            VERSION="${GIT_BRANCH}-${GIT_SHA}"
            ENV="test"
            ;;
    esac

    echo "IMAGE_VERSION=$VERSION"
    echo "IMAGE_ENV=$ENV"
    echo "IMAGE_TAG=${ENV}-${VERSION}"
}


# ============================================
# Docker Compose 배포
# ============================================
compose_deploy() {
    local VERSION="${1:-latest}"

    # 이미지 pull 및 컨테이너 재시작
    VERSION=${VERSION} docker-compose pull
    VERSION=${VERSION} docker-compose up -d

    # 무중단 배포 (웹 서비스만)
    # VERSION=${VERSION} docker-compose up -d --no-deps --build web
}


# ============================================
# 사용법
# ============================================
# source deploy_scripts.sh
# deploy 1.2.3                    # 버전 1.2.3 배포
# save_deployment_state           # 배포 전 상태 저장
# rollback                        # 롤백
# blue_green_deploy               # Blue-Green 배포
# generate_tags                   # 태그 생성
# compose_deploy 1.2.3            # Docker Compose 배포
