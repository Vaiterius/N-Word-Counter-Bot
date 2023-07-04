"""Main file

N-word Counter bot
"""
import os
import platform
import logging
import random
from json import load
from pathlib import Path

import discord
from discord.ext import commands, tasks

# Fetch bot token.
with Path("../config.json").open() as f:
    config = load(f)

TOKEN = config["DISCORD_TOKEN"]

# DO NOT TOUCH - for running on hosting platform.
if TOKEN == "":
    TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = False

bot = commands.AutoShardedBot(
    # shard_count=5, remove to automatically calculate depending on guild count.
    intents=intents,
    owner_ids=(354783154126716938, 691896247052927006, 234248229426823168)
)

# Logging (DEBUG clogs my stdout).
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter(
    "%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

# Load cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        try:
            bot.load_extension(f'cogs.{filename[:-3]}')
            logging.info(f'Loaded {filename[:-3]}')
        except discord.errors.ExtensionFailed as e:
            logging.error(f'Failed to load {filename[:-3]}')
            logging.error(e.with_traceback(e.__traceback__))


@bot.event
async def on_ready():
    """Display successful startup status"""
    logger.info(f"{bot.user.name} connected!")
    logger.info(f"Using Discord.py version {discord.__version__}")
    logger.info(f"Using Python version {platform.python_version()}")
    logger.info(
        f"Running on {platform.system()} {platform.release()} ({os.name})")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"over your messages"))
    # status_loop.start()


@bot.slash_command(name="ping", description="Pong back latency")
async def ping(ctx: discord.ApplicationContext):
    """Pong back latency"""
    await bot.wait_until_ready()
    await ctx.respond(
        f"_Pong!_ ({round(bot.latency * 1000, 1)} ms)",
        ephemeral=True,
        delete_after=15)

# Removed for now, possible reason for rate limit.
# @tasks.loop(seconds=30)
# async def status_loop():
#     """This loop runs every 30 seconds and changes the bot's status"""
#     await bot.wait_until_ready()
#     status = random.randint(1, 4)
#     if status == 1:
#         await bot.change_presence(
#             activity=discord.Activity(type=discord.ActivityType.watching, name=f"over {len(bot.guilds)} servers"))
#     elif status == 2:
#         await bot.change_presence(activity=discord.Game(name=f"with {random.choice(bot.guilds).name}"))
#     elif status == 3:
#         await bot.change_presence(
#             activity=discord.Activity(type=discord.ActivityType.listening, name=f" your messages"))
#     elif status == 4:
#        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=" your language"))


if __name__ == "__main__":
    bot.run(TOKEN, reconnect=True)
