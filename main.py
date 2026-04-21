import logging
import math
import timeit
import asyncio
import aiofiles.os
from asyncio import TaskGroup
from multiprocessing import Pool
from typing import Generator, Iterable
from itertools import batched
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from app.common.error import DateAlreadyPresentError
from app.database import create_all_tables, SpimexTradingResults, DBAsyncSession
from app.datasheets import read_document, IDataSaver
from app.parser import (
    find_documents,
    IResultFilter,
    ParseResult,
    download_documents,
    ensure_download_directory,
    DownloadedDocumentInfo,
)
from app.common.logger_config import config


config()
logger = logging.getLogger(__name__)


async def read_document_and_save(
    document_info: DownloadedDocumentInfo,
    data_saver: IDataSaver,
) -> None:
    try:
        trading_results = await read_document(document_info)
        await aiofiles.os.remove(document_info.filepath)
        await data_saver.save_all(trading_results)
    except Exception as e:
        logger.warning(str(e))


async def read_documents_and_save(
    documents_info: Iterable[DownloadedDocumentInfo],
    data_saver: IDataSaver,
) -> None:
    async with TaskGroup() as group:
        _ = [
            group.create_task(read_document_and_save(info, data_saver))
            for info in documents_info
        ]


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
        try:
            async with DBAsyncSession() as session:
                await session.execute(insert(SpimexTradingResults), dict_objs)
                await session.commit()
        except IntegrityError:
            raise DateAlreadyPresentError(objs[0].date)
        logger.info("Finish saving %d rows to DB", len_)


def sync_download_task(info_list: list[ParseResult]) -> list[DownloadedDocumentInfo]:
    logger.info("Start files downloading")
    result = asyncio.run(download_documents(info_list))
    logger.info("Finish files downloading")
    return result


def sync_read_documents_and_save(documents_data: list[DownloadedDocumentInfo]):
    logger.info("Start read and save documents")
    asyncio.run(read_documents_and_save(documents_data, DBSaver))
    logger.info("Finish read and save documents")


def multiprocessing_main(
    workers: int = 5,
    start_page: int = 2,
    end_page: int = 3,
):
    # Получение всех ссылок
    reports_info: list[ParseResult] = asyncio.run(
        find_documents(
            filter=YearFilter,
            start_page=start_page,
            end_page=end_page,
        )
    )

    n_reports_info = len(reports_info)
    logger.info("Reports total count: %d", n_reports_info)

    if n_reports_info == 0:
        logger.info("Not found files for downloading, exiting")
        return

    batch_size = int(math.ceil(n_reports_info / workers))
    logger.info("Batch size: %d", batch_size)

    # Скачивание всех файлов
    ensure_download_directory()

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
