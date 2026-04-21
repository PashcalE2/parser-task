import logging


def config():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(processName)s] [%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s",
        handlers=[logging.StreamHandler()],
    )
