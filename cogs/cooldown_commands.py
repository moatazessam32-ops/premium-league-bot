import discord
import os
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from .utils import load_json, save_json

# ICON موحّد
ICON = "https://media.discordapp.net/attachments/1437876851132338339/1442818666751066122/2.png?ex=6926d118&is=69257f98&hm=51d18ef4146a01b290f7a6042bf7652e12abd466e0f39640a441dd7415fa71a1&=&format=webp&quality=lossless&width=834&height=834"

# ملفات مهمّة
SUSP_FILE = "data/suspensions.json"

# قنوات الرسائل:
TEXT_LOG_CH = 1437876849207410923   # رسالة عادية بدون Embed
EMBED_LOG_CH = 1437876849207410924  # Embed احترافي


# -------------------------------------------------------
# Footer with Egypt Time
# -------------------------------------------------------
def footer_time():
    egypt = datetime.utcnow() + timedelta(hours=2)
    return f"⭐ Premium League • {egypt.strftime('%A • %d %b %Y • %I:%M %p')}"


# ----------------------------------------------
# Create file if missing
# ----------------------------------------------
if not os.path.exists(SUSP_FILE):
    with open(SUSP_FILE, "w") as f:
        f.write("{}")


def load_susp():
    return load_json(SUSP_FILE)


def save_susp(data):
    save_json(SUSP_FILE, data)


# -------------------------------------------------
# Required by queue_panel.py
# -------------------------------------------------
def is_suspended(user_id: int):
    data = load_susp()
    uid = str(user_id)

    if uid not in data:
        return False

    try:
        expires = datetime.fromisoformat(data[uid]["expires"])
    except:
        return False

    return datetime.utcnow() < expires


# ===========================================================
# COG — COOL DOWN SYSTEM
# ===========================================================
class CooldownCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_checker.start()

    # ----------------------------------------------
    # Auto remove expired cooldowns every 30 sec
    # ----------------------------------------------
    @tasks.loop(seconds=30)
    async def cooldown_checker(self):
        data = load_susp()
        now = datetime.utcnow()
        changed = False

        for user_id, entry in list(data.items()):
            try:
                expires = datetime.fromisoformat(entry["expires"])
            except:
                continue

            if now >= expires:
                guild = self.bot.guilds[0]
                member = guild.get_member(int(user_id))
                cd_role = discord.utils.get(guild.roles, name="COOL DOWN")

                if member and cd_role:
                    try:
                        await member.remove_roles(cd_role)
                    except:
                        pass

                # Send normal clean text message
                text_ch = guild.get_channel(TEXT_LOG_CH)
                if text_ch:
                    await text_ch.send(
                        f"✅ **Cooldown Ended for:** <@{user_id}> (`{user_id}`)"
                    )

                # Send embed
                embed_ch = guild.get_channel(EMBED_LOG_CH)
                if embed_ch:
                    embed = discord.Embed(
                        title="⏳ Cooldown Ended",
                        color=0x00ff44
                    )
                    embed.set_author(name="Premium League • Auto System", icon_url=ICON)
                    embed.set_thumbnail(url=ICON)
                    embed.add_field(
                        name="👤 Member",
                        value=f"<@{user_id}> (`{user_id}`)",
                        inline=False
                    )
                    embed.add_field(
                        name="📊 Status",
                        value="```fix\nCooldown Finished Automatically\n```",
                        inline=False
                    )
                    embed.set_footer(text=footer_time(), icon_url=ICON)
                    await embed_ch.send(embed=embed)

                del data[user_id]
                changed = True

        if changed:
            save_susp(data)

    # -------------------------------------------------------
    # MANUAL COOLDOWN COMMAND
    # .c-d @user <days> <reason>
    # -------------------------------------------------------
    @commands.command(name="c-d")
    async def cooldown(self, ctx, member: discord.Member, days: int, *, reason="No reason provided"):
        try:
            await ctx.message.delete()
        except:
            pass

        if not ctx.author.guild_permissions.administrator and not discord.utils.get(ctx.author.roles, name="PUG Admin"):
            return await ctx.send("❌ No permission.", delete_after=5)

        data = load_susp()
        expiry = datetime.utcnow() + timedelta(days=days)
        data[str(member.id)] = {"expires": expiry.isoformat()}
        save_susp(data)

        cd_role = discord.utils.get(ctx.guild.roles, name="COOL DOWN")
        if cd_role:
            await member.add_roles(cd_role)

        # TEXT MESSAGE
        text_ch = ctx.guild.get_channel(TEXT_LOG_CH)
        if text_ch:
            await text_ch.send(
                f"{ctx.author.mention} **CoolDown Reason:** {reason}\n"
                f"- **`#` Duration:** {days} days\n"
                f"- **`#` Player:** {member.mention} (`{member.id}`)"
            )

        # EMBED
        embed_ch = ctx.guild.get_channel(EMBED_LOG_CH)
        if embed_ch:
            embed = discord.Embed(
                title="⏳ Manual Cooldown Applied",
                color=0xff0000
            )
            embed.set_author(name="Premium League • Admin System", icon_url=ICON)
            embed.set_thumbnail(url=ICON)
            embed.add_field(name="👑 Administrator", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=False)
            embed.add_field(name="👤 Member", value=f"{member.mention} (`{member.id}`)", inline=False)
            embed.add_field(name="🕰️ Duration", value=f"```fix\n{days} Days\n```", inline=False)
            embed.add_field(name="📋 Reason", value=f"```fix\n{reason}\n```", inline=False)
            embed.set_footer(text=footer_time(), icon_url=ICON)
            await embed_ch.send(embed=embed)

        await ctx.send(f"⛔ {member.mention} is now on Cooldown ({days} days).", delete_after=2)

    # -------------------------------------------------------
    # REMOVE COOL DOWN — .uncd @user
    # -------------------------------------------------------
    @commands.command()
    async def uncd(self, ctx, member: discord.Member):
        try:
            await ctx.message.delete()
        except:
            pass

        if not ctx.author.guild_permissions.administrator and not discord.utils.get(ctx.author.roles, name="PUG Admin"):
            return await ctx.send("❌ No permission.", delete_after=5)

        data = load_susp()
        uid = str(member.id)

        if uid not in data:
            return await ctx.send("ℹ️ This user is not in cooldown.", delete_after=5)

        del data[uid]
        save_susp(data)

        cd_role = discord.utils.get(ctx.guild.roles, name="COOL DOWN")
        if cd_role:
            try:
                await member.remove_roles(cd_role)
            except:
                pass

        # TEXT
        text_ch = ctx.guild.get_channel(TEXT_LOG_CH)
        if text_ch:
            await text_ch.send(
                f"🟢 **Cooldown Removed:** {member.mention} (`{member.id}`)"
            )

        # EMBED
        embed_ch = ctx.guild.get_channel(EMBED_LOG_CH)
        if embed_ch:
            embed = discord.Embed(
                title="🟢 Cooldown Removed",
                color=0x00ff44
            )
            embed.set_author(name="Premium League • Admin System", icon_url=ICON)
            embed.set_thumbnail(url=ICON)
            embed.add_field(name="Member", value=f"{member.mention} (`{member.id}`)", inline=False)
            embed.add_field(name="Action", value="```fix\nCooldown Removed Manually\n```", inline=False)
            embed.add_field(name="Administrator", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=False)
            embed.set_footer(text=footer_time(), icon_url=ICON)
            await embed_ch.send(embed=embed)

        await ctx.send(f"🟢 {member.mention} cooldown removed.", delete_after=5)


async def setup(bot):
    await bot.add_cog(CooldownCommands(bot))
