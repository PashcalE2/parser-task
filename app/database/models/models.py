from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy.types import Date
from sqlalchemy import func

Base = declarative_base()


class CreatedUpdated(Base):
    __abstract__ = True

    created_on: Mapped["date"] = mapped_column(Date(), default=func.now())
    updated_on: Mapped["date"] = mapped_column(
        Date(), onupdate=func.now(), nullable=True
    )


class SpimexTradingResults(CreatedUpdated):
    """
    Из таблицы "Единица измерения: Метрическая тонна", где количество Договоров, шт. > 0

    Код Инструмента (exchange_product_id)

    Наименование Инструмента (exchange_product_name)

    Базис поставки (delivery_basis_name)

    Объем Договоров в единицах измерения (volume)

    Объем Договоров, руб. (total)

    Количество Договоров, шт. (count)

    Дата торгов (date)
    """

    __tablename__ = "spimex_trading_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange_product_id: Mapped[str]
    exchange_product_name: Mapped[str]
    oil_id: Mapped[str]  # exchange_product_id[:4]
    delivery_basis_id: Mapped[str]  # exchange_product_id[4:7]
    delivery_basis_name: Mapped[str]
    delivery_type_id: Mapped[str]  # exchange_product_id[-1]
    volume: Mapped[int]
    total: Mapped[int]
    count: Mapped[int]
    date: Mapped["date"] = mapped_column(Date())  # Дата торгов

    def __init__(
        self,
        exchange_product_id: int,
        exchange_product_name: str,
        delivery_basis_name: str,
        volume: int,
        total: int,
        count: int,
        date: "date",
        **kwargs,
    ):
        # Call the superclass __init__ to handle mapped columns
        super().__init__(
            exchange_product_id=exchange_product_id,
            exchange_product_name=exchange_product_name,
            oil_id=exchange_product_id[:4],
            delivery_basis_id=exchange_product_id[4:7],
            delivery_basis_name=delivery_basis_name,
            delivery_type_id=exchange_product_id[-1],
            volume=volume,
            total=total,
            count=count,
            date=date,
            **kwargs,
        )

    def __repr__(self) -> str:
        return f"SpimexTradingResults(id={self.id!r}, exchange_product_id={self.exchange_product_id!r}, exchange_product_name={self.exchange_product_name!r}, oil_id={self.oil_id!r}, delivery_basis_id={self.delivery_basis_id!r}, delivery_basis_name={self.delivery_basis_name!r}, delivery_type_id={self.delivery_type_id!r}, volume={self.volume!r}, total={self.total!r}, count={self.count!r}, date={self.date!r}, created_on={self.created_on!r}, updated_on={self.updated_on!r})"

    def to_dict(self) -> dict:
        return {
            "exchange_product_id": self.exchange_product_id,
            "date": self.date,
            "exchange_product_name": self.exchange_product_name,
            "oil_id": self.oil_id,
            "delivery_basis_id": self.delivery_basis_id,
            "delivery_basis_name": self.delivery_basis_name,
            "delivery_type_id": self.delivery_type_id,
            "volume": int(self.volume),
            "total": int(self.total),
            "count": int(self.count),
        }
