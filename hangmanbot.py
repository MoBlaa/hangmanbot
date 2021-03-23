import logging
import settings
import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix="!")

@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send("Pong")

bot.run(settings.DISCORD_TOKEN)