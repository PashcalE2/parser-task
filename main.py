import logging
import timeit
from sqlalchemy import insert
from app.parser import find_docs, SomeFilter
from app.database import DBSession
from app.database.models import SpimexTradingResults
from app.datasheets import IDataSaver, read_docs_and_save


logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s"
)
logger = logging.getLogger(__name__)


class DBSaver(IDataSaver):
    def save_all(self, objs: list[SpimexTradingResults]):
        dict_objs = (obj.to_dict() for obj in objs)
        with DBSession() as session:
            session.execute(insert(SpimexTradingResults), dict_objs)
            session.commit()


def main(start_page: int = 5, end_page: int = 6):
    docs = find_docs(SomeFilter(), start_page, end_page)
    read_docs_and_save(docs, DBSaver())


if __name__ == "__main__":
    execution_time = timeit.timeit(main, number=1)
    logger.info("Execution time: %f", execution_time)
