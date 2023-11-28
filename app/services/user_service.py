from app.logs import log, logger
from app.models.models import User


class UserService:
    """
    Service class for managing user-related operations.
    """

    def __init__(self) -> None:
        """
        Initialize the UserService.
        """
        ...

    @classmethod
    @log(logger)
    async def get_user(cls, tg_id: int) -> dict or int:
        """
        Retrieve user information based on Telegram user ID.

        Args:
            tg_id (int): Telegram user ID.

        Returns:
            dict or int: User information or 0 if the user doesn't exist.
        """
        user_obj = await User.filter(id=tg_id).first().values()
        return user_obj

    @classmethod
    @log(logger)
    async def add_user(cls, tg_id: int, username: str = None, is_admin: bool = False):
        """
        Add a new user or update the existing user's information.

        Args:
            tg_id (int): Telegram user ID.
            username (str): Telegram username.
            is_admin (bool): Whether the user is an admin.

        Returns:
            int: 0 if a new user is added, 1 if the existing user is updated.
        """
        user_obj = await User.filter(id=tg_id).first()

        if not user_obj:
            await User.create(id=tg_id, username=username, is_admin=is_admin)
            return 0
        else:
            user_obj.username = username
            await user_obj.save()
            return 1

    @classmethod
    @log(logger)
    async def update_notification(cls, tg_id: int):
        """
        Toggle user notification status.

        Args:
            tg_id (int): Telegram user ID.

        Returns:
            int: Updated notification status.
        """
        user_obj = await User.filter(id=tg_id).first()

        if user_obj:
            user_obj.notification = 0 if user_obj.notification else 1
            await user_obj.save()
            return user_obj.notification

    @classmethod
    @log(logger)
    async def update_percent(cls, tg_id: int, percent: float):
        """
        Update the user's alert percentage.

        Args:
            tg_id (int): Telegram user ID.
            percent (float): New alert percentage.

        Returns:
            int: 0 if the update is successful.
        """
        user_obj = await User.filter(id=tg_id).first()

        if user_obj:
            user_obj.percent = percent
            await user_obj.save()
            return 0

    @classmethod
    @property
    @log(logger)
    async def get_admins(cls):
        """
        Retrieve a list of admin users.

        Returns:
            list: List of admin users.
        """
        admin_objs = await User.filter(is_admin=True).values("id")

        if admin_objs:
            return admin_objs

    @classmethod
    @property
    @log(logger)
    async def get_ready_users(cls):
        """
        Retrieve a list of users with notifications enabled.

        Returns:
            list: List of users with notifications enabled.
        """
        user_objs = await User.filter(notification=True).values("id", "percent")

        if user_objs:
            return user_objs

    @classmethod
    @log(logger)
    async def update_admin(cls, tg_id: int, status: int):
        """
        Update the admin status of a user.

        Args:
            tg_id (int): Telegram user ID.
            status (int): New admin status.

        Returns:
            int: 0 if the update is successful.
        """
        user_obj = await User.filter(id=tg_id).first()

        if user_obj:
            user_obj.is_admin = status
            await user_obj.save()
            return 0
