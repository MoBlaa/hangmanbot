"""Cooldowns of user actions"""

from datetime import datetime

COOLDOWN_SECONDS = 10


class Cooldown:
    """A Cooldown of a single user"""
    __created: datetime
    __seconds: int

    def __init__(self, seconds: int = None):
        self.__created = datetime.now()
        self.__seconds = seconds if seconds else COOLDOWN_SECONDS

    def __seconds_since(self) -> int:
        now = datetime.now()
        since = now - self.__created
        return int(since.total_seconds())

    def expired(self) -> bool:
        """Returns if enough time has passed since creation of the cooldown"""
        return self.__seconds_since() >= self.__seconds

    def expires_in(self) -> int:
        """Returns the seconds till the cooldown is expired"""
        return self.__seconds - self.__seconds_since()

    def __str__(self):
        return f"Cooldown(at{self.__created} for {self.__seconds}s)"

    def __repr__(self):
        return f"Cooldown({self.__created.__repr__()}, {self.__seconds.__repr__()})"
