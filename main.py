import logging
import timeit
import asyncio
from app.database import create_all_tables
from app.parser import find_docs, YearFilter
from app.logger_config import config
from app.parser.parser import ParseResult

config()
logger = logging.getLogger(__name__)


async def find_docs_task(start_page, end_page):
    result = await find_docs(YearFilter(), start_page=start_page, end_page=end_page)
    logger.info("Found %d", len(result))
    return result


async def async_tasks():
    tasks = [
        asyncio.create_task(find_docs_task(start_page=from_, end_page=to_))
        for from_, to_ in ((1, 2), (3, 5), (7, 10))
    ]

    results: list[list[ParseResult]] = await asyncio.gather(*tasks)
    logger.info(len(results))


async def run():
    await create_all_tables()
    # links = await find_docs(YearFilter(), start_page=1, end_page=2)
    # logger.info(len(links))

    await async_tasks()


def process_main():
    asyncio.run(run())


if __name__ == "__main__":
    execution_time = timeit.timeit(process_main, number=1)
    logger.info("Execution time: %f", execution_time)
