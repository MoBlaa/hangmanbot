"""Discord Bot implementing a simple Hangman game."""

import logging
import discord
from discord.ext import commands
from settings import DISCORD_TOKEN
from states import States, Running, Solved, Failed
from cooldowns import Cooldowns, CooldownType

logging.basicConfig(level=logging.INFO)


states = States.load()

cooldowns = Cooldowns.load()

bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    """Runs if the bot is ready"""
    print("Logged in as {0}".format(bot.user))


@bot.command(name="cooldown-get", aliases=["cd", "cooldown"])
@commands.has_permissions(administrator=True)
async def __get_cooldown(ctx: commands.Context, cd_type: str = None):
    channel_id = ctx.channel.id
    cd_type = cd_type.strip().lower()

    if cd_type in {'rm', 'remove'}:
        value = cooldowns.get_cooldown((CooldownType.REMOVE, channel_id))
    elif cd_type in {'guess', 'g'}:
        value = cooldowns.get_cooldown((CooldownType.GUESS, channel_id))
    elif cd_type in {'s', 'start_hangman'}:
        value = cooldowns.get_cooldown((CooldownType.START, channel_id))
    else:
        await ctx.send(f"Unknown cooldown type '{cd_type}'. "
                       f"Supported: 'rm|remove', 'g|guess', 's|start_hangman'")
        return
    value = f"{value.seconds}s" if value else "None"
    await ctx.send(f"Cooldown for '{cd_type}' in this channel: {value}")


@bot.command(name="cooldown-edit", aliases=["cd-edit", "cd-e"])
@commands.has_permissions(administrator=True)
async def __cooldown_edit(ctx: commands.Context, cd_type: str, value: int):
    channel_id = ctx.channel.id
    cd_type = cd_type.strip().lower()

    if cd_type in {'rm', 'remove'}:
        cooldowns.set_cooldown((CooldownType.REMOVE, channel_id), value)
    elif cd_type in {'guess', 'g'}:
        cooldowns.set_cooldown((CooldownType.GUESS, channel_id), value)
    elif cd_type in {'s', 'start_hangman'}:
        cooldowns.set_cooldown((CooldownType.START, channel_id), value)
    else:
        await ctx.send(f"Unknown cooldown type '{cd_type}'. "
                       f"Supported: 'rm|remove', 'g|guess', 's|start_hangman'")
        return

    await ctx.send(f"Successfully set cooldown of '{cd_type}' to {value}s")


@bot.command(name="remove", aliases=["rm"])
async def __remove(ctx: commands.Context):
    channel_id = ctx.channel.id
    author_id = ctx.author.id
    cooldown_id = (CooldownType.REMOVE, author_id, channel_id)
    if (channel_id not in states) or (not isinstance(states[channel_id], Running)):
        await ctx.send("No game to reset...")
    if cooldown_id in cooldowns:
        cooldown = cooldowns[cooldown_id]
        if not cooldown.expired():
            await ctx.send(f"{ctx.author.mention} removing allowed in {cooldown.expires_in()}s")
            return
    state = states[channel_id]
    if isinstance(state, Running):
        if state.author_id == author_id or ctx.author.server_permissions.administrator:
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
    cooldown_id = (CooldownType.START, author_id, channel_id)

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
    cooldowns.add_for(cooldown_id)

    await ctx.send(f"{states[channel_id]}")


@bot.command(name="guess", aliases=["g"])
async def __guess(ctx: commands.Context, *, guess: str):
    channel_id = ctx.channel.id
    author_id = ctx.author.id
    guess_cooldown_id = (CooldownType.GUESS, author_id, channel_id)
    remove_cooldown_id = (CooldownType.REMOVE, author_id, channel_id)
    start_cooldown_id = (CooldownType.START, author_id, channel_id)

    if channel_id not in states:
        await ctx.send(
            "No guess running in this channel. "
            "Please start with `!s ||<phrase>||` first"
        )
        return

    old_state = states[channel_id]
    if isinstance(old_state, Running) and old_state.author_id == author_id:
        await ctx.send("Authors are only allowed to reset the current game!")
        return

    if guess_cooldown_id in cooldowns:
        cooldown = cooldowns[guess_cooldown_id]
        if cooldown.expired():
            del cooldowns[guess_cooldown_id]
        else:
            await ctx.send(f"{ctx.author.mention} still has a "
                           f"cooldown of {cooldown.expires_in()}s!")
            return

    guess = guess.strip()
    new_state = old_state.guess(guess, ctx.author)
    states[channel_id] = new_state

    await ctx.send(f"{new_state}")

    if isinstance(new_state, (Solved, Failed)):
        # Also add Cooldown for users which started the game so others can start a game
        cooldowns.add_for(start_cooldown_id)

        del states[channel_id]
        # Cooldown on remove should be cleared to save space
        del cooldowns[remove_cooldown_id]
    if isinstance(new_state, Running) \
            and new_state.guessing_started() \
            and (remove_cooldown_id not in cooldowns):
        cooldowns.add_for(remove_cooldown_id)
    cooldowns.clear(CooldownType.GUESS)
    cooldowns.add_for(guess_cooldown_id)


@__start_hangman.error
@__guess.error
@__remove.error
@__cooldown_edit.error
@__get_cooldown.error
async def __handle_error(ctx: commands.Context, error):
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.channel.send(
            "Bot is Missing permissions: manage_messages (to delete the start message)"
        )
        return
    print("Error: {0}".format(error))


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
