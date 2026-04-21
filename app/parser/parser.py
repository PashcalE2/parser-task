import logging
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from aiohttp import ClientSession

from app.common.utils import retry_middleware
from .types import IResultFilter, ParseResult


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


def parse_page(html: str) -> list[ParseResult]:
    logger.info("Parsing links from html")
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


async def find_documents_on_one_page(page: int = 1):
    response_text: str
    logger.info("Starting async http client")
    async with ClientSession(middlewares=[retry_middleware]) as session:
        async with session.get(
            url=REQUEST_URL,
            params=make_request_param(page),
        ) as response:
            logger.info("Request URL = %s", response.request_info.url)
            response_text = await response.text()

    return parse_page(response_text)


async def find_documents(
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
        try:
            parsed_data = await find_documents_on_one_page(page)
        except Exception as e:
            logger.warning(e)
        else:
            if len(parsed_data) == 0:
                # Потому что так устроен их сайт
                # Запрос со страницей, которая больше максимальной => 200-OK, нет ссылок на документы
                logger.info("No links found on this page - stop fetching")
                break

            parsed_data = filter.filter_all(parsed_data)
            result.extend(parsed_data)

    return result
