import inspect
import logging
import os

from dotenv import load_dotenv

env = os.environ.get
load_dotenv("./.env")

LOG_LEVEL = env("LOG_LEVEL").upper()

logger = logging.getLogger("eth_tracker")

logger.setLevel(level=LOG_LEVEL if LOG_LEVEL in ["DEBUG", "ERROR", "INFO", "WARNING"] else "INFO")
file_handler = logging.FileHandler("eth_tracker.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s", datefmt="%d/%m/%Y %H:%M:%S"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def log(logger):
    def decorator_log(func):
        is_async = inspect.iscoroutinefunction(func)
        func_name = func.__name__

        if is_async:

            async def wrapper(*args, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                    return result

                except Exception as error:
                    logger.error("%s/%s||%s", func_name, error.__class__, error.args[0])
                    return -1

                finally:
                    logger.info("%s", func_name)

            return wrapper

        else:

            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    return result

                except Exception as error:
                    logger.error("%s/%s||%s", func_name, error.__class__, error.args[0])
                    return -1

                finally:
                    logger.info("%s", func_name)

            return wrapper

    return decorator_log
