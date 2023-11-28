from tortoise import fields
from tortoise.models import Model

from app.validators.user_validator import NullOrPositive


class User(Model):
    """
    Represents a Telegram user.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): User's username, can be null.
        is_admin (bool): Flag indicating if the user is an admin.
        notification (bool): Flag indicating if the user has notifications enabled.
        percent (float): User's percentage, default is 1.0.
        modified_at (datetime): Timestamp for the last modification.
    """

    id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=32, null=True, default=None)
    is_admin = fields.BooleanField(default=False)
    notification = fields.BooleanField(default=False)
    percent = fields.FloatField(null=True, default=1.0, validators=[NullOrPositive()])
    modified_at = fields.DatetimeField(auto_now=True)


class TradingPair(Model):
    """
    Represents a trading pair.

    Attributes:
        id (int): Unique identifier for the trading pair.
        pair (str): The trading pair identifier.
        market (str): The market where the trading pair belongs, default is "futures".
        price (float): The price of the trading pair, can be null.
        publication_date (datetime): Timestamp for the publication date.
    """

    id = fields.BigIntField(pk=True)
    pair = fields.CharField(max_length=60)
    market = fields.CharField(max_length=16, default="futures")
    price = fields.FloatField(default=None, validators=[NullOrPositive()])
    publication_date = fields.DatetimeField(auto_now_add=True)
