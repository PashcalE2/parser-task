import datetime
import pytest
from sqlalchemy.orm.session import Session
from app.database import DBSession, create_all
from app.database.models import SpimexTradingResults


create_all()


trading_results_example = SpimexTradingResults(
    exchange_product_id="A100NVY060F",
    exchange_product_name="Бензин (АИ-100-К5), ст. Новоярославская (ст. отправления)",
    delivery_basis_name="ст. Новоярославская",
    volume="60",
    total="5487300",
    count=1,
    date=datetime.date(2026, 3, 31),
)


class Tests:
    @pytest.fixture
    def session(self) -> Session:
        return DBSession()

    def test_insert(self, session: Session):
        with session:
            session.add(trading_results_example)
            session.flush()

            assert trading_results_example.id is not None

            session.rollback()
