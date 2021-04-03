"""Discord Bot implementing a simple Hangman game."""

import logging
import discord
from discord.ext import commands
from settings import DISCORD_TOKEN
from states import States, Running, Solved, Failed
from cooldowns import cooldowns, Cooldown

logging.basicConfig(level=logging.INFO)


states = States.load()

bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    """Runs if the bot is ready"""
    print("Logged in as {0}".format(bot.user))


@bot.command(name="remove", aliases=["rm"])
async def __remove(ctx: commands.Context):
    channel_id = ctx.channel.id
    user_id = ctx.author.id
    if (channel_id not in states) or (not isinstance(states[channel_id], Running)):
        await ctx.send("No game to reset...")
    state = states[channel_id]
    if isinstance(state, Running):
        if state.author_id == user_id or ctx.author.server_permissions.administrator:
            del states[channel_id]
            await ctx.send("Current game was removed!")
        else:
            await ctx.send("You're not allowed to reset the game "
                           "(not author of game or admin of server)")


@bot.command(name="start_hangman", aliases=["s"])
@commands.bot_has_permissions(manage_messages=True)
async def __start_hangman(ctx: commands.Context, *, phrase: str):
    channel_id = ctx.channel.id
    author_id = ctx.author.id
    cooldown_id = (author_id, channel_id)

    if (channel_id in states) and isinstance(states[channel_id], Running):
        await ctx.send("A game is still running!")
        return

    if cooldown_id in cooldowns:
        cooldown = cooldowns[cooldown_id]
        if cooldown.expired():
            del cooldowns[cooldown_id]
        else:
            await ctx.send(f"{ctx.author.mention} still has a cooldown of {cooldown.expires_in()}")
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

    states[channel_id] = Running(phrase, author_id=ctx.author.id)
    cooldowns[cooldown_id] = Cooldown()

    await ctx.send(f"{states[channel_id]}")


@bot.command(name="guess", aliases=["g"])
async def __guess(ctx: commands.Context, *, guess: str):
    channel_id = ctx.channel.id
    author_id = ctx.author.id
    cooldown_id = (author_id, channel_id)

    if channel_id not in states:
        await ctx.send(
            "No guess running in this channel. "
            "Please start with `!s ||<phrase>||` first"
        )
        return

    if cooldown_id in cooldowns:
        cooldown = cooldowns[cooldown_id]
        if cooldown.expired():
            del cooldowns[cooldown_id]
        else:
            await ctx.send(f"{ctx.author.mention} still has a "
                           f"cooldown of {cooldown.expires_in()}s!")
            return

    guess = guess.strip()
    old_state = states[channel_id]
    if isinstance(old_state, Running) and old_state.author_id == author_id:
        await ctx.send("Authors are only allowed to reset the current game!")
        return

    new_state = old_state.guess(guess, ctx.author)

    cooldowns[cooldown_id] = Cooldown()

    await ctx.send(f"{new_state}")

    if isinstance(new_state, (Solved, Failed)):
        # Also add Cooldown for users which started the game so others can start a game
        cooldowns[cooldown_id] = Cooldown()

        del states[channel_id]
    else:
        states[channel_id] = new_state


@__start_hangman.error
@__guess.error
@__remove.error
async def __handle_error(ctx: commands.Context, error):
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.channel.send(
            "Bot is Missing permissions: manage_messages (to delete the start message)"
        )
        return
    print("Error: {0}".format(error))


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
