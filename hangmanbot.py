import logging
import settings
import discord
from enum import Enum

logging.basicConfig(level=logging.INFO)

class State:
    def guess(self, guess: str, guesser: discord.Member):
        return self

MAX_GUESSES = 5
class Running(State):
    word: str
    unveiled: [bool]
    wrong_guesses: int

    def __init__(self, word: str):
        if not word:
            raise ValueError("Word has to be a non empty string")
        self.word = word
        self.unveiled = [False for _ in range(len(word))]
        self.wrong_guesses = 0

    def __unveiled(self) -> str:
        result = ""
        for index, char in enumerate(self.unveiled):
            if char:
                result += f" {self.word[index]} "
            else:
                result += " _ "
        return result
    
    def guess(self, guess: str, guesser: discord.Member):
        """Guessing a single character or the whole word"""
        if len(guess) == 1:
            contained = False
            for index, char in enumerate(self.word):
                if char.lower() == guess.lower():
                    contained = True
                    self.unveiled[index] = True
            
            if not contained:
                self.wrong_guesses += 1
        elif self.word.lower() == guess.lower():
            return Solved(word=self.word, solver=guesser)
        else:
            self.wrong_guesses += 1

        if self.wrong_guesses >= MAX_GUESSES:
            return Failed(self.word)
        elif all(self.unveiled):
            return Solved(word=self.word, solver=guesser)
        else:
            return self
    
    def __str__(self) -> str:
        return f"Remaining Bad Guesses:\t{MAX_GUESSES - self.wrong_guesses}\n```\n{self.__unveiled()}\n```"

class Solved(State):
    word: str
    solver: discord.Member

    def __init__(self, word: str, solver: discord.Member):
        self.word = word
        self.solver = solver

    def __str__(self) -> str:
        return f"__Solved!__ {self.solver.mention} won and guessed the word `{self.word}`"

class Failed(State):
    word: str

    def __init__(self, word: str):
        self.word = word

    def __str__(self) -> str:
        return f"__Failed!__ The word was `{self.word}`"

class Hangmanbot(discord.Client):
    states = {}

    async def on_ready(self):
        print('Logged in as {0}'.format(self.user))

    async def on_message(self, message: discord.Message):
        if message.author.display_name.startswith(settings.DISCORD_DISPLAY_NAME):
            return

        print('Message from {0.author}: {0.content}'.format(message))

        if message.content.startswith("!start_hangman"):
            word = message.content.replace("!start_hangman", "").strip(" |")
            if len(word) <= 2:
                raise ValueError("Word has to be at least 3 characters long")
            if not isinstance(message.channel, discord.TextChannel) and not isinstance(message.channel, discord.GroupChannel):
                await message.channel.send("Can only start hangman in text or group channels")
                return
            
            await message.delete()

            self.states[message.channel.id] = Running(word)
            await message.channel.send(f"{self.states.get(message.channel.id)}")
        elif message.content.startswith("!guess"):
            if (message.channel.id not in self.states) and (not isinstance(self.states.get(message.channel.id), Running)):
                await message.channel.send("No guess running in this channel. Please start with `!start <word>` first")
                return

            guess = message.content.replace("!guess", "").strip()
            self.states[message.channel.id] = self.states.get(message.channel.id).guess(guess, message.author)
            await message.channel.send(f"{self.states[message.channel.id]}")

            if isinstance(self.states.get(message.channel.id), Solved):
                del self.states[message.channel.id]

client = Hangmanbot()
client.run(settings.DISCORD_TOKEN)