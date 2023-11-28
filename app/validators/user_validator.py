from tortoise.exceptions import ValidationError
from tortoise.validators import Validator


class NullOrPositive(Validator):
    """
    Validator to ensure that the provided value is greater than or equal to zero or null.
    """

    def __call__(self, value: int):
        """
        Validates if the provided value is greater than or equal to zero or null.

        Args:
        - value (int): The value to be validated.

        Raises:
        - ValidationError: If the provided value is less than zero.
        """
        if value < 0:
            raise ValidationError("Provided value should be positive")
