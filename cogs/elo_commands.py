import discord
from discord.ext import commands
from datetime import datetime, timedelta
from .utils import load_json, save_json
from .config import PLAYER_DATA_FILE, ELO_CHANNEL_ID, ELO_LOG_CHANNEL_ID

ELO_FILE = PLAYER_DATA_FILE

ICON = "https://media.discordapp.net/attachments/1437876851132338339/1442818666751066122/2.png?ex=6926d118&is=69257f98&hm=51d18ef4146a01b290f7a6042bf7652e12abd466e0f39640a441dd7415fa71a1&=&format=webp&quality=lossless&width=834&height=834"


# -------------------------------
#  FOOTER TIME — Egypt 🇪🇬
# -------------------------------
def footer_time():
    egypt = datetime.utcnow() + timedelta(hours=2)
    return f"⭐ Premium League • {egypt.strftime('%A • %d %b %Y • %I:%M %p')}"


def get_elo(user_id: int):
    data = load_json(ELO_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"elo": 0}
        save_json(ELO_FILE, data)
    return data[uid]["elo"]


def set_elo(user_id: int, new_elo: int):
    data = load_json(ELO_FILE)
    uid = str(user_id)
    data.setdefault(uid, {})
    data[uid]["elo"] = new_elo
    save_json(ELO_FILE, data)


# ============================
#       ELO COMMANDS
# ============================

class ELOCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----- ROLE CHECK -----
    def has_elo_permission(self, ctx):
        allowed_roles = ["PL Admin", "PUG Admin"]
        return any(r.name in allowed_roles for r in ctx.author.roles)

    # ----- CHANNEL CHECK -----
    async def cog_check(self, ctx):
        if ctx.channel.id != ELO_CHANNEL_ID:
            await ctx.send("❌ You can use ELO commands only in **🎖️・ᴇʟᴏ-ᴠɪᴄᴛᴏʀʏ**.", delete_after=5)
            return False
        return True

    # ----- EMBED BUILDER -----
    def build_embed(self, title, admin, member, amount, old_elo, new_elo, color):

        embed = discord.Embed(title=title, color=color)
        embed.set_author(name="⭐ Premium League Monitoring System", icon_url=ICON)
        embed.set_thumbnail(url=ICON)

        embed.add_field(name="👑 Administrator", value=f"{admin.mention} (`{admin.id}`)", inline=False)
        embed.add_field(name="👤 Member", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="📊 ELO Change", value=f"```fix\n{amount}\n```", inline=False)
        embed.add_field(name="📉 Old ELO", value=f"```fix\n{old_elo}\n```", inline=True)
        embed.add_field(name="📈 New ELO", value=f"```fix\n{new_elo}\n```", inline=True)

        embed.set_footer(text=footer_time(), icon_url=ICON)

        return embed

    # ============================
    #          SEND ELO
    # ============================
    @commands.command()
    async def sendelo(self, ctx, member: discord.Member, amount: int):

        if not self.has_elo_permission(ctx):
            return await ctx.send("❌ You don't have permission to use **ELO commands**.", delete_after=5)

        try:
            await ctx.message.delete()
        except:
            pass

        old_elo = get_elo(member.id)
        new_elo = old_elo + amount
        set_elo(member.id, new_elo)

        # ---- NORMAL MESSAGE ----
        msg = (
            f"{ctx.author.mention} **Send `{amount}` ELO**\n"
            f"- ** `#` Player:** {member.mention} (`{member.id}`)\n"
            f"- **Old ELO:** `{old_elo}`\n"
            f"- **New ELO:** `{new_elo}`"
        )
        await ctx.send(msg)

        # ---- LOG EMBED ----
        embed = self.build_embed(
            title="📈 ELO SENT 🔱",
            admin=ctx.author,
            member=member,
            amount=amount,
            old_elo=old_elo,
            new_elo=new_elo,
            color=0x00ff6a
        )

        log_ch = self.bot.get_channel(ELO_LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(embed=embed)

    # ============================
    #          TAKE ELO
    # ============================
    @commands.command()
    async def takeelo(self, ctx, member: discord.Member, amount: int):

        if not self.has_elo_permission(ctx):
            return await ctx.send("❌ You don't have permission to use **ELO commands**.", delete_after=5)

        try:
            await ctx.message.delete()
        except:
            pass

        old_elo = get_elo(member.id)
        new_elo = max(0, old_elo - amount)
        set_elo(member.id, new_elo)

        # ---- NORMAL MESSAGE ----
        msg = (
            f"{ctx.author.mention} **Take `{amount}` ELO**\n"
            f"- ** `#` Player:** {member.mention} (`{member.id}`)\n"
            f"- **Old ELO:** `{old_elo}`\n"
            f"- **New ELO:** `{new_elo}`"
        )
        await ctx.send(msg)

        # ---- LOG EMBED ----
        embed = self.build_embed(
            title="📉 ELO TAKEN 🛑",
            admin=ctx.author,
            member=member,
            amount=amount,
            old_elo=old_elo,
            new_elo=new_elo,
            color=0xff3838
        )

        log_ch = self.bot.get_channel(ELO_LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(embed=embed)

    # ============================
    #          SET ELO
    # ============================
    @commands.command()
    async def setelo(self, ctx, member: discord.Member, amount: int):

        if not self.has_elo_permission(ctx):
            return await ctx.send("❌ You don't have permission to use **ELO commands**.", delete_after=5)

        try:
            await ctx.message.delete()
        except:
            pass

        old_elo = get_elo(member.id)
        set_elo(member.id, amount)

        # ---- NORMAL MESSAGE ----
        msg = (
            f"{ctx.author.mention} **set ELO manually**\n"
            f"- ** `#` Player:** {member.mention} (`{member.id}`)\n"
            f"- **Old ELO:** `{old_elo}`\n"
            f"- **New ELO:** `{amount}`"
        )
        await ctx.send(msg)

        # ---- LOG EMBED ----
        embed = self.build_embed(
            title="⚙️ MANUAL ELO SETTING",
            admin=ctx.author,
            member=member,
            amount=amount,
            old_elo=old_elo,
            new_elo=amount,
            color=0xffa500
        )

        log_ch = self.bot.get_channel(ELO_LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ELOCommands(bot))
