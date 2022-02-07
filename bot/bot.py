"""Main file

N-word Counter bot
"""
import os
from json import load
from pathlib import Path

import discord
from discord.ext import commands

# Fetch bot token.
with Path("../config.json").open() as f:
    config = load(f)

TOKEN = config["DISCORD_TOKEN"]

# Me and my alt account(s).
owner_ids = (354783154126716938, 691896247052927006)

bot = commands.Bot(
    command_prefix=["nibba ", "`"],
    case_insensitive=True,
    intents=discord.Intents.all()
)


@bot.event
async def on_ready():
    """Display successful startup status"""
    print(f"{bot.user} connected!")


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
        bot.load_extension(f"cogs.{extension}")
        print(msg_success)
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
        bot.unload_extension(f"cogs.{extension}")
        print(msg_success)
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
        bot.unload_extension(f"cogs.{extension}")
        bot.load_extension(f"cogs.{extension}")
        print(msg_success)
        await context.send(msg_success)
    else:
        await context.send(msg_fail)


# Load cogs into the bot.
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")


bot.run(TOKEN)
