import logging
import math
import timeit
import asyncio
from multiprocessing import Pool
from typing import Generator
from itertools import batched
from sqlalchemy import insert
from app.database import create_all_tables, SpimexTradingResults, DBAsyncSession
from app.datasheets import read_documents_and_save, IDataSaver
from app.parser import (
    find_documents,
    IResultFilter,
    ParseResult,
    download_documents,
    DownloadedDocumentInfo,
)
from app.logger_config import config


config()
logger = logging.getLogger(__name__)


class YearFilter(IResultFilter):
    @staticmethod
    def filter_all(objs: list[ParseResult]) -> Generator[ParseResult]:
        return (obj for obj in objs if obj.date.year >= 2023)


class DBSaver(IDataSaver):
    @staticmethod
    async def save_all(objs: list[SpimexTradingResults]) -> None:
        len_ = len(objs)
        logger.info("Start saving %d rows to DB", len_)
        dict_objs = (obj.to_dict() for obj in objs)
        async with DBAsyncSession() as session:
            await session.execute(insert(SpimexTradingResults), dict_objs)
            await session.commit()
        logger.info("Finish saving %d rows to DB", len_)


def sync_download_task(info_list) -> list[DownloadedDocumentInfo]:
    logger.info("Start files download")
    result = asyncio.run(download_documents(info_list))
    logger.info("Finish files download")
    return result


def sync_read_documents_and_save(documents_data):
    logger.info("Start read and save documents")
    asyncio.run(read_documents_and_save(documents_data, DBSaver))
    logger.info("Finish read and save documents")


def multiprocessing_main(
    workers: int = 5,
    start_page: int = 1,
    end_page: int = 2,
):
    # Получение всех ссылок
    reports_info: list[ParseResult] = asyncio.run(
        find_documents(
            filter=YearFilter,
            start_page=start_page,
            end_page=end_page,
        )
    )

    logger.info("Reports total count: %d", len(reports_info))

    batch_size = int(math.ceil(len(reports_info) / workers))
    logger.info("Batch size: %d", batch_size)

    # Скачивание всех файлов
    download_results: list[DownloadedDocumentInfo] = []

    with Pool(workers) as pool:
        results = pool.map(
            func=sync_download_task,
            iterable=batched(reports_info, batch_size),
        )
        for result in results:
            download_results.extend(result)

    logger.info("Downloaded reports count: %d", len(download_results))

    # Создание таблиц в БД если их нет
    asyncio.run(create_all_tables())

    # Считывание, обработка и отправка данных из файлов
    with Pool(workers) as pool:
        pool.map(
            func=sync_read_documents_and_save,
            iterable=batched(download_results, batch_size),
        )


def main():
    multiprocessing_main()


if __name__ == "__main__":
    execution_time = timeit.timeit(main, number=1)
    logger.info("Execution time: %f", execution_time)
