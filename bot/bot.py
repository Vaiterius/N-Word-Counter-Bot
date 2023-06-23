"""Main file

N-word Counter bot
"""
import os
import platform
import logging
from json import load
from pathlib import Path

import discord
from discord.ext import commands

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

bot = commands.Bot(
    intents=intents,
    # Had to comment out because adding this disables slash commands everywhere else.
    # debug_guilds=[867773426773262346],
    owner_ids=(354783154126716938, 691896247052927006, 234248229426823168),
)

# Logging (DEBUG clogs my stdout).
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

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
    logging.info(f"{bot.user.name} connected!")
    logging.info(f"Using Discord.py version {discord.__version__}")
    logging.info(f"Using Python version {platform.python_version()}")
    logging.info(
        f"Running on {platform.system()} {platform.release()} ({os.name})")


@bot.event
async def on_command_error(ctx, error):
    logging.error(error)
    await ctx.channel.send("Sorry, an error occurred.", delete_after=5)


@bot.slash_command(name="ping", description="Pong back latency")
async def ping(ctx: discord.ApplicationContext):
    """Pong back latency"""
    await ctx.respond(
        f"_Pong!_ ({round(bot.latency * 1000, 1)} ms)",
        ephemeral=True,
        delete_after=15)


if __name__ == "__main__":
    bot.run(TOKEN, reconnect=True)
