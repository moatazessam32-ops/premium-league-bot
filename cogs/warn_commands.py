import discord
from discord.ext import commands
from datetime import datetime, timedelta
from .utils import load_json, save_json
from .config import WARN_DATA_FILE, SUSPEND_CHANNEL_ID, WARN_CHANNEL_ID
from .cooldown_commands import load_susp, save_susp

ICON = "https://media.discordapp.net/attachments/1437876851132338339/1442818666751066122/2.png?ex=6926d118&is=69257f98&hm=51d18ef4146a01b290f7a6042bf7652e12abd466e0f39640a441dd7415fa71a1&=&format=webp&quality=lossless&width=834&height=834"
SUSPEND_LOG_CHANNEL = 1437876849207410924  # نفس قناة الكول داون


# -------------------------------------------------------
# Footer with Egypt Time 🇪🇬
# -------------------------------------------------------
def footer_time():
    egypt = datetime.utcnow() + timedelta(hours=2)
    return f"⭐ Premium League • {egypt.strftime('%A • %d %b %Y • %I:%M %p')}"


class WarnCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_queue_panel(self):
        return self.bot.get_cog("QueuePanel")

    # -----------------------------------------------------
    # ADD WARNING
    # -----------------------------------------------------
    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await ctx.message.delete()
        except:
            pass

        # Permission check
        if not ctx.author.guild_permissions.administrator and not discord.utils.get(ctx.author.roles, name="PUG Admin"):
            return await ctx.send("❌ You don't have permission to warn players.", delete_after=5)

        data = load_json(WARN_DATA_FILE)
        uid = str(member.id)

        data.setdefault(uid, []).append({
            "reason": reason,
            "by": ctx.author.id,
            "timestamp": str(datetime.utcnow())
        })
        save_json(WARN_DATA_FILE, data)

        total_warns = len(data[uid])

        # SEND TO WARN CHANNEL (TEXT ONLY)
        warn_channel = ctx.guild.get_channel(WARN_CHANNEL_ID)
        if warn_channel:
            await warn_channel.send(
                f"{ctx.author.mention} **Warn Reason:** {reason}\n"
                f"- **Total Warns:** `{total_warns}`\n"
                f"- **Player:** **{member.mention} (`{member.id}`)**"
            )

        # LOG EMBED
        suspend_channel = ctx.guild.get_channel(SUSPEND_CHANNEL_ID)
        if suspend_channel:

            embed = discord.Embed(title="🔴 Added Warning 🔴", color=0x00aaff)
            embed.set_author(name="Premium League • Warning System", icon_url=ICON)
            embed.set_thumbnail(url=ICON)

            embed.add_field(
                name="",
                value=(
                    f"**》Administrator:** {ctx.author.mention} (`{ctx.author.id}`)\n\n"
                    f"**》Member:** {member.mention} (`{member.id}`)\n\n"
                    f"**》Reason:** **{reason}**\n\n"
                    "────────────────────────────────────────"
                ),
                inline=False
            )

            embed.add_field(
                name="\u200b",
                value="```fix\n🛡️ نــظــام الــمــراقــبــة الــمــتــقــدم\n```",
                inline=False
            )

            embed.set_footer(text=footer_time(), icon_url=ICON)

            await suspend_channel.send(embed=embed)

        # -----------------------------------------------------
        # AUTO COOLDOWN BASED ON WARN COUNTS
        # -----------------------------------------------------
        if total_warns in [3, 7, 10]:

            duration = {3: 3, 7: 10, 10: 30}[total_warns]

            susp = load_susp()
            expiry = datetime.utcnow() + timedelta(days=duration)
            susp[str(member.id)] = {"expires": expiry.isoformat()}
            save_susp(susp)

            cd_role = discord.utils.get(ctx.guild.roles, name="COOL DOWN")
            if cd_role:
                await member.add_roles(cd_role)

            log_ch = ctx.guild.get_channel(SUSPEND_LOG_CHANNEL)
            if log_ch:

                cd_embed = discord.Embed(
                    title="⏳ Auto Cooldown Applied",
                    color=0xff0000
                )

                cd_embed.set_author(
                    name="⭐ Premium League • Auto System ⭐",
                    icon_url=ICON
                )
                cd_embed.set_thumbnail(url=ICON)

                cd_embed.add_field(
                    name="👤 Member",
                    value=f"{member.mention} (`{member.id}`)",
                    inline=False
                )

                cd_embed.add_field(
                    name="📋 Reason",
                    value=f"```fix\n{total_warns} Warnings\n```",
                    inline=False
                )

                cd_embed.add_field(
                    name="⏱️ Duration",
                    value=f"```fix\n{duration} Days\n```",
                    inline=False
                )

                cd_embed.set_footer(text=footer_time(), icon_url=ICON)

                await log_ch.send(embed=cd_embed)

        # REMOVE FROM QUEUE
        qp = self.get_queue_panel()
        if qp and qp.view:
            qv = qp.view
            if member in qv.players:
                qv.players.remove(member)
                if qv.message:
                    await qv.message.edit(embed=qv.build_embed(), view=qv)
                await ctx.send(
                    f"⚠️ {member.mention} was removed from the queue due to warning.",
                    delete_after=5
                )

    # -----------------------------------------------------
    # REMOVE WARNING
    # -----------------------------------------------------
    @commands.command()
    async def removewarn(self, ctx, member: discord.Member):
        try:
            await ctx.message.delete()
        except:
            pass

        if not ctx.author.guild_permissions.administrator and not discord.utils.get(ctx.author.roles, name="PUG Admin"):
            return await ctx.send("❌ You don't have permission.", delete_after=5)

        data = load_json(WARN_DATA_FILE)
        uid = str(member.id)

        if uid not in data or len(data[uid]) == 0:
            return await ctx.send("ℹ️ This user has no warnings.")

        removed = data[uid].pop(0)
        save_json(WARN_DATA_FILE, data)

        # SEND TEXT MESSAGE TO WARN CHANNEL
        warn_channel = ctx.guild.get_channel(WARN_CHANNEL_ID)
        if warn_channel:
            remaining = len(data[uid])
            await warn_channel.send(
                f"{ctx.author.mention} **Removed Warn:** {removed['reason']}\n"
                f"- **Remaining Warns:** `{remaining}`\n"
                f"- **Player:** **{member.mention} (`{member.id}`)**"
            )

        suspend_channel = ctx.guild.get_channel(SUSPEND_CHANNEL_ID)
        if suspend_channel:

            embed = discord.Embed(title="🟢 Removing Warn 🟢", color=0xffaa00)
            embed.set_author(name="Premium League • Warning System", icon_url=ICON)
            embed.set_thumbnail(url=ICON)

            embed.add_field(
                name="",
                value=(
                    f"**》👑 Administrator:** {ctx.author.mention}\n\n"
                    f"**》👤 Member:** {member.mention}\n\n"
                    f"**》📋 Removed Reason:** {removed['reason']}\n\n"
                    "────────────────────────────────────────"
                ),
                inline=False
            )

            embed.add_field(
                name="\u200b",
                value="```fix\n🛡️ نــظــام الــمــراقــبــة الــمــتــقــدم\n```",
                inline=False
            )

            embed.set_footer(text=footer_time(), icon_url=ICON)

            await suspend_channel.send(embed=embed)

        await ctx.send(f"✅ Removed 1 warn from {member.mention}", delete_after=5)

    # -----------------------------------------------------
    # SHOW WARNINGS
    # -----------------------------------------------------
    @commands.command()
    async def warnings(self, ctx, member: discord.Member):
        data = load_json(WARN_DATA_FILE)
        uid = str(member.id)

        if uid not in data:
            return await ctx.send(f"ℹ️ {member.mention} has no warnings.")

        embed = discord.Embed(
            title=f"⚠️ Warnings for {member}",
            color=discord.Color.orange()
        )

        for i, w in enumerate(data[uid], 1):
            admin = ctx.guild.get_member(w["by"])
            embed.add_field(
                name=f"{i}. By {admin if admin else 'Unknown'}",
                value=f"Reason: {w['reason']}\nTime: {w['timestamp']}",
                inline=False
            )

        embed.set_footer(text=footer_time(), icon_url=ICON)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WarnCommands(bot))
