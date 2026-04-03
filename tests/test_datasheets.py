import os
import pytest
from datetime import date
from app.database import create_all
from app.database.models import SpimexTradingResults
from app.datasheets import download_doc, read_doc, read_docs_and_save, IDataSaver
from app.parser import find_docs, SomeFilter, ParseResult, DocType
from app.database import DBSession


create_all()


parse_result_pdf_example = ParseResult(
    url="https://spimex.com/files/trades/result/pdf/oil/oil_20260327162000.pdf?r=5503",
    filename="oil_20260327162000.pdf",
    date=date.today(),
    type=DocType.pdf,
)

parse_result_xls_example = ParseResult(
    url="https://spimex.com/files/trades/result/oil_xls/oil_xls_20251125162000.xls?r=2763&p=L3VwbG9hZC9yZXBvcnRzL3BkZi9vaWwvb2lsXzIwMjUxMTI1MTYyMDAwLnBkZg..",
    filename="oil_xls_20251125162000.xls",
    date=date.today(),
    type=DocType.xls,
)


class Tests:
    @pytest.fixture
    def commit(self):
        return True

    def test_download(self):
        docs_data = find_docs(SomeFilter(), start_page=10, end_page=11)
        fpath: str = download_doc(docs_data[0])
        print(fpath)
        assert os.path.exists(fpath)

    def test_read_pdf(self):
        data = read_doc(parse_result_pdf_example)
        assert len(data) > 0

    def test_read_and_save_xls(self):
        data = read_doc(parse_result_xls_example)[:10]
        with DBSession() as session:
            session.add_all(data)
            session.flush()

            print(data[0])
            assert data[0].id is not None
            session.rollback()

    def test_read_and_save_many(self, commit):
        class SomeSaver(IDataSaver):
            def save_all(self, objs: list[SpimexTradingResults]):
                with DBSession() as session:
                    session.add_all(objs)
                    session.flush()

                    session.query(SpimexTradingResults).update(
                        {SpimexTradingResults.count: SpimexTradingResults.count}
                    )
                    session.flush()

                    updated = (
                        session.query(SpimexTradingResults)
                        .filter(SpimexTradingResults.updated_on is not None)
                        .all()
                    )
                    print(updated[0])
                    assert updated[0].updated_on is not None

                    if commit:
                        session.commit()

        read_docs_and_save([parse_result_xls_example], SomeSaver())


"""
SpimexTradingResults(
    id=1,
    exchange_product_id="A100NVY060F",
    exchange_product_name="Бензин (АИ-100-К5), ст. Новоярославская (ст. отправления)",
    oil_id="A100",
    delivery_basis_id="NVY",
    delivery_basis_name="ст. Новоярославская",
    delivery_type_id="F",
    volume="60",
    total="5487300",
    count=1,
    date=datetime.date(2026, 3, 31),
    created_on=datetime.date(2026, 3, 30),
    updated_on=None,
)
"""
