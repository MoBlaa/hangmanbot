"""Discord Bot implementing a simple Hangman game."""

import logging
import discord
from discord.ext import commands
from settings import DISCORD_TOKEN
from states import States, Running, Solved

logging.basicConfig(level=logging.INFO)


states = States.load()

bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    """Runs if the bot is ready"""
    print("Logged in as {0}".format(bot.user))


@bot.command(name="start_hangman", aliases=["s"])
@commands.bot_has_permissions(manage_messages=True)
async def __start_hangman(ctx: commands.Context, *, phrase: str):
    channel_id = ctx.channel.id

    if (channel_id in states) and isinstance(states[channel_id], Running):
        await ctx.send("A game is still running!")
        return

    phrase = phrase.replace("!start_hangman", "").strip(" |")
    if len(phrase) <= 2:
        await ctx.send("Phrase has to be at least 3 characters long")
        return
    if not isinstance(ctx.channel, discord.TextChannel) and not isinstance(
            ctx.channel, discord.GroupChannel):
        await ctx.send("Can only start hangman in text or group channels")
        return

    await ctx.message.delete()

    states[channel_id] = Running(phrase)
    await ctx.send(f"{states[channel_id]}")


@bot.command(name="guess", aliases=["g"])
async def __guess(ctx: commands.Context, *, guess: str):
    channel_id = ctx.channel.id
    if (channel_id not in states) and (not isinstance(states[channel_id],
                                                      Running)):
        await ctx.send(
            "No guess running in this channel. "
            "Please start with `!start_hangman ||<phrase>||` first"
        )
        return

    guess = guess.strip()
    old_state = states[channel_id]
    states[channel_id] = old_state.guess(guess, ctx.author)

    await ctx.send(f"{states[channel_id]}")

    if isinstance(states[channel_id], Solved):
        del states[channel_id]


@__start_hangman.error
@__guess.error
async def __handle_error(ctx: commands.Context, error):
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.channel.send(
            "Bot is Missing permissions: manage_messages (to delete the start message)"
        )
        return
    print("Error: {0}".format(error))


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
