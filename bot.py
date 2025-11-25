import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# ====== LOAD .ENV ======
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise ValueError("❌ No DISCORD_TOKEN found in .env file!")

# ====== Intents ======
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="", intents=intents)


# ====== Load Cogs ======
async def load_extensions():
    await bot.load_extension("cogs.queue_panel")
    await bot.load_extension("cogs.score_reporter")
    await bot.load_extension("cogs.warn_commands")
    await bot.load_extension("cogs.sub_commands")
    await bot.load_extension("cogs.elo_commands")
    await bot.load_extension("cogs.cooldown_commands")
    await bot.load_extension("cogs.config_commands")
    await bot.load_extension("cogs.help_commands")
    await bot.load_extension("cogs.leaderboard")
    await bot.load_extension("cogs.profile_commands")

# ====== On Ready ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


# ====== Main Start ======
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())
