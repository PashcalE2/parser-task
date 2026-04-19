import logging
import timeit
from app.parser import find_docs, SomeFilter


logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s"
)
logger = logging.getLogger(__name__)


def find_docs_task(start_page, end_page):
    result = find_docs(SomeFilter(), start_page=start_page, end_page=end_page)
    logger.info("Found %d", len(result))
    return result


def tasks():
    results = [
        find_docs_task(start_page=from_, end_page=to_)
        for from_, to_ in ((1, 2), (3, 5), (7, 10))
    ]

    logger.info(len(results))


def run():
    # links = await find_docs(YearFilter(), start_page=1, end_page=2)
    # logger.info(len(links))

    tasks()


def process_main():
    run()


if __name__ == "__main__":
    execution_time = timeit.timeit(process_main, number=1)
    logger.info("Execution time: %f", execution_time)
