import os

import discord
import logging


class Developer(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    dev = discord.SlashCommandGroup(
        name="dev", description="Developer commands", hidden=True)

    @staticmethod
    async def __callback(
            interaction: discord.Interaction, ctx, bot, type=None):
        if interaction.user.id == ctx.author.id:
            await interaction.response.defer()
            cog = interaction.data["values"][0]
            try:
                if type == "load":
                    bot.load_extension(f"{cog}")
                elif type == "unload":
                    bot.unload_extension(f"{cog}")
                else:
                    bot.reload_extension(f"{cog}")
            except Exception as e:
                await interaction.edit_original_response(
                    content=f"Failed to {type} {cog}:\n{e}", view=None)
                logging.error(f"Failed to {type} {cog}:\n{e}")
                await interaction.delete_original_response(delay=10)
                return False
            await interaction.edit_original_response(
                content=f"{'Loaded' if type == 'load' else 'Unloaded' if type == 'unload' else 'Reloaded'} "
                        f"{cog}.py successfully.",
                view=None)
            await interaction.delete_original_response(delay=10)
            return True
        else:
            return False

    def _prepare_callback(
            self, extensions: list, ctx: discord.ApplicationContext, bot,
            type=None):
        view = discord.ui.View()
        select = discord.ui.Select(
            placeholder="Select a cog to load", options=extensions,
            min_values=1, max_values=1)
        select.callback = lambda interaction: self.__callback(
            interaction, ctx, bot, type)
        view.add_item(select)
        return view

    @dev.command(
        name="load",
        description="(Bot dev only) Load a cog into the bot")
    async def load(self, ctx):
        """(Bot dev only) Load a cog into the bot"""
        await self.bot.wait_until_ready()
        extensions = [
            discord.SelectOption(
                label=f"cogs.{cog[:-3]}",
                value=f"cogs.{cog[:-3]}")
            for cog in os.listdir("./cogs") if cog.endswith(".py")
        ]
        view = self._prepare_callback(extensions, ctx, self.bot, "load")
        await ctx.respond(view=view, ephemeral=True, delete_after=30)

    @dev.command(
        name="unload",
        description="(Bot dev only) Unload a cog from the bot")
    async def unload(self, ctx):
        """(Bot dev only) Unload a cog from the bot"""
        await self.bot.wait_until_ready()
        extensions = [
            discord.SelectOption(
                label=f"cogs.{cog[:-3]}",
                value=f"cogs.{cog[:-3]}"
            )
            for cog in os.listdir("./cogs") if cog.endswith(".py")
        ]
        view = self._prepare_callback(extensions, ctx, self.bot, "unload")
        await ctx.respond(view=view, ephemeral=True, delete_after=30)

    @dev.command(
        name="reload",
        description="(Bot dev only) Reload a cog into the bot")
    async def reload(self, ctx):
        """(Bot dev only) Reload a cog into the bot"""
        extensions = [
            discord.SelectOption(
                label=f"cogs.{cog[:-3]}",
                value=f"cogs.{cog[:-3]}"
            )
            for cog in os.listdir("./cogs") if cog.endswith(".py")
        ]
        view = self._prepare_callback(extensions, ctx, self.bot)
        await ctx.respond(view=view, ephemeral=True, delete_after=30)

    @dev.command(
        name="logs",
        description="(Bot dev only) Get the bot's most recent logs")
    async def logs(self, ctx):
        await ctx.defer()
        await ctx.respond("Logs", file=discord.File("discord.log"))



def setup(bot):
    bot.add_cog(Developer(bot))
