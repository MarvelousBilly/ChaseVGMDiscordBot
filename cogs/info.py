import discord
import datetime
from discord import app_commands
from discord.ext import commands
from pythonScripts import NextBatch
import textwrap

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="spreadsheets", description="""Print most major spreadsheets people use""")
    async def spreadsheets(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to know the spreadsheets. [{datetime.datetime.now()}]")
        message = textwrap.dedent("""\
            [Chase Scoreboard](<https://docs.google.com/spreadsheets/d/1GznrCAUaUxofszlk79bgJGEri5t1xoSzBASrXnVsLl0>)
            [The List 2.0](<https://docs.google.com/spreadsheets/d/1vKRBWECF4VV2PLXP_h2XNrNOpFqSJxkmz0kHsnc6lPw>)
            [The Bot's Confirmed Track List](<https://docs.google.com/spreadsheets/d/1_UdKlca1olhvFfx0yRLleZvcYL5NWCeyxs-N8mlg9aA>)
            [Shelldude's Confirmed Track List](<https://docs.google.com/spreadsheets/d/1FNL1T25OFi73CzcbbAIKSm5fLvcjrceSo2TUiTzYBe0>)
            [Taffer's Confirmed Track List](<https://docs.google.com/spreadsheets/d/14kiOBkbamw2nKjZz08F9gwGCHhQKDjV6t4jcgr_q80U>)
            [Aak boost data](<https://docs.google.com/spreadsheets/d/1qJ1Pkeqy7DTlGwDymSalzyUXKJZfYPIi6r3Qvq7KXHE>)
        """)
        await interaction.response.send_message(message)

    @app_commands.command(name="top100", description="""Print the spreadsheets for each Top 100""")
    async def top100(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to know the top 100 data. [{datetime.datetime.now()}]")
        message = textwrap.dedent("""\
            [5th Chase's Choice RESULTS + Stats](<https://docs.google.com/spreadsheets/d/1VWj6rL0snJCwjwh_9U3DU_M4QcNbCJrmGn07GkJu-ns>)
            [5th Chase's Choice RESULTS](<https://docs.google.com/spreadsheets/d/1qZOvJi5KXCijy6482n5f5PFezdj2YbC7dnePxYIpV4s>)
            [4th Chase's Choice RESULTS + Stats](<https://docs.google.com/spreadsheets/d/1xPuD5lUcD394XXfssSTf0k0XLMeyaAWxLFruX9Ebos8>)
            [4th Chase's Choice RESULTS](<https://docs.google.com/spreadsheets/d/1fCvRAvYCgvtqpx_1djmqdmIvHQ385MOrunnP7cmAItc>)
            [3rd Chase's Choice RESULTS + Stats](<https://docs.google.com/spreadsheets/d/1LZY6XA8cngGiHYviXfw-OsCcdbqkBtubSJrlW-mucVI>)
            [3rd Chase's Choice RESULTS](<https://docs.google.com/spreadsheets/d/1NhMvQoZEzrZXZvtt6GisytO1KjpBTAvvTxJrYkXKjwI>)
            [2nd Chase's Choice RESULTS](<https://docs.google.com/spreadsheets/d/1FSxe1pwDRT5qvYRGVi4_-VcxjXEC1UllXjxBtzjU5EY>)
            [1st Chase's Choice RESULTS](<https://docs.google.com/spreadsheets/d/1XtqlU1Rjvm1hcvqX2PacsS4YKKAc37Qh5hFG5YAioFs>)
        """)
        await interaction.response.send_message(message)
        
    @app_commands.command(name="x00", description="""Print all of the X00 episodes (200, 300, 400, ...)""")
    async def x00(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to know the x00 episodes. [{datetime.datetime.now()}]")
        message = textwrap.dedent("""\
            [Episode 200](<https://youtu.be/bkmHRs7sNWY>)
            [Episode 300](<https://youtu.be/XqEixNDsUyg>)
            [Episode 400](<https://youtu.be/4yP7uvrPZFs>)
            [Episode 500](<https://youtu.be/pqLJJ4Z9pro>)
            [Episode 600](<https://youtu.be/z4Z0eI9OmlU>)
            [Episode 700](<https://www.youtube.com/playlist?list=PLVVkQ8yRRzHWbHkeyYFdpkAvsAmnYQ5yW>)
        """)
        await interaction.response.send_message(message)

    @app_commands.command(name="specials", description="""Print all of the Special episodes (X00, Top 100, and Masters)""")
    async def specials(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to know the special episodes. [{datetime.datetime.now()}]")
        await interaction.response.send_message("[Special Episode Playlist](https://www.youtube.com/playlist?list=PLLGK1dKhseIJbiWWgMgeltK_RP14ilIs3)")

    @app_commands.command(name="vgmv", description="""Link to the VGMV MusicBee plugin""")
    async def vgmv(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants VGMV. [{datetime.datetime.now()}]")
        await interaction.response.send_message("""[VGMV Github download link for MusicBee](https://github.com/MarvelousBilly/Musicbee-VGMV-plugin/releases)""")
        
    @app_commands.command(name="youtube", description="""Link to the ChaseVGM Youtube Channel""")
    async def youtube(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants YouTube. [{datetime.datetime.now()}]")
        await interaction.response.send_message("""[The ChaseVGM YouTube channel](https://www.youtube.com/@thechasevgm7623/videos)""")

    @app_commands.command(name="boostsuggestion", description="""Link to the Boost Suggestion Form""")
    async def boostsuggestion(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to boost suggest. [{datetime.datetime.now()}]")
        await interaction.response.send_message("""[Boost Suggestion Form](https://forms.gle/ffULn7ZALg5353dj9)""")

    @app_commands.command(name="nextbatch", description="""Displays when the next batch reveal is""")
    async def nextbatch(self, interaction: discord.Interaction):
        print(f"------\n{interaction.user} wants to know when the next batch is. [{datetime.datetime.now()}]")
        await interaction.response.send_message(NextBatch.print_batch(datetime.datetime.today().date()))

async def setup(bot):
    await bot.add_cog(Info(bot))