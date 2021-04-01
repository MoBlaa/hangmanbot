import logging
from settings import DISCORD_TOKEN
import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)


class State:
    def guess(self, guess: str, guesser: discord.Member):
        return self


MAX_GUESSES = 5


class Running(State):
    phrase: str
    unveiled: [bool]
    wrong_guesses: int

    def __init__(self, phrase: str):
        if not phrase:
            raise ValueError("Word has to be a non empty string")
        self.phrase = phrase
        self.unveiled = [False for _ in range(len(phrase))]
        self.wrong_guesses = 0
        self.__solve(lambda char: not char.isalnum())

    def __unveiled(self) -> str:
        result = ""
        for index, char in enumerate(self.unveiled):
            if char:
                result += f" {self.phrase[index]} "
            else:
                result += " _ "
        return result

    def __solve(self, guess) -> bool:
        contained = False
        for index, char in enumerate(self.phrase):
            if guess(char):
                contained = True
                self.unveiled[index] = True
        return contained

    def guess(self, guess: str, guesser: discord.Member):
        """Guessing a single character or the whole phrase"""
        if len(guess) == 1:
            contained = self.__solve(
                lambda char: char.lower() == guess.lower())

            if not contained:
                self.wrong_guesses += 1
        elif self.phrase.lower() == guess.lower():
            return Solved(phrase=self.phrase, solver=guesser)
        else:
            self.wrong_guesses += 1

        if self.wrong_guesses >= MAX_GUESSES:
            return Failed(self.phrase)
        elif all(self.unveiled):
            return Solved(phrase=self.phrase, solver=guesser)
        else:
            return self

    def __str__(self) -> str:
        return f"Remaining Bad Guesses:\t{MAX_GUESSES - self.wrong_guesses}\n```\n{self.__unveiled()}\n```"


class Solved(State):
    phrase: str
    solver: discord.Member

    def __init__(self, phrase: str, solver: discord.Member):
        self.phrase = phrase
        self.solver = solver

    def __str__(self) -> str:
        return f"__Solved!__ {self.solver.mention} won and guessed the phrase `{self.phrase}`"


class Failed(State):
    phrase: str

    def __init__(self, phrase: str):
        self.phrase = phrase

    def __str__(self) -> str:
        return f"__Failed!__ The phrase was `{self.phrase}`"


states = {}

bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    print("Logged in as {0}".format(bot.user))


@bot.command(name="start_hangman")
@commands.bot_has_permissions(manage_messages=True)
async def __start_hangman(ctx: commands.Context, phrase: str):
    channel_id = ctx.channel.id
    phrase = phrase.replace("!start_hangman", "").strip(" |")
    if len(phrase) <= 2:
        raise ValueError("Word has to be at least 3 characters long")
    if not isinstance(ctx.channel, discord.TextChannel) and not isinstance(
            ctx.channel, discord.GroupChannel):
        await ctx.send("Can only start hangman in text or group channels")
        return

    await ctx.message.delete()

    states[channel_id] = Running(phrase)
    await ctx.send(f"{states.get(channel_id)}")


@bot.command(name="guess")
async def __guess(ctx: commands.Context, guess: str):
    channel_id = ctx.channel.id
    if (channel_id not in states) and (not isinstance(states.get(channel_id),
                                                      Running)):
        await ctx.send(
            "No guess running in this channel. Please start with `!start_hangman ||<phrase>||` first"
        )
        return

    guess = guess.strip()
    states[channel_id] = states.get(channel_id).guess(guess, ctx.author)

    await ctx.send(f"{states[channel_id]}")

    if isinstance(states.get(channel_id), Solved):
        del states[channel_id]


@__start_hangman.error
@__guess.error
async def handle_error(ctx: commands.Context, error):
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.channel.send(
            "Bot is Missing permissions: manage_messages (to delete the start message)"
        )
        return
    print("Error: {0}".format(error))


bot.run(DISCORD_TOKEN)
