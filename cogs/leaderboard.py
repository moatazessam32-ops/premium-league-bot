import discord
from discord.ext import commands
from .utils import load_json, PLAYER_DATA_FILE

# ⬅️ ضع هنا ID قناة الـ leaderboard
LEADERBOARD_CHANNEL_ID = 1437876849207410921


def get_title(elo):
    if elo >= 3000: return "🥇 Legend"
    elif elo >= 2500: return "🔥 Master"
    elif elo >= 2000: return "💎 Diamond"
    elif elo >= 1500: return "⭐ Platinum"
    elif elo >= 1000: return "🥈 Gold"
    elif elo >= 500: return "🥉 Silver"
    return "⚪ Bronze"


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx):

        # ❌ لو القناة غلط
        if ctx.channel.id != LEADERBOARD_CHANNEL_ID:
            return await ctx.send(
                f"❌ This command can only be used in <#{LEADERBOARD_CHANNEL_ID}>",
                delete_after=5
            )

        data = load_json(PLAYER_DATA_FILE)

        if not data:
            return await ctx.send("⚠️ No players found.")

        # Sort by ELO
        sorted_players = sorted(
            data.items(),
            key=lambda x: x[1]["elo"],
            reverse=True
        )

        top = sorted_players[:25]

        desc = "__**The most skilled players in our arena**__\n\n"

        rank_emojis = ["👑", "🥈", "🥉"]

        for i, (pid, stats) in enumerate(top, start=1):

            user = ctx.guild.get_member(int(pid))
            name = user.mention if user else f"`Unknown ({pid})`"

            emoji = rank_emojis[i-1] if i <= 3 else f"#{i}"

            desc += f"**{emoji}** {name} — ``{stats['elo']}`` **ELO**\n"

        embed = discord.Embed(
            title="Premium League",
            description="🏆 **Top 25 Elite Champions** 🏆\n" + desc,
            color=discord.Color.gold()
        )

        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1433880842551296081/1440201538017689631/05ec3e25-8481-416b-8927-aaa0a66d853c.png"
        )

        embed.set_footer(
            text=f"Premium League • Updated Leaderboard • Today at {discord.utils.utcnow().strftime('%I:%M %p')}"
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
