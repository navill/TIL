import logging
from http import HTTPMethod, HTTPStatus
from typing import Any

import aiohttp

from adapters.exceptions import GatewayRouterException, NotFoundException
from config.settings import BaseSettings
from ports.gateway_router import GatewayRouter

logger = logging.getLogger()


class AiohttpGatewayRouter(GatewayRouter):
    def __init__(self, session: aiohttp.ClientSession, settings: BaseSettings):
        self._session = session
        self._settings = settings

    async def __call__(
            self,
            service_name: str,
            route: str,
            headers: dict[str, Any],
            method: str = HTTPMethod.GET,
            body: bytes | None = None,
    ) -> tuple[bytes, int]:
        service = self._settings.service_mapping.get(service_name)
        if service is None:
            raise NotFoundException
        try:
            # ClientSession(connection pool)을 재사용하기 때문에 context manager를 이용한 session.close구문은 필요 X
            # 단, fastapi 앱 종료 시점에 session.close() 호출 필요함 -> lifespan에서 처리
            # _RequestContextManager.__aexit__ 내에서 _resp.release()로 connection release
            async with self._session.request(
                    method=method,
                    url=service.internal_url
                        + (route[:-1] if route.endswith("/") else route),
                    headers=self._get_headers(headers),
                    data=body,
            ) as response:
                response_body = b""
                if response.status != HTTPStatus.NO_CONTENT:
                    response_body = await response.content.read()
            return response_body, response.status
        except Exception as e:
            logger.exception(f"{service.name}: {e}")
            raise GatewayRouterException from e

    @staticmethod
    def _get_headers(headers: dict[str, Any]) -> dict[str, Any]:
        # here you can control or inject additional headers
        return headers


class AiohttpSessionEngine:
    def __init__(self) -> None:
        self.session: None | aiohttp.ClientSession = None

    async def __call__(self) -> aiohttp.ClientSession:
        # session을 싱글톤으로 사용
        if self.session is None:
            connector = aiohttp.TCPConnector(limit_per_host=100)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self.session

    async def close(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None


get_session = AiohttpSessionEngine()
