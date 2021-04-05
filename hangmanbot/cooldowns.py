"""Cooldowns of user actions"""

import json
import sys
import os
from datetime import datetime
from enum import Enum
from settings import CONFIG_DIR, COOLDOWNS_FILE


class CooldownType(Enum):
    """Type of a cooldown"""

    REMOVE = 1
    GUESS = 2
    START = 3


class Cooldown:
    """A Cooldown of a single user"""
    __created: datetime
    __seconds: int

    def __init__(self, seconds: int):
        self.__created = datetime.now()
        self.__seconds = seconds

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
        return f"Cooldown(at {self.__created} for {self.__seconds}s)"

    def __repr__(self):
        return f"Cooldown({self.__created.__repr__()}, {self.__seconds.__repr__()})"


DEFAULT_RM_COOLDOWN: int = 60
DEFAULT_START_COOLDOWN: int = 20
DEFAULT_GUESS_COOLDOWN: int = 5


class Cooldowns:
    """Manages cooldown for different commands based on channel."""

    __remove_cooldowns: {(int, int): Cooldown} = dict()
    __guess_cooldowns: {(int, int): Cooldown} = dict()
    __start_cooldowns: {(int, int): Cooldown} = dict()
    __guess_cooldown_values: {(CooldownType, int): int}

    @classmethod
    def from_json(cls, data: dict):
        """Creates a instance of Cooldowns from json data"""
        return cls(guess_cooldown_values=data.get('guess_cooldowns'))

    @classmethod
    def load(cls):
        """Reads persisted states of hangman games"""
        try:
            serialized = open(CONFIG_DIR, "r").read()
            return cls.from_json(json.loads(serialized))
        except OSError as err:
            print(f"Failed to read states file: {err}")
            return cls()

    def __init__(self, guess_cooldown_values: {int: int} = None):
        self.__guess_cooldown_values = guess_cooldown_values if guess_cooldown_values else {}

    def __getitem__(self, item: (CooldownType, int, int)) -> Cooldown:
        cd_type, author, channel = item
        if cd_type == CooldownType.START:
            return self.__start_cooldowns.get((author, channel))
        if cd_type == CooldownType.REMOVE:
            return self.__remove_cooldowns.get((author, channel))
        return self.__guess_cooldowns.get((author, channel))

    def __contains__(self, item: (CooldownType, int, int)) -> bool:
        cd_type, author, channel = item
        if cd_type == CooldownType.START:
            return self.__start_cooldowns.__contains__((author, channel))
        if cd_type == CooldownType.REMOVE:
            return self.__remove_cooldowns.__contains__((author, channel))
        return self.__guess_cooldowns.__contains__((author, channel))

    def __save(self):
        serialized = json.dumps({'guess_cooldowns': self.__guess_cooldowns})
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            states_file = open(COOLDOWNS_FILE, "w")
            states_file.write(serialized)
        except OSError as err:
            print(f"Couldn't write cooldowns file: {err}")
            sys.exit(1)

    def __get_cooldown_seconds_for(self, key: (CooldownType, int)) -> int:
        seconds = self.__guess_cooldown_values.get(key)
        if seconds:
            return seconds
        cd_type, _ = key
        if cd_type == CooldownType.START:
            return DEFAULT_START_COOLDOWN
        if cd_type == CooldownType.REMOVE:
            return DEFAULT_RM_COOLDOWN
        return DEFAULT_GUESS_COOLDOWN

    def set_cooldown(self, key: (CooldownType, int), value: int):
        """Sets a cooldown value for a type and channel"""
        self.__guess_cooldown_values[key] = value if value else 0

    def add_for(self, key: (CooldownType, int, int), cooldown: Cooldown = None):
        """Creates a cooldown for the given key (type, author_id, channel_id) and
        sets a default Cooldown based on the type and configured cooldown value."""
        cd_type, author, channel = key
        cooldown = cooldown if cooldown else Cooldown(
            self.__get_cooldown_seconds_for((cd_type, channel)))
        if cd_type == CooldownType.START:
            self.__start_cooldowns[(author, channel)] = cooldown
        if cd_type == CooldownType.REMOVE:
            self.__remove_cooldowns[(author, channel)] = cooldown
        self.__guess_cooldowns[(author, channel)] = cooldown

    def clear(self, cd_type: CooldownType):
        """Clears a type of cooldown"""
        if cd_type == CooldownType.START:
            self.__start_cooldowns.clear()
        if cd_type == CooldownType.REMOVE:
            self.__remove_cooldowns.clear()
        self.__guess_cooldowns.clear()
