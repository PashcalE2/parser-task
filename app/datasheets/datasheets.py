import asyncio
from typing import Protocol
from pandas import DataFrame
from datetime import date
import pandas as pd
import camelot
from app.parser import DocType, DownloadedDocumentInfo
from app.database.models import SpimexTradingResults
import logging


logger = logging.getLogger(__name__)


class IDataSaver(Protocol):
    @staticmethod
    async def save_all(objs: list[SpimexTradingResults]) -> None: ...


target_columns_dict = {
    "product_id": "Код\nИнструмента",
    "product_name": "Наименование\nИнструмента",
    "basis_name": "Базис\nпоставки",
    "volume": "Объем\nДоговоров\nв единицах\nизмерения",
    "total": "Обьем\nДоговоров,\nруб.",
    "count": "Количество\nДоговоров,\nшт.",
}
target_columns = [
    target_columns_dict["product_id"],
    target_columns_dict["product_name"],
    target_columns_dict["basis_name"],
    target_columns_dict["volume"],
    target_columns_dict["total"],
    target_columns_dict["count"],
]


class IDocumentReader(Protocol):
    @staticmethod
    def check_compatible(date_: date) -> bool: ...

    @staticmethod
    async def read(filepath: str) -> DataFrame: ...


class XLSReader(IDocumentReader):
    @staticmethod
    def check_compatible(date_: date) -> bool:
        return True

    @staticmethod
    async def read(filepath: str) -> DataFrame:
        def read_excel() -> DataFrame:
            return pd.read_excel(filepath, dtype=str)

        loop = asyncio.get_running_loop()
        df: DataFrame = await loop.run_in_executor(None, read_excel)
        df = df.dropna(axis=1, how="all")

        # Поиск нужной таблицы
        target_table_start = df.loc[
            df[df.columns[0]] == "Единица измерения: Метрическая тонна"
        ].index.start

        # Удаление лишних строк, добавление названий столбцов
        df = df.iloc[target_table_start + 1 :]
        df = DataFrame(df.values[2:], columns=df.iloc[0].values)
        df = df[target_columns]

        target_table_end = df.loc[df[df.columns[0]] == "Итого:"].index.start
        df = df.iloc[:target_table_end]

        return df


class PDFReader(IDocumentReader):
    @staticmethod
    def check_compatible(date_: date) -> bool:
        return True

    @staticmethod
    async def read(filepath: str) -> DataFrame:
        logger.info("Reading PDF using camelot")

        def read_pdf():
            return camelot.read_pdf(filepath, pages="all")

        # loop = asyncio.get_running_loop()
        # data = await loop.run_in_executor(None, read_pdf)
        data = read_pdf()

        logger.info("Looking for table")
        # В таких файлах первые несколько таблиц не те что надо
        wanted_table_start = 0
        while data._tables[wanted_table_start].page == 1:
            wanted_table_start += 1
        wanted_table_start -= 1

        logger.info("Found wanted table: %d", wanted_table_start)

        df: DataFrame = pd.concat(
            (table.df for table in data._tables[wanted_table_start:]),
            ignore_index=True,
        )
        df = DataFrame(df.values[2:], columns=df.iloc[0].values)
        df = df[target_columns]

        logger.info("Converted to DataFrame")

        return df


document_readers: dict[DocType, list[IDocumentReader]] = {
    DocType.xls: [XLSReader],
    DocType.pdf: [PDFReader],
}


def choose_reader(info: DownloadedDocumentInfo) -> IDocumentReader:
    for reader in document_readers[info.type]:
        if reader.check_compatible(info.date):
            return reader
    raise


async def read_document(info: DownloadedDocumentInfo) -> list[SpimexTradingResults]:
    logger.info("Reading document: %s", info.filepath)
    reader = choose_reader(info)
    df: DataFrame = await reader.read(info.filepath)

    count_column_name = target_columns_dict["count"]
    df[count_column_name] = df[count_column_name].replace("-", "0").astype(int)
    df = df.loc[df[count_column_name] > 0]

    result = [
        SpimexTradingResults(
            exchange_product_id=line[0],
            exchange_product_name=line[1],
            delivery_basis_name=line[2],
            volume=line[3],
            total=line[4],
            count=line[5],
            date=info.date,
        )
        for line in df.values
    ]
    return result
