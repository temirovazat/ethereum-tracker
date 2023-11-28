import asyncio
import inspect
import json
import os

from dotenv import load_dotenv

from app.logs import logger
from app.services.bot_service import TelegramBot
from app.services.db_service import DatabaseService
from app.services.trading_service import tracking_loop
from app.services.user_service import UserService

env = os.environ.get
load_dotenv("../.env")

API_TOKEN = env("API_TOKEN")
ADMINS = json.loads(env("ADMINS"))

TRADING_PAIR = env("TRADING_PAIR")

DEBUG = env("DEBUG").lower() == "true"
POSTGRE_CON = (
    f"postgres://{env('POSTGRES_USER')}:{env('POSTGRES_PASSWORD')}"
    f"@{env('POSTGRES_HOST')}:{env('POSTGRES_PORT')}/{env('POSTGRES_DB')}"
)


async def main() -> None:
    """
    The main function to initialize and run the trading bot.

    It sets up the database, user service, and the Telegram bot. It then starts the event loop
    and initiates the trading loop in the background.

    :return: None
    """
    func_name = inspect.currentframe().f_code.co_name

    try:
        db_service = DatabaseService(DEBUG, POSTGRE_CON, ADMINS)

        await db_service.init_db()

        user_service = UserService()

        aio_bot = TelegramBot(API_TOKEN, user_service)

        aio_bot.dp._loop_create_task(tracking_loop(user_service, aio_bot, TRADING_PAIR))

        await aio_bot.dp.skip_updates()
        await aio_bot.dp.start_polling()

    except Exception as error:
        logger.error("%s/%s||%s", func_name, error.__class__, error.args[0])

    finally:
        await db_service.close_db()
        session = await aio_bot.bot.get_session()
        await session.close()
        logger.info("%s", func_name)


if __name__ == "__main__":
    asyncio.run(main())
