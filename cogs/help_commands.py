import discord
from discord.ext import commands
from datetime import datetime, timedelta

ICON = "https://media.discordapp.net/attachments/1437876851132338339/1442818666751066122/2.png?ex=6926d118&is=69257f98&hm=51d18ef4146a01b290f7a6042bf7652e12abd466e0f39640a441dd7415fa71a1&=&format=webp&quality=lossless&width=834&height=834"


def egypt_time():
    return (datetime.utcnow() + timedelta(hours=2)).strftime("%A • %d %b %Y • %I:%M %p")


class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="phelp")
    async def help_cmd(self, ctx):

        embed = discord.Embed(
            title="📘 Premium League • Help Menu",
            description="**List of all available commands**",
            color=0x00aaff
        )

        embed.set_author(
            name="Premium League Help Center",
            icon_url=ICON
        )
        embed.set_thumbnail(url=ICON)

        # ================================
        #   QUEUE SYSTEM
        # ================================
        embed.add_field(
            name="🎮 **Queue System Commands**",
            value=(
                "• `.queuepanel` — Create the queue panel\n"
                "• *(Auto)* Join/Leave buttons inside panel\n"
            ),
            inline=False
        )

        # ================================
        #   SUB SYSTEM
        # ================================
        embed.add_field(
            name="🔄 **Substitution System**",
            value=(
                "• `.needsub <old_player>` — Request auto replacement from queue\n"
                "• `.replace <old> <new>` — Admin replace manually\n"
            ),
            inline=False
        )

        # ================================
        #   WARNING SYSTEM
        # ================================
        embed.add_field(
            name="⚠️ **Warning System**",
            value=(
                "• `.warn <player> <reason>` — Add warning\n"
                "• `.removewarn <player>` — Remove one warning\n"
                "• `.warnings <player>` — Show user warns\n"
                "• *(Auto)* 3, 7, 10 warns → cooldown\n"
            ),
            inline=False
        )

        # ================================
        #   COOLDOWN SYSTEM
        # ================================
        embed.add_field(
            name="⏳ **Cooldown System**",
            value=(
                "• `.c-d <player>` — Check cooldown information\n"
                "• *(Auto)* Cooldown role applied when player reaches 3, 7, 10 warns\n"
            ),
            inline=False
        )

        # ================================
        #   ELO SYSTEM
        # ================================
        embed.add_field(
            name="🏅 **ELO System**",
            value=(
                "• `.sendelo <player> <amount>` — Give ELO\n"
                "• `.takeelo <player> <amount>` — Remove ELO\n"
                "• `.setelo <player> <amount>` — Set ELO manually\n"
            ),
            inline=False
        )

        # ================================
        #   CONFIG
        # ================================
        embed.add_field(
            name="⚙️ **Configuration**",
            value=(
                "• `.config` — Show full Premium League configuration\n"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"⭐ Premium League • {egypt_time()}",
            icon_url=ICON
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
