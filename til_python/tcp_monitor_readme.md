## backend TCP 외부 연결 monitoring
- TCP 연결 상태 확인을 위한 python script(local)

```python
# 자동 감지 모드 (모든 백엔드 서비스 탐색)
%(prog)s

# 특정 서비스 타입 모니터링
%(prog)s -s daphne
%(prog)s -s gunicorn
%(prog)s -s uvicorn

# 포트 기반 필터링
%(prog)s -s daphne -p 8000

# 사용자 정의 프로세스명
%(prog)s -n "python manage.py"

# 갱신 주기 설정 (기본 2초)
%(prog)s -s gunicorn -i 5

# 색상 없이 출력
%(prog)s --no-color

지원 서비스:
- Daphne (Django Channels ASGI)
- Gunicorn (Django WSGI)
- Uvicorn (FastAPI ASGI)
- Django runserver (개발 서버)
- FastAPI dev server
- Hypercorn

```