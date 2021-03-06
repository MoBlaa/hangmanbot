"""Cooldowns of user actions"""

import json
import logging
import sys
import os
from datetime import datetime
from enum import IntEnum
from typing import Any

from settings import CONFIG_DIR, COOLDOWNS_FILE


class CooldownType(IntEnum):
    """Type of a cooldown"""

    REMOVE = 1
    GUESS = 2
    START = 3
    STATE = 4


class Cooldown:
    """A Cooldown of a single user"""
    __created: datetime
    seconds: int

    def __init__(self, seconds: int):
        self.__created = datetime.now()
        self.seconds = seconds

    def __seconds_since(self) -> int:
        now = datetime.now()
        since = now - self.__created
        return int(since.total_seconds())

    def expired(self) -> bool:
        """Returns if enough time has passed since creation of the cooldown"""
        return self.__seconds_since() >= self.seconds

    def expires_in(self) -> int:
        """Returns the seconds till the cooldown is expired"""
        return self.seconds - self.__seconds_since()

    def __str__(self):
        return f"Cooldown(at {self.__created} for {self.seconds}s)"

    def __repr__(self):
        return f"Cooldown({self.__created.__repr__()}, {self.seconds.__repr__()})"


DEFAULT_RM_COOLDOWN: int = 60
DEFAULT_START_COOLDOWN: int = 20
DEFAULT_GUESS_COOLDOWN: int = 5
DEFAULT_STATE_COOLDOWN: int = 60


class Cooldowns:
    """Manages cooldown for different commands based on channel."""

    __remove_cooldowns: {(int, int): Cooldown} = dict()
    __guess_cooldowns: {(int, int): Cooldown} = dict()
    __start_cooldowns: {(int, int): Cooldown} = dict()
    __state_cooldowns: {(int, int): Cooldown} = dict()
    cooldown_values: {(CooldownType, int): int} = dict()

    @classmethod
    def from_json(cls, data: [dict]):
        """Creates a instance of Cooldowns from json data"""
        logging.debug("Loaded cooldowns: %s", data)
        cooldowns = dict()
        for cooldown in data:
            cd_type, channel, value = cooldown['type'], cooldown['channel'], cooldown['value']
            cooldowns[(CooldownType(cd_type), channel)] = value
        return cls(cooldown_values=cooldowns)

    @classmethod
    def load(cls):
        """Reads persisted states of hangman games"""
        try:
            serialized = open(COOLDOWNS_FILE, "r").read()
            return cls.from_json(json.loads(serialized))
        except OSError as err:
            logging.debug("No Cooldowns file found to load (%s)", err)
            return cls()

    def __init__(self, cooldown_values: {(CooldownType, int): int} = None):
        self.cooldown_values = cooldown_values if cooldown_values else {}

    def __getitem__(self, item: (CooldownType, int, int)) -> Cooldown:
        cd_type, author, channel = item
        if cd_type == CooldownType.START:
            return self.__start_cooldowns.get((author, channel))
        if cd_type == CooldownType.REMOVE:
            return self.__remove_cooldowns.get((author, channel))
        if cd_type == CooldownType.GUESS:
            return self.__guess_cooldowns.get((author, channel))
        return self.__state_cooldowns.get((author, channel))

    def __contains__(self, item: (CooldownType, int, int)) -> bool:
        cd_type, author, channel = item
        if cd_type == CooldownType.START:
            return self.__start_cooldowns.__contains__((author, channel))
        if cd_type == CooldownType.REMOVE:
            return self.__remove_cooldowns.__contains__((author, channel))
        if cd_type == CooldownType.GUESS:
            return self.__guess_cooldowns.__contains__((author, channel))
        return self.__state_cooldowns.__contains__((author, channel))

    def __delitem__(self, key: (CooldownType, int, int)):
        cd_type, author, channel = key
        if cd_type == CooldownType.START:
            cds = self.__start_cooldowns
        elif cd_type == CooldownType.REMOVE:
            cds = self.__remove_cooldowns
        elif cd_type == CooldownType.GUESS:
            cds = self.__guess_cooldowns
        elif cd_type == CooldownType.STATE:
            cds = self.__state_cooldowns
        else:
            raise RuntimeError(f"Unsupported CooldownType: {cd_type}")
        cds.pop((author, channel), None)

    def __save(self):
        serialized = json.dumps(self, cls=CooldownsEncoder)
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            states_file = open(COOLDOWNS_FILE, "w")
            states_file.write(serialized)
        except OSError as err:
            logging.error("Couldn't write cooldowns file: %s", err)
            sys.exit(1)

    def __get_cooldown_seconds_for(self, key: (CooldownType, int)) -> int:
        seconds = self.cooldown_values.get(key)
        if seconds or seconds == 0:
            return seconds
        cd_type, _ = key
        if cd_type == CooldownType.START:
            return DEFAULT_START_COOLDOWN
        if cd_type == CooldownType.REMOVE:
            return DEFAULT_RM_COOLDOWN
        if cd_type == CooldownType.GUESS:
            return DEFAULT_GUESS_COOLDOWN
        return DEFAULT_STATE_COOLDOWN

    def set_cooldown(self, key: (CooldownType, int), value: int):
        """Sets a cooldown value for a type and channel"""
        self.cooldown_values[key] = value if value else 0
        self.__save()

    def get_cooldown(self, key: (CooldownType, int)) -> Cooldown:
        """Gets a cooldown value for a type and channel"""
        return Cooldown(self.cooldown_values.get(
            key,
            self.__get_cooldown_seconds_for(key)))

    def add_for(self, key: (CooldownType, int, int), cooldown: Cooldown = None):
        """Creates a cooldown for the given key (type, author_id, channel_id) and
        sets a default Cooldown based on the type and configured cooldown value."""
        cd_type, author, channel = key
        cooldown = cooldown if cooldown else Cooldown(
            self.__get_cooldown_seconds_for((cd_type, channel)))
        if cd_type == CooldownType.START:
            self.__start_cooldowns[(author, channel)] = cooldown
        elif cd_type == CooldownType.REMOVE:
            self.__remove_cooldowns[(author, channel)] = cooldown
        elif cd_type == CooldownType.GUESS:
            self.__guess_cooldowns[(author, channel)] = cooldown
        elif cd_type == CooldownType.STATE:
            self.__state_cooldowns[(author, channel)] = cooldown
        else:
            raise RuntimeError(f"Unsupported CooldownType: {cd_type}")
        self.__save()

    def clear(self, cd_type: CooldownType):
        """Clears a type of cooldown"""
        if cd_type == CooldownType.START:
            self.__start_cooldowns.clear()
        if cd_type == CooldownType.REMOVE:
            self.__remove_cooldowns.clear()
        if cd_type == CooldownType.STATE:
            self.__state_cooldowns.clear()
        if cd_type == CooldownType.GUESS:
            self.__guess_cooldowns.clear()


class CooldownsEncoder(json.JSONEncoder):
    """Implements serializing cooldowns to json"""
    def default(self, o: Any) -> Any:
        if isinstance(o, Cooldowns):
            cooldowns = []
            for key, value in o.cooldown_values.items():
                cd_type, channel = key
                cooldowns.append({'type': int(cd_type), 'channel': channel, 'value': value})
            return cooldowns
        return super().default(o)
