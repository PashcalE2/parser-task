import os
from asyncio import TaskGroup, Task
import aiofiles
import aiohttp
from typing import Iterable
from .types import ParseResult, DownloadedDocumentInfo


STORAGE_DIR: str = ".reports"


async def download_document(info: ParseResult) -> DownloadedDocumentInfo:
    async with aiohttp.ClientSession() as session:
        async with session.get(url=info.url) as response:
            response: aiohttp.ClientResponse
            filepath = f"./{STORAGE_DIR}/{info.filename}"
            async with aiofiles.open(filepath, "wb") as file:
                async for chunk in response.content.iter_chunked(1024):
                    await file.write(chunk)
    return DownloadedDocumentInfo(filepath=filepath, date=info.date, type=info.type)


async def download_documents(
    info_list: Iterable[ParseResult],
) -> list[DownloadedDocumentInfo]:
    async with TaskGroup() as group:
        tasks: list[Task] = [
            group.create_task(download_document(info)) for info in info_list
        ]

    results: list[DownloadedDocumentInfo] = []
    for task in tasks:
        results.append(task.result())

    return results


def ensure_download_directory():
    try:
        os.mkdir(f"./{STORAGE_DIR}")
    except FileExistsError as e:
        pass
