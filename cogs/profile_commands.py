import discord
from discord.ext import commands

# Imports from utils.py
from .utils import (
    PLAYER_DATA_FILE,
    MAPS,
    get_player_elo,
    get_player_stats,
    get_map_stats
)

# ====== حط هنا ID القناة اللي عايز فيها البروفايل ======
PROFILE_CHANNEL_ID = 1437876849207410921  # <<< غيّرها للـ ID بتاعك


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="p")
    async def profile_cmd(self, ctx, member: discord.Member = None):
        """Show player profile"""
        member = member or ctx.author

        # ---- GET PLAYER DATA ----
        elo = get_player_elo(member.id)
        stats = get_player_stats(member.id)
        map_stats = get_map_stats(member.id)

        wins = stats.get("wins", 0)
        losses = stats.get("losses", 0)
        cancels = stats.get("cancels", 0)

        warnings = stats.get("warnings", 0)
        cooldown_active = stats.get("cooldown", False)

        # ---- TITLE SYSTEM ----
        if elo >= 400:
            title = "Elite"
        elif elo >= 200:
            title = "Advanced"
        else:
            title = "Rookie"

        # ---- BUILD EMBED ----
        embed = discord.Embed(
            title=f"{member.name}'s Profile",
            color=discord.Color.gold()
        )

        embed.set_author(
            name=member.display_name,
            icon_url=member.avatar.url
        )

        embed.set_thumbnail(url=member.avatar.url)

        # Player Info
        embed.add_field(
            name="👤 Player Information",
            value=f"{member.mention}",
            inline=False
        )

        # Competitive Stats
        embed.add_field(
            name="🏆 Competitive Stats",
            value=f"> **Elo:** `{elo}`\n> **Title:** `{title}`\n",
            inline=False
        )

        # Game Stats
        embed.add_field(
            name="🎮 Game Statistics",
            value=(
                f"> **Wins:** `{wins}`\n"
                f"> **Losses:** `{losses}`\n"
                f"> **Cancels:** `{cancels}`\n"
            ),
            inline=False
        )

        # Status
        embed.add_field(
            name="⚠️ Status",
            value=(
                f"> **Cooldown:** {'🔴 Active' if cooldown_active else '🟢'}\n"
                f"> **Warnings:** `{warnings}`\n"
            ),
            inline=False
        )

        # ---- MAP STATS ----
        map_text = "-------------------------\n"

        for map_name, data in map_stats.items():
            w = data.get("wins", 0)
            l = data.get("losses", 0)
            c = data.get("cancels", 0)  # <-- NEW

            map_text += (
                f"**{map_name}**\n"
                f"Wins: `{w}`  |  Losses: `{l}` | Cancels: `{c}`\n\n"
            )

        embed.add_field(
            name="📍 Map Statistics",
            value=map_text,
            inline=False
        )

        embed.set_footer(text="Premium League • Profile System")

        # ========== SEND TO SPECIFIC CHANNEL ONLY ==========
        channel = ctx.guild.get_channel(PROFILE_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)

        try:
            await ctx.message.delete()
        except:
            pass


async def setup(bot):
    await bot.add_cog(Profile(bot))
