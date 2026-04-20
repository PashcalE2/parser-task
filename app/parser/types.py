from datetime import date
from enum import StrEnum
from dataclasses import dataclass
from typing import Protocol, Generator


class DocType(StrEnum):
    xls = "xls"
    pdf = "pdf"


@dataclass
class ParseResult:
    url: str
    filename: str
    date: "date"
    type: DocType


class IResultFilter(Protocol):
    @staticmethod
    def filter_all(objs: list[ParseResult]) -> Generator[ParseResult]: ...


@dataclass
class DownloadedDocumentInfo:
    filepath: str
    date: "date"
    type: DocType
