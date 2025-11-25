import discord
from discord.ext import commands
from .match_system import create_match_channels

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def startmatch(self, ctx):
        players = ctx.channel.members
        await create_match_channels(ctx.guild, players)

async def setup(bot):
    await bot.add_cog(MatchCommands(bot))
