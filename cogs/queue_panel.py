import discord 
from discord.ext import commands, tasks
from discord.ui import View, button

from .match_system import create_match_channels
from .utils import get_player_elo
from .cooldown_commands import is_suspended

QUEUE_SIZE = 2

AUTHOR_ICON = "https://media.discordapp.net/attachments/1437876851132338339/1442818666751066122/2.png?ex=6926d118&is=69257f98&hm=51d18ef4146a01b290f7a6042bf7652e12abd466e0f39640a441dd7415fa71a1&=&format=webp&quality=lossless&width=834&height=834"
THUMBNAIL_URL = AUTHOR_ICON
FOOTER_ICON = AUTHOR_ICON

# قناة اللوج برسائل الدخول والخروج
QUEUE_LOG_CHANNEL = 1437876848938848498  


# -------------------------
# Footer Time (Egypt Time)
# -------------------------
def footer_time():
    from datetime import datetime, timedelta
    egypt = datetime.utcnow() + timedelta(hours=2)
    return f"⭐ Premium League • {egypt.strftime('%A • %d %b %Y • %I:%M %p')}"


class QueueView(View):
    def __init__(self, bot, message=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.players = []
        self.message = message
        self.auto_update.start()

    # ------------ EMBED ------------
    def build_embed(self):
        embed = discord.Embed(
            title="🎮 PL NA / EU Queue",
            description="> Welcome to the queue system! Join a match and compete with other players.",
            color=discord.Color.blue()
        )

        embed.set_author(name="Premium League", icon_url=AUTHOR_ICON)
        embed.set_thumbnail(url=THUMBNAIL_URL)

        embed.add_field(
            name="📌 Queue Information",
            value=f"⏱️ Updates every 20 seconds\n👥 Current Players: **{len(self.players)}/{QUEUE_SIZE}**",
            inline=False
        )

        if self.players:
            player_list = "".join([
                f"``{i+1}.`` {p.mention} **〡** ``{get_player_elo(p.id)} ELO``\n"
                for i, p in enumerate(self.players)
            ])
        else:
            player_list = "```diff\n- No players in queue. Be the first to join!\n```"

        embed.add_field(name="👤 Player List", value=player_list, inline=False)
        embed.set_footer(text=footer_time(), icon_url=FOOTER_ICON)
        return embed

    # ============================
    #        JOIN BUTTON
    # ============================
    @button(label="Join", style=discord.ButtonStyle.green, emoji="🟢")
    async def join(self, interaction: discord.Interaction, btn):

        # ===== ROLE CHECK =====
        required_role = discord.utils.get(interaction.guild.roles, name="PUG Approved")
        if required_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ You do not have the required role to join the queue.",
                ephemeral=True
            )

        # ====== COOL DOWN CHECK ======
        if is_suspended(interaction.user.id):
            return await interaction.response.send_message(
                "❌ You are currently in **COOL DOWN**.\n"
                "**⛔ You cannot join the queue.**",
                ephemeral=True
            )

        if interaction.user in self.players:
            return await interaction.response.send_message("❌ You are already in the queue!", ephemeral=True)

        if len(self.players) >= QUEUE_SIZE:
            return await interaction.response.send_message("⚠️ The queue is full!", ephemeral=True)

        self.players.append(interaction.user)

        await interaction.response.send_message(
            f"✅ {interaction.user.mention} joined the queue!",
            ephemeral=True
        )

        await self.send_log(interaction.user, joined=True)

        if self.message:
            await self.message.edit(embed=self.build_embed(), view=self)

        if len(self.players) >= QUEUE_SIZE:
            await create_match_channels(interaction.guild, self.players)
            self.players.clear()
            if self.message:
                await self.message.edit(embed=self.build_embed(), view=self)

    # ============================
    #        LEAVE BUTTON
    # ============================
    @button(label="Leave", style=discord.ButtonStyle.red, emoji="🔴")
    async def leave(self, interaction: discord.Interaction, btn):
        if interaction.user not in self.players:
            return await interaction.response.send_message("❌ You are not in the queue!", ephemeral=True)

        self.players.remove(interaction.user)
        await interaction.response.send_message("✅ You left the queue.", ephemeral=True)

        await self.send_log(interaction.user, joined=False)

        if self.message:
            await self.message.edit(embed=self.build_embed(), view=self)

    # ============================
    #      AUTO UPDATE LOOP
    # ============================
    @tasks.loop(seconds=20)
    async def auto_update(self):
        if self.message:
            await self.message.edit(embed=self.build_embed(), view=self)

    # ============================
    #      SEND LOG FUNCTION
    # ============================
    async def send_log(self, user, joined: bool):
        log_ch = self.bot.get_channel(QUEUE_LOG_CHANNEL)
        if not log_ch:
            return

        status = "🟢 Joined Queue" if joined else "🔴 Left Queue"
        color = 0x00ff00 if joined else 0xff0000

        embed = discord.Embed(
            title=status,
            color=color
        )

        embed.set_author(name="Premium League • Queue Log", icon_url=AUTHOR_ICON)
        embed.set_thumbnail(url=AUTHOR_ICON)

        embed.add_field(
            name="👤 Player",
            value=f"{user.mention} (`{user.id}`)",
            inline=False
        )

        embed.add_field(
            name="🎮 Action",
            value="Joined the Queue" if joined else "Left the Queue",
            inline=False
        )

        embed.add_field(
            name="📊 Current ELO",
            value=f"```fix\n{get_player_elo(user.id)}\n```",
            inline=False
        )

        embed.set_footer(text=footer_time(), icon_url=AUTHOR_ICON)

        await log_ch.send(embed=embed)



# ==========================================
#        QUEUE PANEL COMMAND + NEW CMDS
# ==========================================
class QueuePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.view = None

    @commands.command()
    async def queuepanel(self, ctx):
        view = QueueView(self.bot)
        embed = view.build_embed()

        msg = await ctx.send(embed=embed, view=view)
        view.message = msg
        self.view = view

    # ============================
    #        RESET QUEUE
    # ============================
    @commands.command()
    async def resetqueue(self, ctx):

        is_admin = ctx.author.guild_permissions.administrator
        pug_admin = discord.utils.get(ctx.author.roles, name="PUG Admin")

        if not is_admin and not pug_admin:
            return await ctx.send("❌ You don’t have permission.", delete_after=5)

        if not self.view:
            return await ctx.send("⚠️ Queue panel is not active.", delete_after=5)

        self.view.players.clear()

        if self.view.message:
            await self.view.message.edit(embed=self.view.build_embed(), view=self.view)

        await ctx.send("♻️ **Queue has been reset.**", delete_after=5)

    # ============================
    #       RESTART QUEUE
    # ============================
    @commands.command()
    async def restartqueue(self, ctx):

        is_admin = ctx.author.guild_permissions.administrator
        pug_admin = discord.utils.get(ctx.author.roles, name="PUG Admin")

        if not is_admin and not pug_admin:
            return await ctx.send("❌ You don’t have permission.", delete_after=5)

        new_view = QueueView(self.bot)
        new_embed = new_view.build_embed()

        msg = await ctx.send("🔄 **Queue restarted successfully!**", embed=new_embed, view=new_view)

        new_view.message = msg
        self.view = new_view



async def setup(bot):
    await bot.add_cog(QueuePanel(bot))
