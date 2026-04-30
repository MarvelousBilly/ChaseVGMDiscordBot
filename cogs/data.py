import random

import discord
from typing import Optional
import datetime
from discord import app_commands
from discord.ext import commands
import math

from pythonScripts import GetTracks
from pythonScripts.Helpers import *
from pythonScripts import GeneralSQL
from pythonScripts import GameSearch
from pythonScripts import ManageData



glorpability = 66



#view for the buttons for track pages
class TrackButtonView(discord.ui.View):
    def __init__(self, conn, game_name, per_page, filename):
        super().__init__(timeout=600)
        _, self.game_name = get_id_and_formatted_game_name(conn, game_name)
        self.track_plays = GetTracks.get_track_plays(conn, self.game_name)
        self.page = 1
        self.per_page = per_page
        self.total_pages = max(math.ceil(len(self.track_plays) / self.per_page), 1)
        self.embeds = [None]
        self.update_buttons()

        # Pre-generate all embeds using filename passed in
        for self.page in range(1, self.total_pages+1):
            self.embeds.append(GetTracks.get_track_embed(conn, self.game_name, self.track_plays, self.page, self.per_page, self.total_pages, filename)) # type: ignore
        self.page = 1
    
    @classmethod
    async def create(cls, conn, game_name, per_page, bot, user):
        global glorpability

        filename = None
        rand_val = random.randint(0, glorpability)
        print(rand_val, glorpability)
        if rand_val == 0:
            glorpability -= 1
            if glorpability == 0:
                glorpability = 100
            random_glorp = random.randint(0, 43)
            filename = os.path.join(".", "data", "glorp", f"glorp{random_glorp:02d}.png")

            channel = bot.get_channel(1046279004925206578)
            await channel.send(f"GLORP HIT!!! Glorpability is now {glorpability}. {user} got Rare Glorp Number {random_glorp}!")

        return cls(conn, game_name, per_page, filename=filename)

    def update_buttons(self):
        self.children[0].disabled = self.page == 1 # type: ignore
        self.children[1].disabled = self.page == self.total_pages # type: ignore
    
    @discord.ui.button(emoji='\u23EA', style=discord.ButtonStyle.grey)
    async def left_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.page][0], view=self) # type: ignore

    @discord.ui.button(emoji='\u23E9', style=discord.ButtonStyle.grey)
    async def right_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages:
            self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.page][0], view=self) # type: ignore

class Data(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tracks", description="""Displays the tracks that have played for the game""")
    @app_commands.describe(game='Game')
    async def tracks(self, interaction: discord.Interaction, game: str):
        print(f"------\n{interaction.user} wants to know the tracks for {game}. [{datetime.datetime.now()}]")

        conn = GeneralSQL.connect()
        match, game_name, _, msg = GameSearch.search(conn, game)
        if(match):
            if(game_name == "UNBEATABLE" and (game.lower() != game and game.upper() != game)): 
                await interaction.response.send_message("literally die", ephemeral=True)
                return

            per_page = 7

            view = await TrackButtonView.create(conn, game_name, per_page, self.bot, interaction.user)
            embed, file = view.embeds[view.page] # type: ignore
            view.update_buttons()
            await interaction.response.send_message(embed=embed, file=file, view=view)
            
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="hailmarygame", description="""Displays how far from Hail Mary is a certain game""")
    @app_commands.describe(game='Game')
    async def hailmarygame(self, interaction: discord.Interaction, game: str):
        print(f"------\n{interaction.user} wants to know where {game} is in hail mary. [{datetime.datetime.now()}]")
        conn = GeneralSQL.connect()
        match, game_name, game_id, msg = GameSearch.search(conn, game)
        if(match):
            if(game_name == "UNBEATABLE" and (game.lower() != game and game.upper() != game)): 
                await interaction.response.send_message("literally die", ephemeral=True)
                return

            msg = ManageData.hail_mary_game(conn, game_id)
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    #TODO: pregenerate the hail mary and dead game lists when a new episode drops, and just grab the file whenever you need to update
    @app_commands.command(name="hailmary", description="""Displays Hail Mary games""")
    async def hailmary(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to know the hail mary list. [{datetime.datetime.now()}]")
        conn = GeneralSQL.connect()

        msg = ManageData.hail_mary(conn)
        with open(os.path.join(".","files","hailmary.txt"), 'w', encoding='utf-8-sig', errors='replace') as f:
            f.write(msg)
        await interaction.response.send_message(file=discord.File(os.path.join(".","files","hailmary.txt")))

    @app_commands.command(name="deadgame", description="""Displays bottom 25 games by their last play in any mode""")
    async def deadgame(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to know the dead game list. [{datetime.datetime.now()}]")
        conn = GeneralSQL.connect()

        msg = ManageData.dead_games(conn, 25)
        with open(os.path.join(".","files","deadgames.txt"), 'w', encoding='utf-8-sig', errors='replace') as f:
            f.write(msg)
        await interaction.response.send_message(file=discord.File(os.path.join(".","files","deadgames.txt")))

    @app_commands.command(name="points", description="""Displays how many points you have, and how much your next sub would cost""")
    @app_commands.describe(player='Player')
    async def points(self, interaction: discord.Interaction, player: Optional[discord.Member] = None):
        print(f"------\n{interaction.user} wants to know how many points {player} has. [{datetime.datetime.now()}]")
        player = player or interaction.user # type: ignore

        conn = GeneralSQL.connect()
        msg = ManageData.points(conn, player)
        await interaction.response.send_message(msg)

    @app_commands.command(name="submissions", description="""Displays all games this player has submitted""")
    @app_commands.describe(player='Player')
    async def submissions(self, interaction: discord.Interaction, player: Optional[discord.Member] = None):
        print(f"------\n{interaction.user} wants to know {player}'s submissions. [{datetime.datetime.now()}]")
        player = player or interaction.user # type: ignore

        conn = GeneralSQL.connect()
        msg = ManageData.submissions(conn, player)
        await interaction.response.send_message(msg)

    
    @app_commands.command(name="hailmarysubmissions", description="""Displays how far from Hail Mary is all this player's subs are""")
    @app_commands.describe(player='Player')
    async def hailmarysubmissions(self, interaction: discord.Interaction, player: Optional[discord.Member] = None):
        print(f"------\n{interaction.user} wants to know where {player}'s games are in hail mary. [{datetime.datetime.now()}]")
        player = player or interaction.user # type: ignore

        conn = GeneralSQL.connect()
        msg = ManageData.hail_mary_submissions(conn, player)
        await interaction.response.send_message(msg)


    @app_commands.command(name="boostdata", description="""Displays the boost score for a given game""")
    @app_commands.describe(game='Game')
    async def boostdata(self, interaction: discord.Interaction, game: str):
        print(f"------\n{interaction.user} wants to know the boost data for {game}. [{datetime.datetime.now()}]")
        conn = GeneralSQL.connect()
        match, game_name, game_id, msg = GameSearch.search(conn, game)

        if(match):
            if(game_name == "UNBEATABLE" and (game.lower() != game and game.upper() != game)): 
                await interaction.response.send_message("literally die", ephemeral=True)
                return

            msg, eph = ManageData.boost_data(conn, game_id, game_name)
            await interaction.response.send_message(msg, ephemeral=eph)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="veryhard", description="""Displays the Very Hard games, those that have a boost score of -2 or less""")
    async def veryhard(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to know the very hard data. [{datetime.datetime.now()}]")
        conn = GeneralSQL.connect()

        msg = ManageData.very_hard(conn)
        with open(os.path.join(".","files","veryhard.txt"), 'w', encoding='utf-8', errors='replace') as f:
            f.write(msg)
        await interaction.response.send_message(file=discord.File(os.path.join(".","files","veryhard.txt")))


async def setup(bot):
    await bot.add_cog(Data(bot))