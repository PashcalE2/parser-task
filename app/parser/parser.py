from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol
from http import HTTPStatus
import requests
from requests import Response
from bs4 import BeautifulSoup, Tag


def make_request_param(page: int) -> dict:
    return {"page": f"page-{page}"}


base_url: str = "https://spimex.com"
base_request_url: str = f"{base_url}/markets/oil_products/trades/results/"
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
            url = f"{base_url}{url}"

        no_params_link = url.split("?")[0]
        filename = no_params_link[no_params_link.rfind("/") + 1 :]

        type_ = filename[filename.rfind(".") + 1 :]

        date_ = datetime.strptime(div.find("span").text, "%d.%m.%Y")

        result.append(ParseResult(url=url, filename=filename, date=date_, type=type_))

    return result


class IResultFilter(Protocol):
    def filter_all(self, objs: list[ParseResult]) -> list[ParseResult]: ...


class SomeFilter(IResultFilter):
    def filter_all(self, objs: list[ParseResult]) -> list[ParseResult]:
        return [obj for obj in objs if obj.date.year >= 2023]


def find_docs(
    filter: IResultFilter, start_page: int = 1, end_page: int = 0
) -> list[ParseResult]:
    result: list[ParseResult] = []

    for page in range(start_page, end_page, 1):
        response: Response = requests.get(
            base_request_url, params=make_request_param(page)
        )

        if response.status_code != HTTPStatus.OK:
            continue

        parsed_data = parse_page(response.text)

        if len(parsed_data) == 0:
            # Потому что так устроен их сайт
            # Запрос со страницей, которая больше максимальной => 200-OK, нет ссылок на документы
            break

        parsed_data = filter.filter_all(parsed_data)
        result.extend(parsed_data)

    return result
