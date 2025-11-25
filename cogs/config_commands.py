import discord
from discord.ext import commands

ICON = "https://media.discordapp.net/attachments/1437876851132338339/1442818666751066122/2.png?ex=6926d118&is=69257f98&hm=51d18ef4146a01b290f7a6042bf7652e12abd466e0f39640a441dd7415fa71a1&=&format=webp&quality=lossless&width=834&height=834"

class ConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def config(self, ctx):

        embed = discord.Embed(
            title="⚙️ Premium League Config",
            description="**Config Information**",
            color=0x00aaff
        )

        embed.set_author(name=f"{ctx.guild.name}", icon_url=ICON)
        embed.set_thumbnail(url=ICON)

        embed.add_field(
            name="👑 Owner Bot :",
            value=f"<@{ctx.author.id}>",
            inline=False
        )

        embed.add_field(name="📌 GuildID :", value=f"`{ctx.guild.id}`", inline=False)

        embed.add_field(name="🗂️ CategoryID :", value="`1437876849534435375`", inline=False)

        embed.add_field(name="🧾 MatchLog :", value="https://discordapp.com/channels/1437876842014183526/1437876849207410922", inline=False)

        embed.add_field(name="⛔ ChannelWarning :", value="https://discordapp.com/channels/1437876842014183526/1437876849207410923", inline=False)

        embed.add_field(name="🎉 ChannelGivePoint :", value="https://discordapp.com/channels/1437876842014183526/1437876848938848506", inline=False)

        embed.add_field(name="📊 ChannelStatsProfile :", value="https://discordapp.com/channels/1437876842014183526/1437876849207410921", inline=False)

        embed.add_field(
            name="👤 PUG Approved  :",
            value="<@&1437876842014183532>",
            inline=False
        )

        embed.add_field(
            name="📝 ScoreReporter :",
            value="<@&1437876842404118684>",
            inline=False
        )

        embed.add_field(
            name="👀 Spectator :",
            value="<@&1437876842395603001>",
            inline=False
        )

        embed.add_field(
            name="🛠️ PUG Admin :",
            value="<@&1437876842404118686>",
            inline=False
        )

        embed.add_field(
            name="❄️ CoolDown :",
            value="<@&1437876842014183529>",
            inline=False
        )

        embed.add_field(name="📌 Point Win :", value="**10**", inline=True)
        embed.add_field(name="📌 Point Loss :", value="**7**", inline=True)

        embed.set_footer(text="⚡ Powered by Premium League", icon_url=ICON)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ConfigCommands(bot))
