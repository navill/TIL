import os

import django
from daphne.cli import CommandLineInterface
from dotenv import load_dotenv

# Django 설정 로드
stage = os.getenv("STAGE", "dev")  # dev or prod
load_dotenv(f".envs/{stage}.env")
print(f"load stage: {stage}")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Daphne 서버 실행 (디버깅 모드)
CommandLineInterface.entrypoint()
