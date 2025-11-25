import discord
import random
import math
from collections import defaultdict
from discord.ext import commands
from .utils import (
    load_match_id,
    save_match_id,
    average_elo_from_members,
    get_player_elo
)

# constants
MATCH_CATEGORY_ID = 1437876849534435375

# maps dict
MAPS = {
    "Sub Base": "https://media.discordapp.net/attachments/1389250798554185858/1397646134398423134/180.png",
    "Black Widow": "https://media.discordapp.net/attachments/1389250798554185858/1397645580758421555/180.png",
    "Mexico": "https://media.discordapp.net/attachments/1389250798554185858/1397645715420745911/180.png",
    "Ankara": "https://media.discordapp.net/attachments/1389250798554185858/1397646443266703492/180.png",
    "Port": "https://media.discordapp.net/attachments/1389250798554185858/1397646278900449501/180.png",
    "Compound": "https://media.discordapp.net/attachments/1389250798554185858/1397650442330312807/200.png",
    "EAGLE EYE 2.0": "https://media.discordapp.net/attachments/1389250798554185858/1397645943935074425/180.png",
}

# votes storage
map_votes_by_channel = defaultdict(lambda: defaultdict(list))


# ---------------------------
#   REBUILD MATCH EMBED
# ---------------------------
def build_match_embed(match_id, team_black, team_global, selected_map):
    avg_black = average_elo_from_members(team_black)
    avg_global = average_elo_from_members(team_global)

    embed = discord.Embed(
        title=f"🎮 Match #{match_id}",
        color=discord.Color.blue()
    )

    embed.add_field(name="🗺️ Map Selected :", value=selected_map, inline=False)

    embed.add_field(
        name="🔴 Team Black List",
        value="\n".join([
            f"`{i+1}.` {p.mention} ``{get_player_elo(p.id)} ELO``"
            for i, p in enumerate(team_black)
        ]) + f"\n\n📊 **Average ELO:** ``{avg_black}``",
        inline=True
    )

    embed.add_field(
        name="🔵 Team Global Risk",
        value="\n".join([
            f"`{i+1}.` {p.mention} ``{get_player_elo(p.id)} ELO``"
            for i, p in enumerate(team_global)
        ]) + f"\n\n📊 **Average ELO:** ``{avg_global}``",
        inline=True
    )

    embed.add_field(
        name="🛠️ Need a Sub?",
        value="Players: `.needsub @player`\nAdmins: `.replace @out @in`",
        inline=False
    )

    embed.set_thumbnail(url=MAPS[selected_map])
    embed.timestamp = discord.utils.utcnow()
    return embed


# ---------------------------
#   MAP SELECT MENU UI
# ---------------------------
class MapSelect(discord.ui.Select):
    def __init__(self, embed_message, embed, maps_dict, text_channel, team_black, team_global):
        self.embed_message = embed_message
        self.embed = embed
        self.maps = maps_dict
        self.text_channel = text_channel

        self.team_black = team_black
        self.team_global = team_global
        self.match_players = team_black + team_global

        total_players = len(self.match_players)
        self.required_votes = max(1, math.ceil(total_players * 0.7))

        options = [
            discord.SelectOption(
                label=name,
                description=f"Vote to change map to {name}",
            )
            for name in maps_dict.keys()
        ]

        super().__init__(
            placeholder="🗺️ Change Map",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user

        if user.id not in [p.id for p in self.match_players]:
            return await interaction.response.send_message(
                "❌ You are not a player in this match.",
                ephemeral=True
            )

        await interaction.response.defer()

        map_name = self.values[0]
        channel_id = self.text_channel.id
        votes_for_channel = map_votes_by_channel[channel_id]

        # Remove previous vote
        for users in votes_for_channel.values():
            if user.id in users:
                users.remove(user.id)

        # Add vote
        votes_for_channel[map_name].append(user.id)
        current_votes = len(votes_for_channel[map_name])

        await self.text_channel.send(
            f"**{user.mention} voted for `{map_name}` — {current_votes}/{self.required_votes}**"
        )

        # ---- End vote ----
        if current_votes >= self.required_votes:

            try:
                self.view.clear_items()
            except:
                pass

            # CREATE NEW EMBED (no edit to original)
            final_embed = discord.Embed(
                title="🗺️ Final Map Selected!",
                description=f"**New Map:** `{map_name}`",
                color=discord.Color.green()
            )
            final_embed.set_thumbnail(url=self.maps[map_name])
            final_embed.set_footer(text="Map vote completed")
            final_embed.timestamp = discord.utils.utcnow()

            await self.text_channel.send(embed=final_embed)

            await self.text_channel.send(f"🎉 **Final map selected: `{map_name}`**")



# ---------------------------
#   MATCH VIEW
# ---------------------------
class MatchView(discord.ui.View):
    def __init__(self, embed_message, embed, team_black, team_global, maps_dict, text_channel):
        super().__init__(timeout=None)
        self.add_item(
            MapSelect(
                embed_message,
                embed,
                maps_dict,
                text_channel,
                team_black,
                team_global
            )
        )


# ---------------------------
#   CREATE MATCH CHANNELS
# ---------------------------
async def create_match_channels(guild: discord.Guild, players: list):

    last = load_match_id() + 1
    save_match_id(last)
    match_id = last

    category = guild.get_channel(MATCH_CATEGORY_ID)

    wolf_role = discord.utils.get(guild.roles, name="PUG Approved")
    if wolf_role is None:
        wolf_role = await guild.create_role(name="PUG Approved")

    spectator_role = discord.utils.get(guild.roles, name="Spectator")
    if spectator_role is None:
        spectator_role = await guild.create_role(name="Spectator", permissions=discord.Permissions.none())

    score_reporter_role = discord.utils.get(guild.roles, name="Score Reporter")
    if score_reporter_role is None:
        score_reporter_role = await guild.create_role(
            name="Score Reporter",
            permissions=discord.Permissions(view_channel=True, send_messages=True)
        )

    overwrites_match_text = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
        wolf_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
        spectator_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
        score_reporter_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    for p in players:
        overwrites_match_text[p] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    text_channel = await guild.create_text_channel(
        name=f"match〡{match_id}〡approved",
        category=category,
        overwrites=overwrites_match_text
    )

    random.shuffle(players)
    half = len(players) // 2
    team_black = players[:half]
    team_global = players[half:]

    # voice permissions
    def base_voice_overwrites():
        return {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False),
            spectator_role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=False)
        }

    overwrites_black = base_voice_overwrites()
    overwrites_global = base_voice_overwrites()

    for p in team_black:
        overwrites_black[p] = discord.PermissionOverwrite(connect=True, speak=True)

    for p in team_global:
        overwrites_global[p] = discord.PermissionOverwrite(connect=True, speak=True)

    await guild.create_voice_channel(
        name=f"🟠 Approved〡{match_id}〡Black List",
        category=category,
        overwrites=overwrites_black,
        user_limit=7
    )

    await guild.create_voice_channel(
        name=f"🔵 Approved〡{match_id}〡Global Risk",
        category=category,
        overwrites=overwrites_global,
        user_limit=7
    )

    selected_map = random.choice(list(MAPS.keys()))
    embed = build_match_embed(match_id, team_black, team_global, selected_map)

    msg = await text_channel.send(
        content="**Your match is ready!** " + " ".join([p.mention for p in players]),
        embed=embed
    )

    view = MatchView(msg, embed, team_black, team_global, MAPS, text_channel)
    await msg.edit(view=view)

    map_votes_by_channel[text_channel.id] = defaultdict(list)

    return match_id


# ---------------- TEST COG ----------------
class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def startmatch(self, ctx):
        players = [m for m in ctx.guild.members if not m.bot][:10]
        if len(players) < 2:
            return await ctx.send("❌ Not enough players.")

        match_id = await create_match_channels(ctx.guild, players)
        await ctx.send(f"✅ Match created #{match_id}")


async def setup(bot):
    await bot.add_cog(MatchCommands(bot))
