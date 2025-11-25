import re
import discord
from discord.ext import commands
from datetime import datetime

# IMPORT FROM UTILS
from .utils import (
    add_win,
    add_loss,
    add_cancel,
    update_player_elo,
    get_player_elo,
    normalize_map_name
)

MATCH_LOG_CHANNEL_ID = 1437876849207410922


# ========== SCORE REPORTER COG ==========
class ScoreReporter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # -------- FIND MATCH EMBED --------
    async def _find_match_message(self, channel):
        async for msg in channel.history(limit=200):
            if msg.author == self.bot.user and msg.embeds:
                emb = msg.embeds[0]
                if emb.title.startswith("🎮 Match"):
                    return msg, emb
        return None, None


    # -------- .PT --------
    @commands.command()
    async def pt(self, ctx, *, text: str):

        role = discord.utils.get(ctx.author.roles, name="Score Reporter")
        if not role:
            return await ctx.send("❌ You need Score Reporter role.", delete_after=5)

        if not ctx.channel.name.startswith("match"):
            return await ctx.send("❌ Use this only in a match channel.", delete_after=5)

        match_msg, emb = await self._find_match_message(ctx.channel)
        if not match_msg:
            return await ctx.send("⚠️ No match embed found.", delete_after=5)

        players = []
        for f in emb.fields:
            if f.name.startswith(("🔴", "🔵")):
                for line in f.value.split("\n"):
                    m = re.search(r"<@!?(\d+)>", line)
                    if m:
                        uid = int(m.group(1))
                        if uid != ctx.author.id:
                            players.append(f"<@{uid}>")

        msg = f"**📢 TEXT MESSAGE:** `{text}`\n\n" + "\n".join(players)
        await ctx.send(msg)

        try:
            await ctx.message.delete()
        except:
            pass


    # -------- MATCH FINISH COMMANDS --------
    @commands.command()
    async def t1win(self, ctx):
        await self._finish_match(ctx, "Black List Victory")

    @commands.command()
    async def t2win(self, ctx):
        await self._finish_match(ctx, "Global Risk Victory")

    @commands.command()
    async def cancel(self, ctx):
        await self._finish_match(ctx, "Match Cancelled")


    # -------- FINISH MATCH CORE --------
    async def _finish_match(self, ctx, winner_text):

        # Check Role
        role = discord.utils.get(ctx.author.roles, name="Score Reporter")
        if not role:
            return await ctx.send("❌ لازم رول Score Reporter")

        # Must be inside a match channel
        if not ctx.channel.name.startswith("match"):
            return await ctx.send("❌ Use inside match channel only.")

        # Find match embed
        match_msg, emb = await self._find_match_message(ctx.channel)
        if not match_msg:
            return await ctx.send("⚠️ Match embed not found.")

        match_id = emb.title.replace("🎮 Match #", "").strip()

        # Extract map
        map_field = next((f for f in emb.fields if "Map Selected" in f.name), None)
        map_name = map_field.value if map_field else "Unknown"
        map_name = normalize_map_name(map_name)

        # Extract teams
        black_f = next((f for f in emb.fields if "Black List" in f.name), None)
        global_f = next((f for f in emb.fields if "Global Risk" in f.name), None)

        black_players = [int(m.group(1)) for m in re.finditer(r"<@!?(\d+)>", black_f.value)]
        global_players = [int(m.group(1)) for m in re.finditer(r"<@!?(\d+)>", global_f.value)]

        # ===== LOGS =====
        elo_log = []
        new_black_lines = []
        new_global_lines = []


        # -------- BLACK WINS --------
        if "Black List" in winner_text:

            for pid in black_players:
                add_win(pid, map_name)
                old, new = update_player_elo(pid, +10)
                elo_log.append(f"<@{pid}> — `{old}` → `{new}`")
                new_black_lines.append(f"<@{pid}> `{new} ELO`")

            for pid in global_players:
                add_loss(pid, map_name)
                old, new = update_player_elo(pid, -7)
                elo_log.append(f"<@{pid}> — `{old}` → `{new}`")
                new_global_lines.append(f"<@{pid}> `{new} ELO`")


        # -------- GLOBAL WINS --------
        elif "Global Risk" in winner_text:

            for pid in global_players:
                add_win(pid, map_name)
                old, new = update_player_elo(pid, +10)
                elo_log.append(f"<@{pid}> — `{old}` → `{new}`")
                new_global_lines.append(f"<@{pid}> `{new} ELO`")

            for pid in black_players:
                add_loss(pid, map_name)
                old, new = update_player_elo(pid, -7)
                elo_log.append(f"<@{pid}> — `{old}` → `{new}`")
                new_black_lines.append(f"<@{pid}> `{new} ELO`")


        # -------- CANCEL --------
        else:
            for pid in black_players + global_players:
                add_cancel(pid, map_name)

            new_black_lines = [f"<@{pid}> `{get_player_elo(pid)} ELO`" for pid in black_players]
            new_global_lines = [f"<@{pid}> `{get_player_elo(pid)} ELO`" for pid in global_players]


        # ===== SEND MATCH LOG =====
        log_ch = ctx.guild.get_channel(MATCH_LOG_CHANNEL_ID)

        log_embed = discord.Embed(
            title=f"🎮 Match #{match_id} Results",
            description="**📊 Match Summary**\n────────────────────",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        log_embed.add_field(
            name="",
            value=(
                f"🗺 **Map:** `{map_name}`\n"
                f"🏆 **Winner:** {winner_text}\n"
                f"📝 **Reporter:** {ctx.author.mention}"
            ),
            inline=False
        )

        log_embed.add_field(name="────────────────────", value="", inline=False)

        log_embed.add_field(
            name="🔴 Black List Team",
            value="\n".join([f"`{i+1}.` {line}" for i, line in enumerate(new_black_lines)]),
            inline=True
        )

        log_embed.add_field(
            name="🔵 Global Risk Team",
            value="\n".join([f"`{i+1}.` {line}" for i, line in enumerate(new_global_lines)]),
            inline=True
        )

        if elo_log:
            log_embed.add_field(
                name="📈 ELO Updates",
                value="\n".join(elo_log),
                inline=False
            )

        if emb.thumbnail:
            log_embed.set_thumbnail(url=emb.thumbnail.url)

        log_embed.set_footer(
            text=f"Match Log System • {datetime.utcnow().strftime('%m/%d/%Y • %I:%M %p')}"
        )

        await log_ch.send(embed=log_embed)

        # ===== DELETE VOICE + TEXT CHANNEL =====
        clean = match_id.replace(" ", "")
        for vc in ctx.guild.voice_channels:
            if clean in vc.name.replace(" ", "").replace("〡", ""):
                try:
                    await vc.delete()
                except:
                    pass

        await ctx.channel.delete()



async def setup(bot):
    await bot.add_cog(ScoreReporter(bot))
