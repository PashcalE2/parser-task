from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol, Generator
from http import HTTPStatus
from bs4 import BeautifulSoup, Tag
from aiohttp import ClientRequest, ClientSession, ClientResponse, TCPConnector
import asyncio
import logging


logger = logging.getLogger(__name__)


def make_request_param(page: int) -> dict:
    return {"page": f"page-{page}"}


BASE_URL: str = "https://spimex.com"
REQUEST_URL: str = f"{BASE_URL}/markets/oil_products/trades/results/"
"""
?page=page-N

1 <= N <= 410 => 200-OK, даты, ссылки на файлы

N < 1 => то же самое, что при N = 1

N > 410 => 200-OK, нет файлов

N не число => 200-OK, N = 1
"""


class DocType(StrEnum):
    xls = "xls"
    pdf = "pdf"


@dataclass
class ParseResult:
    url: str
    filename: str
    date: "date"
    type: DocType


def parse_page(html: str) -> list[ParseResult]:
    parser = BeautifulSoup(html, features="html.parser")
    container: Tag = parser.find(class_="accordeon-inner")
    if not container:
        return []

    result = []
    for div in container.find_all(class_="accordeon-inner__item"):
        url = str(div.find("a").get("href"))
        if not url.startswith("https"):
            if not url.startswith("/files"):
                continue
            url = f"{BASE_URL}{url}"

        no_params_link = url.split("?")[0]
        filename = no_params_link[no_params_link.rfind("/") + 1 :]
        type_ = filename[filename.rfind(".") + 1 :]
        date_ = datetime.strptime(div.find("span").text, "%d.%m.%Y")
        result.append(ParseResult(url=url, filename=filename, date=date_, type=type_))

    return result


class IResultFilter(Protocol):
    def filter_all(self, objs: list[ParseResult]) -> Generator[ParseResult]: ...


class YearFilter(IResultFilter):
    def filter_all(self, objs: list[ParseResult]) -> Generator[ParseResult]:
        return (obj for obj in objs if obj.date.year >= 2023)


async def _retry_middleware(
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


async def find_docs(
    filter: IResultFilter,
    start_page: int = 1,
    end_page: int = 0,
) -> list[ParseResult]:
    if end_page < start_page:
        logger.info("Fetching site from page %d", start_page)
    else:
        logger.info("Fetching site from page %d to %d", start_page, end_page)

    result: list[ParseResult] = []

    for page in range(start_page, end_page, 1):
        response_text: str

        logger.info("Starting async http client")
        async with ClientSession(middlewares=[_retry_middleware]) as session:
            async with session.get(
                url=REQUEST_URL,
                params=make_request_param(page),
            ) as response:
                response_text = await response.text()

        logger.info("Parsing links from html")
        parsed_data = parse_page(response_text)

        if len(parsed_data) == 0:
            # Потому что так устроен их сайт
            # Запрос со страницей, которая больше максимальной => 200-OK, нет ссылок на документы
            logger.info("No links found on this page - stop fetching")
            break

        parsed_data = filter.filter_all(parsed_data)
        result.extend(parsed_data)

    return result
