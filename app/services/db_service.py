from tortoise import Tortoise

from app.logs import log, logger
from app.services.user_service import UserService


class DatabaseService:
    """
    DatabaseService class for handling database initialization and closure.

    Attributes:
    - debug (bool): A flag indicating whether the application is in debug mode.
    - postgre_con (str): Connection string for PostgreSQL database.
    - admins (list): List of admin user IDs.

    Methods:
    - __init__: Initializes the DatabaseService with configuration parameters.
    - init_db: Initializes the database connection and generates schemas.
    - close_db: Closes the database connections.
    """

    def __init__(
        self,
        debug: bool = True,
        postgre_con: str = "postgres://postgres:pass@db.host:5432/somedb",
        admins: list = None,
    ) -> None:
        """
        Initializes the DatabaseService instance.

        Args:
        - debug (bool): A flag indicating whether the application is in debug mode.
        - postgre_con (str): Connection string for Postgres database.
        - admins (list): List of admin user IDs.
        """
        self.db_url = "sqlite://db.sqlite3" if debug else postgre_con
        self.admins = admins

    @log(logger)
    async def init_db(self) -> None:
        """
        Initializes the database connection and generates schemas.
        If admins are provided, adds them as admin users in the database.
        """
        await Tortoise.init(
            db_url=self.db_url, modules={"models": ["app.models.models"]}, timezone="Europe/Moscow"
        )
        await Tortoise.generate_schemas()

        if self.admins:
            for admin_id in self.admins:
                await UserService.add_user(tg_id=admin_id, is_admin=True)

    @classmethod
    @log(logger)
    async def close_db(cls) -> None:
        """
        Closes the database connections.
        """
        await Tortoise.close_connections()
