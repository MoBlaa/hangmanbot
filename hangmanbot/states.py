"""States of hangman games"""

from __future__ import annotations
import logging
import json
import os
import sys
from typing import Any

import discord
from settings import STATES_FILE, CONFIG_DIR
from ascii import MAX_GUESSES, HANGMANS


class State:
    """Superclass for all States of the hangman game"""
    post_id: int

    def __init__(self, post_id: int = None):
        self.post_id = post_id

    def guess(self, _guess: str, _guesser: discord.Member) -> State:
        """Process a guess of a discord member.

        Args:
              _guess (str): The guessed phrase or character.
              _guesser (discord.Member): The discord member which guessed.

        """
        return self


class Running(State):
    """Hangman game is currently running and is not yet solved or failed."""

    author_id: int
    phrase: str
    unveiled: [bool]
    wrong_guesses: int
    guessed: {str}

    @classmethod
    def from_json(cls, data: dict) -> Running:
        """Parses this class from json deserialized data"""
        return Running(phrase=data['phrase'],
                       author_id=data['author_id'],
                       post_id=data['post_id'],
                       unveiled=data['unveiled'],
                       wrong_guesses=data['wrong_guesses'],
                       guessed=set(data['guessed']))

    def __init__(self, phrase: str, author_id: int, post_id: int = None, unveiled: [bool] = None,
                 wrong_guesses: int = None, guessed: {str} = None):
        super().__init__(post_id)
        if not phrase:
            raise ValueError("Word has to be a non empty string")
        self.phrase = phrase
        self.author_id = author_id
        if not unveiled:
            self.unveiled = [False for _ in range(len(phrase))]
        else:
            self.unveiled = unveiled
        self.guessed = set() if not guessed else guessed
        self.wrong_guesses = 0 if not wrong_guesses else wrong_guesses
        self.__solve(lambda char: not char.isalpha())

    def __unveiled(self) -> str:
        result = ""
        for index, char in enumerate(self.unveiled):
            if char:
                result += f" {self.phrase[index]} "
            else:
                result += " _ "
        return result

    def __guessed(self) -> str:
        result = ""
        for char in sorted(self.guessed):
            result += f"{char.upper()} "
        return result + ""

    def __solve(self, guess) -> bool:
        contained = False
        for index, char in enumerate(self.phrase):
            if guess(char):
                contained = True
                self.unveiled[index] = True
        return contained

    def guessing_started(self) -> bool:
        """Returns if someone has already started guessing"""
        return bool(self.guessed)

    def guess(self, guess: str, guesser: discord.Member):
        """Guessing a single character or the whole phrase"""
        # TODO: Remove
        # if guesser.id == self.author_id:
        #    return self

        guess = guess.lower()
        if len(guess) == 1:
            if guess in self.guessed:
                self.wrong_guesses += 1
                return self

            contained = self.__solve(
                lambda char: char.lower() == guess)

            if not contained:
                self.wrong_guesses += 1

            self.guessed.add(guess)
        elif self.phrase.lower() == guess:
            return Solved(phrase=self.phrase, solver_mention=guesser.mention, post_id=self.post_id)
        else:
            self.wrong_guesses += 1

        if self.wrong_guesses >= MAX_GUESSES:
            return Failed(self.phrase, post_id=self.post_id)
        if all(self.unveiled):
            return Solved(phrase=self.phrase, solver_mention=guesser.mention, post_id=self.post_id)
        return self

    def __str__(self) -> str:
        return f"```" \
               f"{HANGMANS[self.wrong_guesses]}\n" \
               f"{self.__guessed()}" \
               f"```" \
               f"```" \
               f"{self.__unveiled()}" \
               f"```" \
               f"Guess with `!g` or `!guess`"

    def __repr__(self):
        return f"Running(phrase={self.phrase}," \
               f"unveiled={self.unveiled}," \
               f"wrong_guesses={self.wrong_guesses}," \
               f"guessed={self.guessed})"


class Solved(State):
    """Hangman game was solved.

    Attributes:
        phrase (str): Phrase of the solved game.
        solver_mention (str): Mention String of the Member who solved the game.

    """
    phrase: str
    solver_mention: str

    @classmethod
    def from_json(cls, data: dict) -> Solved:
        """Parses this class from json deserialized data"""
        return Solved(phrase=data['phrase'], solver_mention=data['solver'], post_id=data['post_id'])

    def __init__(self, phrase: str, solver_mention: str, post_id: int):
        super().__init__(post_id)
        self.phrase = phrase
        self.solver_mention = solver_mention
        self.post_id = post_id

    def __str__(self) -> str:
        return f"__Solved!__ {self.solver_mention} won and guessed the phrase `{self.phrase}`"


class Failed(State):
    """Hangman game failed for the given phrase.

    Attributes:
        phrase (str): Phrase of the failed game.

    """
    phrase: str
    post_id: int

    @classmethod
    def from_json(cls, data: dict) -> Failed:
        """Parses this class from json deserialized data"""
        return Failed(phrase=data['phrase'], post_id=data['post_id'])

    def __init__(self, phrase: str, post_id: int):
        super().__init__(post_id)
        self.phrase = phrase
        self.post_id = post_id

    def __str__(self) -> str:
        return f"```" \
               f"{HANGMANS[MAX_GUESSES]}" \
               f"```" \
               f"__Failed!__ The phrase was ||{self.phrase}||"


class States:
    """Manages states of multiple channels and persists them on change"""
    states: {int: State} = {}

    def __init__(self, states: {int: State}):
        self.states = states

    def __getitem__(self, channel_id: int):
        return self.states[channel_id]

    def __setitem__(self, channel_id: int, state: State):
        self.states[channel_id] = state
        self.__save()

    def __delitem__(self, key):
        del self.states[key]
        self.__save()

    def __iter__(self):
        return self.states.__iter__()

    def __contains__(self, item):
        return self.states.__contains__(item)

    def __save(self):
        """Persists the current states of hangman games"""
        serialized = json.dumps(self.states, cls=StatesEncoder)
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            states_file = open(STATES_FILE, "w")
            states_file.write(serialized)
        except OSError as err:
            logging.error("Couldn't write states file: %s", err)
            sys.exit(1)

    @classmethod
    def from_json(cls, data: dict) -> States:
        """Parses this class from json deserialized data"""
        states = {}
        for key, val in data.items():
            key: int = int(key)
            if 'Solved' in val:
                states[key] = Solved.from_json(val['Solved'])
            elif 'Failed' in val:
                states[key] = Failed.from_json(val['Failed'])
            elif 'Running' in val:
                states[key] = Running.from_json(val['Running'])
            else:
                raise ValueError(f'Expected "Solved", "Failed" or "Running": {val}')
        logging.debug("Loaded States: %s", states)
        return States(states)

    @classmethod
    def load(cls) -> States:
        """Reads persisted states of hangman games"""
        try:
            serialized = open(STATES_FILE, "r").read()
            return cls.from_json(json.loads(serialized))
        except OSError as err:
            logging.debug("No states file found to load (%s)", err)
            return cls(states={})


class StatesEncoder(json.JSONEncoder):
    """Implements encoding for State implementations and States class"""
    def default(self, o: Any) -> Any:
        if isinstance(o, Running):
            return {
                'Running': {
                    'phrase': o.phrase,
                    'unveiled': o.unveiled,
                    'author_id': o.author_id,
                    'post_id': o.post_id,
                    'wrong_guesses': o.wrong_guesses,
                    'guessed': list(o.guessed),
                }
            }
        if isinstance(o, Solved):
            return {
                'Solved': {
                    'post_id': o.post_id,
                    'phrase': o.phrase,
                    'solver': o.solver_mention,
                }
            }
        if isinstance(o, Failed):
            return {
                'Failed': {
                    'post_id': o.post_id,
                    'phrase': o.phrase
                }
            }
        if isinstance(o, States):
            states: {int: State} = {}
            for channel, state in o.states:
                states[channel] = self.default(state)
            return states
        return super().default(o)
