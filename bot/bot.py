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

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(
    intents=intents,
    debug_guilds=[867773426773262346],
    owner_ids=(354783154126716938, 691896247052927006, 234248229426823168),
)  # https://bit.ly/3rJiM2S

# Logging.
logging.basicConfig(level=logging.DEBUG)

# Load cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        try:
            bot.load_extension(f'cogs.{filename[:-3]}')
            logging.info(f'Loaded {filename[:-3]}')
        except discord.errors.ExtensionFailed as e:
            logging.error(f'Failed to load {filename[:-3]}')
            logging.error(e.with_traceback(e.__traceback__))
            # print line info
            print(e.__traceback__.tb_lineno)
            print(e.with_traceback(e.__traceback__))


@bot.event
async def on_ready():
    """Display successful startup status"""
    logging.info(f"{bot.user.name} connected!")
    logging.info(f"Using Discord.py version {discord.__version__}")
    logging.info(f"Using Python version {platform.python_version()}")
    logging.info(f"Running on {platform.system()} {platform.release()} ({os.name})")


@bot.event
async def on_command_error(ctx, error):
    logging.error(error)


@bot.slash_command(name="ping", description="Pong back latency")
async def ping(ctx):
    """Pong back latency"""
    await ctx.respond(f"_Pong!_ ({round(bot.latency * 1000, 1)} ms)", ephemeral=True, delete_after=15)


if __name__ == "__main__":
    bot.run(TOKEN, reconnect=True)
