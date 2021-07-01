"""Discord Bot implementing a simple Hangman game."""

import logging
import discord
from discord.ext import commands

from hangmanbot.player import Player
from settings import DISCORD_TOKEN
from states import States, Running, Solved, Failed
from cooldowns import Cooldowns, CooldownType

logging.basicConfig(level=logging.DEBUG)


states = States.load()

cooldowns = Cooldowns.load()

bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    """Runs if the bot is ready"""
    logging.info("Logged in as %s", bot.user)


@bot.command(name="cooldown-get", aliases=["cd", "cooldown"], help="Get the cooldown value for a command")
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
                       f"Supported: 'rm|remove', 'g|guess', 's|start_hangman'", delete_after=5)
        return
    value = f"{value.seconds}s" if value else "None"
    await ctx.send(f"Cooldown for '{cd_type}' in this channel: {value}")


@bot.command(name="cooldown-edit", aliases=["cd-edit", "cd-e"], help="Edit/Set the cooldown value for a command")
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


@bot.command(name="remove", aliases=["rm"], help="Remove the current game")
async def __remove(ctx: commands.Context):
    channel_id = ctx.channel.id
    author_id = ctx.author.id
    cooldown_id = (CooldownType.REMOVE, author_id, channel_id)
    if (channel_id not in states) or (not isinstance(states[channel_id], Running)):
        await ctx.send("No game to reset...", delete_after=2)
    if cooldown_id in cooldowns:
        cooldown = cooldowns[cooldown_id]
        if not cooldown.expired():
            expires_in = cooldown.expires_in()
            await ctx.send(f"{ctx.author.mention} removing allowed in {expires_in}s",
                           delete_after=expires_in)
            return
    state = states[channel_id]
    if isinstance(state, Running):
        if state.author.id == author_id or ctx.author.server_permissions.administrator:
            message = await ctx.fetch_message(state.post_id)
            await message.delete()
            del states[channel_id]
            await ctx.send("Current game was removed!", delete_after=2)
        else:
            await ctx.send("You're not allowed to reset the game "
                           "(not author of game or admin of server)", delete_after=5)


@bot.command(name="state", help="Repost the game state message")
@commands.bot_has_permissions(manage_messages=True)
async def __post_state(ctx: commands.Context):
    channel_id = ctx.channel.id
    author_id = ctx.author.id
    cooldown_id = (CooldownType.STATE, author_id, channel_id)

    # Delete !state message
    await ctx.message.delete()

    if channel_id not in states:
        await ctx.send("No Game running!", delete_after=5)
        return

    if cooldown_id in cooldowns:
        cooldown = cooldowns[cooldown_id]
        if cooldown.expired():
            del cooldowns[cooldown_id]
        else:
            expires_in = cooldown.expires_in()
            await ctx.send(f"{ctx.author.mention} still has a cooldown of {expires_in}",
                           delete_after=expires_in)
            return

    state = states[channel_id]
    # Create new state and only delet old state if new state posting was successful
    old_message = await ctx.fetch_message(state.post_id)
    new_message = await ctx.send(f"{state}")
    state.post_id = new_message.id
    # Re-Add so it's stored properly
    states[channel_id] = state
    await old_message.delete()

    cooldowns.add_for(cooldown_id)


@bot.command(name="start_hangman", aliases=["s"], help="Start a new game")
@commands.bot_has_permissions(manage_messages=True)
async def __start_hangman(ctx: commands.Context, *, phrase: str):
    channel_id = ctx.channel.id
    author_id = ctx.author.id
    cooldown_id = (CooldownType.START, author_id, channel_id)

    if (channel_id in states) and isinstance(states[channel_id], Running):
        await ctx.send("A game is still running!", delete_after=2)
        return

    if cooldown_id in cooldowns:
        cooldown = cooldowns[cooldown_id]
        if cooldown.expired():
            del cooldowns[cooldown_id]
        else:
            expires_in = cooldown.expires_in()
            await ctx.send(f"{ctx.author.mention} still has a cooldown of {expires_in}",
                           delete_after=expires_in)
            return

    phrase = phrase.replace("!start_hangman", "").strip(" |")
    if len(phrase) <= 2:
        await ctx.send("Phrase has to be at least 3 characters long", delete_after=10)
        return
    if not isinstance(ctx.channel, discord.TextChannel) and not isinstance(
            ctx.channel, discord.GroupChannel):
        await ctx.send("Can only start hangman in text or group channels", delete_after=10)
        return

    await ctx.message.delete()

    state = Running(phrase, author=Player.from_user(ctx.author))
    cooldowns.add_for(cooldown_id)

    message = await ctx.send(f"{state}")
    state.post_id = message.id
    states[channel_id] = state


@bot.command(name="guess", aliases=["g"], help="Guess a character or the whole phrase")
@commands.bot_has_permissions(manage_messages=True)
async def __guess(ctx: commands.Context, *, guess: str):
    channel_id = ctx.channel.id
    author_id = ctx.author.id
    guess_cooldown_id = (CooldownType.GUESS, author_id, channel_id)
    remove_cooldown_id = (CooldownType.REMOVE, author_id, channel_id)
    start_cooldown_id = (CooldownType.START, author_id, channel_id)

    # Delete message at last to remove spam
    await ctx.message.delete(delay=2)

    if channel_id not in states:
        await ctx.send(
            "No guess running in this channel. "
            "Please start with `!s ||<phrase>||` first",
            delete_after=10
        )
        return

    old_state = states[channel_id]
    if isinstance(old_state, Running) and old_state.author.id == author_id:
        await ctx.send("Authors are only allowed to reset the current game!", delete_after=5)
        return

    if guess_cooldown_id in cooldowns:
        cooldown = cooldowns[guess_cooldown_id]
        if cooldown.expired():
            del cooldowns[guess_cooldown_id]
        else:
            expires_in = cooldown.expires_in()
            await ctx.send(f"{ctx.author.mention} still has a cooldown of {expires_in}s!",
                           delete_after=expires_in)
            return

    guess = guess.strip()
    new_state = old_state.guess(guess, ctx.author)
    states[channel_id] = new_state

    if isinstance(new_state, (Solved, Failed)):
        # Unveil all remaining characters in old state if solved
        assert isinstance(old_state, Running)
        if isinstance(new_state, Solved):
            old_state.unveil()
        # Update Message to show hanged man
        message = await ctx.fetch_message(old_state.post_id)
        await message.edit(content=f"{old_state}")

        # Create new post so everyone is mentioned properly and gamestate is still
        # visible after the game was finished
        await ctx.send(f"{new_state}")

        # Also add Cooldown for users which started the game so others can start a game
        cooldowns.add_for(start_cooldown_id)

        del states[channel_id]
        # Cooldown on remove should be cleared to save space
        del cooldowns[remove_cooldown_id]
    if isinstance(new_state, Running):
        # Edit game post if still running
        message = await ctx.fetch_message(new_state.post_id)
        await message.edit(content=f"{new_state}")

        if new_state.guessing_started() and (remove_cooldown_id not in cooldowns):
            cooldowns.add_for(remove_cooldown_id)
    cooldowns.clear(CooldownType.GUESS)
    cooldowns.add_for(guess_cooldown_id)


@__start_hangman.error
@__guess.error
@__remove.error
@__cooldown_edit.error
@__get_cooldown.error
@__post_state.error
async def __handle_error(ctx: commands.Context, error):
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.channel.send(
            "Missing permission: manage_messages (to delete its own and command messages)"
        )
        return
    logging.error("Error: %s", error)


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
