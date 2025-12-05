import logging
import os
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings as PydanticBaseSettings

from config.environements import EnvType
from domain.enitities.service import Service


class BaseSettings(PydanticBaseSettings):
    env: EnvType
    api_gateway_url: str = "http://localhost:8010"
    service_a_url: str = "http://service-a:8000"
    service_b_url: str = "http://service-b:8080"
    log_level: int = logging.DEBUG
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_algorithm: str = "HS256"
    allow_origins: list[str] = ["*"]
    additional_headers: dict[str, Any] = {
        "Strict-Transport-Security": "max-age=31536000",
        "X-Content-Type-Options": "nosniff",
    }
    base_path: Path = Path(__file__).parent.parent.resolve()

    # 특정 env 파일을 읽어야할 경우
    # model_config = SettingsConfigDict(env_file='dev.env', env_file_encoding='utf-8')

    def configure_logging(self) -> None:
        logging.basicConfig(level=self.log_level)

    @cached_property
    def service_mapping(self) -> dict[str, Service]:
        return {
            "service-a": Service(
                name="Service A", internal_url=self.service_a_url, slug="service-a"
            ),
            "service-b": Service(
                name="Service B", internal_url=self.service_b_url, slug="service-b"
            ),
        }


class TestSettings(BaseSettings):
    env: EnvType = EnvType.test
    jwt_secret_key: SecretStr = SecretStr("supersecret")

    @cached_property
    def service_mapping(self) -> dict[str, Service]:
        return {
            "test": Service(
                name="Test",
                internal_url="https://jsonplaceholder.typicode.com",
                slug="test",
            ),
            "not-exist": Service(
                name="Not exist", internal_url="https://not-exist", slug="not-exist"
            ),
        }


class LocalSettings(BaseSettings):
    pass


class DevSettings(BaseSettings):
    pass


class ProdSettings(BaseSettings):
    log_level: int = logging.INFO


settings_mapping = {
    EnvType.dev: DevSettings,
    EnvType.test: TestSettings,
    EnvType.prod: ProdSettings,
    EnvType.local: LocalSettings,
}


@lru_cache
def get_settings() -> BaseSettings:
    env_type = os.getenv("ENV_TYPE", "local")
    if env_type in ["local", "dev"]:
        load_dotenv()

    try:
        env = EnvType(env_type)
    except ValueError:
        valid_envs = [e.value for e in EnvType]
        raise ValueError(f"올바르지 않은 환경변수 ENV: {env_type}(valid_envs: {valid_envs})")
    return settings_mapping[env](env=env)
