from typing import Protocol
import requests
from requests import Response
import pandas as pd
from pandas import DataFrame
import camelot
from app.parser import DocType
from app.database.models import SpimexTradingResults
from app.parser import ParseResult


class IDataSaver(Protocol):
    def save_all(self, objs: list[SpimexTradingResults]) -> None: ...


storage_dir: str = ".reports"


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


def download_doc(doc_data: ParseResult):
    response: Response = requests.get(doc_data.url)
    filepath = f"./{storage_dir}/{doc_data.filename}"
    with open(filepath, "wb") as file:
        file.write(response.content)
    return filepath


def read_xls(filepath: str):
    df: DataFrame = pd.read_excel(filepath, dtype=str)
    df = df.dropna(axis=1, how="all")

    target_table_start = df.loc[
        df[df.columns[0]] == "Единица измерения: Метрическая тонна"
    ].index.start

    df = df.iloc[target_table_start + 1 :]
    df = DataFrame(df.values[2:], columns=df.iloc[0].values)
    df = df[target_columns]

    target_table_end = df.loc[df[df.columns[0]] == "Итого:"].index.start
    df = df.iloc[:target_table_end]

    return df


def read_pdf(filepath: str):
    data = camelot.read_pdf(filepath, pages="all")

    # В таких файлах первые две таблицы не те что надо
    df: DataFrame = pd.concat(
        (table.df for table in data._tables[2:]), ignore_index=True
    )

    df = DataFrame(df.values[2:], columns=df.iloc[0].values)

    return df


def read_doc(doc_data: ParseResult):
    filepath = download_doc(doc_data)

    result: list[SpimexTradingResults]
    df: DataFrame
    if filepath.endswith(DocType.xls):
        df = read_xls(filepath)
    elif filepath.endswith(DocType.pdf):
        df = read_pdf(filepath)

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
            date=doc_data.date,
        )
        for line in df.values
    ]
    return result


def read_docs_and_save(docs_data: list[ParseResult], data_saver: IDataSaver):
    for data in docs_data:
        data_saver.save_all(read_doc(data))
