# ============================================
# Dockerfile 기본 템플릿
# Python 애플리케이션용 기본 구조
# ============================================

# 베이스 이미지 선택
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 (캐시 최적화를 위해 먼저 복사)
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경변수 설정
ENV PYTHONUNBUFFERED=1

# 노출할 포트 선언
EXPOSE 8000

# 컨테이너 시작 시 실행할 명령
CMD ["python", "app.py"]


# ============================================
# Dockerfile 주요 명령어 참조
# ============================================
#
# FROM       - 베이스 이미지 지정
#              예: FROM python:3.12-slim
#
# WORKDIR    - 작업 디렉토리 설정
#              예: WORKDIR /app
#
# COPY       - 파일/디렉토리 복사
#              예: COPY . /app
#
# ADD        - 파일 복사 + URL/압축 해제 지원
#              예: ADD archive.tar.gz /app
#
# RUN        - 이미지 빌드 시 명령 실행
#              예: RUN apt-get update
#
# CMD        - 컨테이너 시작 시 기본 명령
#              예: CMD ["python", "app.py"]
#
# ENTRYPOINT - 컨테이너 진입점 설정
#              예: ENTRYPOINT ["python"]
#
# ENV        - 환경변수 설정
#              예: ENV DEBUG=false
#
# ARG        - 빌드 시점 변수
#              예: ARG VERSION=1.0
#
# EXPOSE     - 포트 노출 선언
#              예: EXPOSE 8000
#
# VOLUME     - 볼륨 마운트 포인트
#              예: VOLUME /data
#
# USER       - 실행 사용자 지정
#              예: USER appuser
#
# LABEL      - 메타데이터 추가
#              예: LABEL version="1.0"


# ============================================
# 레이어 최적화 예제
# ============================================

# [나쁜 예] 레이어가 많고 캐싱 비효율적
# COPY file1.txt .
# COPY file2.txt .
# RUN apt-get update
# RUN apt-get install -y package1
# RUN apt-get install -y package2

# [좋은 예] 레이어 최소화 및 캐싱 최적화
# COPY file1.txt file2.txt ./
# RUN apt-get update && \
#     apt-get install -y package1 package2 && \
#     rm -rf /var/lib/apt/lists/*
