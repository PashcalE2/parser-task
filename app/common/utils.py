import asyncio
import logging
from aiohttp import ClientRequest, ClientResponse
from http import HTTPStatus

logger = logging.getLogger(__name__)


async def retry_middleware(
    request: ClientRequest,
    handler,
) -> ClientResponse:
    for i in range(3):
        try:
            response: ClientResponse = await handler(request)
            if response.status == HTTPStatus.OK:
                return response
            logger.warning("%s. Retry attempt #%d", f"{response.status=}", i + 1)
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            raise
    raise Exception()
