import discord
from discord.ext import commands
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from pythonScripts import *
from pythonScripts.Helpers import *

logging_channels = [1046279004925206578, 1377780328034209954]
mia_id = 143411810672967680

with open(os.path.join(".","data","config.json")) as f:
    d = json.load(f)
    token = d["token"]
    client_id = d["clientId"]
    guild_id = discord.Object(id=d["guildId"])

class MyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.silly")
        await self.load_extension("cogs.info")
        await self.load_extension("cogs.data")

        self.tree.copy_global_to(guild=guild_id)
        await self.tree.sync(guild=guild_id)

client = MyClient()

conn = GeneralSQL.connect()

@client.event
async def on_ready():
    await client.tree.sync()
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.event
async def on_message(message):
    if(message.channel.id in logging_channels):
        print(f'Message in {message.channel.guild}, from: {message.author}, with content: {message.content}')

print("Bot starting...")
client.run(token)