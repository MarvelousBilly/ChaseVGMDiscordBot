import random
import discord
from discord import app_commands
from discord.ext import commands

class Silly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="klonoa", description="Klonoa says hi :)")
    async def klonoa(self, interaction: discord.Interaction):
        if random.random() < 0.1:
            await interaction.response.send_message(
                f'<a:klonoa:1376402124623187978> says: FUCK YOU, {interaction.user.mention} <a:cuh:1373433106106941441>'
            )
        else:
            await interaction.response.send_message(
                f'<a:klonoa:1376402124623187978> says: Wahoo! <a:fuh:1382929987925053522>'
            )

async def setup(bot):
    await bot.add_cog(Silly(bot))