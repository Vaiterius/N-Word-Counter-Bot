"""Main file

N-word Counter bot
"""
import os
import platform
import asyncio
import logging
from json import load
from pathlib import Path

import discord
from discord.ext import commands

# Fetch bot token.
TOKEN = os.environ.get("DISCORD_TOKEN")

# Me and my alt account(s).
owner_ids = (354783154126716938, 691896247052927006)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = False

bot = commands.Bot(
    command_prefix=["nibba ", "n!"],
    case_insensitive=True,
    intents=intents,
    help_command=commands.MinimalHelpCommand()
)  # https://bit.ly/3rJiM2S

# Logging.
discord.utils.setup_logging(level=logging.INFO, root=False)
logger = logging.getLogger("discord")
logger.setLevel(logging.ERROR)


async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)


@bot.event
async def on_ready():
    """Display successful startup status"""
    logger.info(f"{bot.user.name} connected!")
    logger.info(f"Using Discord.py version {discord.__version__}")
    logger.info(f"Using Python version {platform.python_version()}")
    logger.info(f"Running on {platform.system()} {platform.release()} ({os.name})")


@bot.event
async def on_command_error(ctx, error):
    logger.error(error)


@bot.command()
async def ping(ctx):
    """Pong back latency"""
    await ctx.send(f"_Pong!_ ({round(bot.latency * 1000, 1)} ms)")


@bot.command()
@commands.has_permissions(administrator=True)
async def load(context, extension):
    """(Bot dev only) Load a cog into the bot"""
    msg_success = f"File **load** of {extension}.py successful."
    msg_fail = "You do not have permission to do this"

    if context.author.id in owner_ids:
        await bot.load_extension(f"cogs.{extension}")
        logger.info(msg_success)
        await context.send(msg_success)
    else:
        await context.send(msg_fail)


@bot.command()
@commands.has_permissions(administrator=True)
async def unload(context, extension):
    """(Bot dev only) Unload a cog from the bot"""
    msg_success = f"File **unload** of {extension}.py successful."
    msg_fail = "You do not have permission to do this"

    if context.author.id in owner_ids:
        await bot.unload_extension(f"cogs.{extension}")
        logger.info(msg_success)
        await context.send(msg_success)
    else:
        await context.send(msg_fail)


@bot.command()
@commands.has_permissions(administrator=True)
async def reload(context, extension):
    """(Bot dev only) Reload a cog into the bot"""
    msg_success = f"File **reload** of {extension}.py successful."
    msg_fail = "You do not have permission to do this"

    if context.author.id in owner_ids:
        await bot.unload_extension(f"cogs.{extension}")
        await bot.load_extension(f"cogs.{extension}")
        logger.info(msg_success)
        await context.send(msg_success)
    else:
        await context.send(msg_fail)


# Load cogs into the bot.
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


asyncio.run(main())
