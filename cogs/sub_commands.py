import re 
import discord
from discord.ext import commands
from discord.ui import View
from .utils import get_player_elo
from datetime import datetime, timedelta

SUB_LOG_CHANNEL = 1437876848938848499   # قناة اللوج


# ============================
#   CANCEL VIEW
# ============================
class SubCancelView(View):
    def __init__(self, old, timeout=60):
        super().__init__(timeout=timeout)
        self.old = old
        self.canceled = False

    @discord.ui.button(label="Cancel Sub", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button):
        if interaction.user != self.old:
            return await interaction.response.send_message(
                "❌ Only the original player can cancel.",
                ephemeral=True
            )
        self.canceled = True
        self.stop()
        await interaction.response.send_message("❌ Sub canceled by original player.", ephemeral=False)



# ============================
#   MAIN SUB / REPLACE COG
# ============================
class SubCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------------------------
    # Find the match embed
    # --------------------------
    async def _find_match_message(self, channel: discord.TextChannel):
        async for msg in channel.history(limit=200):
            if msg.author == self.bot.user and msg.embeds:
                emb = msg.embeds[0]
                if emb.title and emb.title.startswith("🎮 Match"):
                    return msg, emb
        return None, None

    # ---------------------------------------------------
    # Build NEW Auto-Sub Embed without touching original
    # ---------------------------------------------------
    async def _build_sub_embed(self, original_embed, old_player, new_player):

        new_embed = discord.Embed(
            title=original_embed.title,
            color=discord.Color.orange()
        )

        if original_embed.thumbnail:
            new_embed.set_thumbnail(url=original_embed.thumbnail.url)

        # MAP FIELD
        new_embed.add_field(
            name=original_embed.fields[0].name,
            value=original_embed.fields[0].value,
            inline=False
        )

        # TEAM FIELDS
        for field in original_embed.fields[1:]:
            text = field.value

            text = text.replace(old_player.mention, new_player.mention)

            if old_player.mention in field.value:
                new_elo = get_player_elo(new_player.id)
                text = re.sub(r"``(\d+)\s*ELO``", f"``{new_elo} ELO``", text)

            elos = re.findall(r"``(\d+)\s*ELO``", text)
            avg = sum(int(x) for x in elos) // len(elos) if elos else 0

            text = re.sub(
                r"📊 \*\*Average ELO:\*\* ``\d+``",
                f"📊 **Average ELO:** ``{avg}``",
                text
            )

            new_embed.add_field(name=field.name, value=text, inline=field.inline)

        new_embed.set_footer(text="Auto-Sub Replacement Completed")
        new_embed.timestamp = discord.utils.utcnow()
        return new_embed



    # --------------------------
    # /needsub
    # --------------------------
    @commands.command()
    async def needsub(self, ctx, old_player: discord.Member):

        # Restrict channel
        if not ctx.channel.name.startswith("match"):
            return await ctx.send("❌ You can only use this command inside a match channel.")

        qv = self.bot.get_cog("QueuePanel")
        if not qv or not qv.view:
            return await ctx.send("⚠️ Queue system not active.")

        queue_view = qv.view
        if not queue_view.players:
            return await ctx.send("⚠️ No players in queue.")

        new_player = queue_view.players.pop(0)

        # CONFIRMATION
        view = SubCancelView(old_player)
        msg = await ctx.send(
            f"⏱️ {old_player.mention}, you have 1 minute to cancel the substitution for {new_player.mention}.",
            view=view
        )
        await view.wait()

        if view.canceled:
            queue_view.players.insert(0, new_player)
            return await msg.edit(
                content=f"❌ Substitution canceled by {old_player.mention}.",
                view=None
            )
        else:
            await msg.delete()

        # ==========================
        # REMOVE OLD PLAYER PERMS
        # ==========================
        await ctx.channel.set_permissions(old_player,
            view_channel=True,
            send_messages=False,
            connect=False,
            speak=False
        )

        if old_player.voice:
            try:
                await old_player.move_to(None)
            except:
                pass

        match_msg, match_embed = await self._find_match_message(ctx.channel)
        match_id = match_embed.title.split("#")[1]

        for vc in ctx.guild.voice_channels:
            if match_id in vc.name:
                await vc.set_permissions(old_player,
                    view_channel=True,
                    connect=False,
                    speak=False
                )

        # ADD NEW PLAYER PERMS
        await ctx.channel.set_permissions(new_player,
            view_channel=True,
            send_messages=True,
            connect=True,
            speak=True
        )

        sub_embed = await self._build_sub_embed(match_embed, old_player, new_player)

        final_msg = await ctx.send(
            content=f"🔄 **Auto-Sub:** {old_player.mention} ➝ {new_player.mention}",
            embed=sub_embed
        )

        # TEAM CHECK
        team_vc = None
        if new_player.mention in sub_embed.fields[1].value:
            team_vc = discord.utils.find(lambda c: "Black List" in c.name, ctx.guild.voice_channels)
        elif new_player.mention in sub_embed.fields[2].value:
            team_vc = discord.utils.find(lambda c: "Global Risk" in c.name, ctx.guild.voice_channels)

        if team_vc:
            await team_vc.set_permissions(new_player,
                view_channel=True,
                connect=True,
                speak=True
            )
            try:
                await new_player.move_to(team_vc)
            except:
                pass

        complete_msg = await ctx.send("✅ Substitution completed!")

        # DELETE COMMAND MESSAGE
        try:
            await ctx.message.delete()
        except:
            pass

        # LOG
        log_ch = ctx.guild.get_channel(SUB_LOG_CHANNEL)
        if log_ch:

            egypt = datetime.utcnow() + timedelta(hours=2)

            log_embed = discord.Embed(
                title="🔄 NeedSub Log",
                color=0x00aaff
            )
            log_embed.set_author(
                name="Premium League • Sub System",
                icon_url="https://media.discordapp.net/attachments/1433880842551296081/1440201538017689631/05ec3e25-8481-416b-8927-aaa0a66d853c.png"
            )

            log_embed.add_field(
                name="👤 Old Player",
                value=f"{old_player.mention} (`{old_player.id}`)",
                inline=False
            )

            log_embed.add_field(
                name="🆕 New Player",
                value=f"{new_player.mention} (`{new_player.id}`)",
                inline=False
            )

            log_embed.add_field(
                name="🆔 Match ID",
                value=f"``{match_id}``",
                inline=False
            )

            log_embed.set_footer(
                text=f"⭐ Premium League • {egypt.strftime('%A • %d %b %Y • %I:%M %p')}",
                icon_url="https://media.discordapp.net/attachments/1433880842551296081/1440201538017689631/05ec3e25-8481-416b-8927-aaa0a66d853c.png"
            )

            await log_ch.send(embed=log_embed)

        # UPDATE QUEUE PANEL
        if queue_view.message:
            await queue_view.message.edit(
                embed=queue_view.build_embed(),
                view=queue_view
            )



    # --------------------------
    # /replace (ADMIN)
    # --------------------------
    @commands.command()
    async def replace(self, ctx, old: discord.Member, new: discord.Member):

        is_admin = ctx.author.guild_permissions.administrator
        pug_admin = discord.utils.get(ctx.author.roles, name="PUG Admin")

        if not is_admin and not pug_admin:
            return await ctx.send("❌ You don't have permission.")

        if not ctx.channel.name.startswith("match"):
            return await ctx.send("❌ You can only use this command inside a match channel.")

        match_msg, match_embed = await self._find_match_message(ctx.channel)
        if not match_msg:
            return await ctx.send("⚠️ Match embed not found.")

        sub_embed = await self._build_sub_embed(match_embed, old, new)

        final_msg = await ctx.send(
            content=f"📢 **Admin Replacement:** {old.mention} ➝ {new.mention}",
            embed=sub_embed
        )

        # Remove old perms
        await ctx.channel.set_permissions(old,
            send_messages=False,
            connect=False,
            speak=False
        )

        if old.voice:
            try:
                await old.move_to(None)
            except:
                pass

        match_id = match_embed.title.split("#")[1]

        for vc in ctx.guild.voice_channels:
            if match_id in vc.name:
                await vc.set_permissions(old,
                    view_channel=True,
                    connect=False,
                    speak=False
                )

        await ctx.channel.set_permissions(new,
            send_messages=True,
            connect=True,
            speak=True
        )

        # Team detect
        team_vc = None
        if new.mention in sub_embed.fields[1].value:
            team_vc = discord.utils.find(lambda c: "Black List" in c.name, ctx.guild.voice_channels)
        else:
            team_vc = discord.utils.find(lambda c: "Global Risk" in c.name, ctx.guild.voice_channels)

        if team_vc:
            try:
                await team_vc.set_permissions(new,
                    view_channel=True,
                    connect=True,
                    speak=True
                )
                await new.move_to(team_vc)
            except:
                pass

        # DELETE COMMAND MESSAGE
        try:
            await ctx.message.delete()
        except:
            pass



async def setup(bot):
    await bot.add_cog(SubCommands(bot))
