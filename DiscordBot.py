import discord
from discord.ext import commands
import subprocess
import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from pythonScripts import *
from pythonScripts.Helpers import *

logging_channels = [1046279004925206578, 1377780328034209954]
mia_id = 143411810672967680

with open(os.path.join(".","data","keys","config.json")) as f:
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
    print(f'Logged in as {client.user} (ID: {client.user.id})') # type: ignore
    print('------')

@client.event
async def on_message(message):
    if(message.channel.id in logging_channels):
        print(f'Message in {message.channel.guild}, from: {message.author}, with content: {message.content}')

        for attachment in message.attachments:
            if "The_Chase_VGM" in attachment.filename:
                output_path = os.path.join("./files", attachment.filename)
                await attachment.save(output_path)
                await message.delete()
                c = conn.cursor()

                c.execute("""SELECT MAX(id) FROM tracks""")
                tracks_before = c.fetchone()[0]

                e = GenerateData.new_episode(conn)
            
                if e is None:
                    c.execute("""
                        SELECT g.name, t.name 
                        FROM tracks as t
                        LEFT JOIN games as g ON t.game_id = g.id
                        WHERE t.id > ?
                    """, (tracks_before, ))
                    new_tracks = c.fetchall()

                    if(len(new_tracks) > 0):
                        msg = "Episode added. The following tracks were added:\n"
                        for game, track in new_tracks:
                            msg += f"\t{game} - {track}\n"
                        msg = msg[:-1] #remove last newline
                    else:
                        msg = "Episode added. No new tracks added."

                    await message.channel.send(msg)
                else:
                    await message.channel.send(str(e))


print("Bot starting...")
client.run(token)