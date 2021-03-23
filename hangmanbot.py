import logging
import settings
import discord

logging.basicConfig(level=logging.INFO)

class Hangmanbot(discord.Client):
    async def on_ready(self):
        print('Logged in as {0}'.format(self.user))

    async def on_message(self, message: discord.Message):
        print('Message from {0.author}: {0.content}'.format(message))

client = Hangmanbot()
client.run(settings.DISCORD_TOKEN)