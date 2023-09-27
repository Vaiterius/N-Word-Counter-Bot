"""Cog for storing n-word count stats and bot meta stuff"""
import discord
from discord.ext import commands
from discord import option
from utils.database import Database
from utils.paginator import paginator
from utils.discord import convert_color, generate_message_embed, generate_color
from discord.ext.pages import Paginator
from discord.ui import Button, View
import platform
import os

HEX_OG_BLURPLE = 0x7289DA


class Meta(commands.Cog):
    """Commands for bot stats and other meta stuff"""

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot

        # Get singleton database connection.
        self.db = Database()

        self.MAX_PER_PAGE = 10
        self.invite_url = "https://discord.com/oauth2/authorize?client_id=939483341684605018&permissions=412317244480" \
                          "&scope=bot"

    top = discord.SlashCommandGroup(
        name="top", description="View scoreboards for the bot")
    top_global = top.create_subgroup(
        name="global", description="View global scoreboards for the bot")
    top_guild = top.create_subgroup(
        name="guild", description="View scoreboards for the current guild")

    @top_guild.command(name="user",
                       description="View the top users in the current guild")
    @option(name="limit", description="The number of users to show", type=int,
            required=False, default=10)
    async def top_guild_user(self, ctx: discord.ApplicationContext, limit: int = 10):
        await ctx.defer()
        if limit < 10:
            await ctx.respond(embed=await generate_message_embed("Limit should be at least 10!", type="error", ctx=ctx),
                              ephemeral=True, delete_after=5)
            return
        elif limit > 100:
            await ctx.respond(
                embed=await generate_message_embed("Limit cannot exceed 100!", type="error", ctx=ctx),
                ephemeral=True, delete_after=5)
            return

        top_members = await self.db.get_member_list(ctx.guild.id)
        server_nword_total = await self.db.get_nword_server_total(ctx.guild.id)
        embed_data = {
            "title": f"Top users in {ctx.guild.name}",
            "description": f"I have seen **{server_nword_total}** n-words in this server!\n"
                           f"That's **{round(server_nword_total / await self.db.get_global_nword_count() * 100, 3)}%**"
                           f" of all n-words!",
            "url": "https://bit.ly/3JmG6cD",
            "color": HEX_OG_BLURPLE
        }
        data_vals = {"type": "rankings"}
        pages = paginator(limit, self.MAX_PER_PAGE, embed_data,
                          top_members, data_vals)
        page_iterator = Paginator(pages=pages, loop_pages=True)
        await page_iterator.respond(ctx.interaction)

    @top_global.command(name="user",
                        description="View the top users in the bot")
    @option(name="limit", description="The number of users to show", type=int,
            required=False, default=10)
    async def top_global_user(self, ctx: discord.ApplicationContext, limit: int = 10):
        await ctx.defer()
        if limit < 10:
            await ctx.respond(embed=await generate_message_embed("Limit should be at least 10!", type="error", ctx=ctx),
                              ephemeral=True, delete_after=5)
            return
        elif limit > 100:
            await ctx.respond(
                embed=await generate_message_embed("Limit cannot exceed 100!", type="error", ctx=ctx),
                ephemeral=True, delete_after=5)
            return

        top_members = await self.db.get_all_time_counts(limit)
        embed_data = {
            "title": "Top users globally",
            "description": f"I have seen the N-word used **{await self.db.get_global_nword_count():,}** times"
                           f" globally!",
            "url": "https://bit.ly/3JmG6cD",
            "color": HEX_OG_BLURPLE
        }
        data_vals = {"type": "topcounts"}
        pages = paginator(limit, self.MAX_PER_PAGE, embed_data,
                          top_members, data_vals)
        page_iterator = Paginator(pages=pages, loop_pages=True)
        await page_iterator.respond(ctx.interaction, ephemeral=True)

    @top_global.command(name="guild", description="View the top guilds.")
    @option(name="limit", description="The number of guilds to show", type=int,
            required=False, default=10)
    async def top_global_guild(self, ctx: discord.ApplicationContext, limit: int = 10):
        await ctx.defer()
        if limit < 10:
            await ctx.respond(embed=await generate_message_embed("Limit should be at least 10!", type="error", ctx=ctx),
                              ephemeral=True, delete_after=5)
            return
        elif limit > 100:
            await ctx.respond(
                embed=await generate_message_embed("Limit cannot exceed 100!", type="error", ctx=ctx),
                ephemeral=True, delete_after=5)
            return

        top_servers = await self.db.get_all_time_servers(limit)
        embed_data = {
            "title": "Top guilds globally",
            "description": f"",
            "url": "https://bit.ly/3JmG6cD",
            "color": HEX_OG_BLURPLE
        }
        data_vals = {"type": "topservers"}
        pages = paginator(limit, self.MAX_PER_PAGE, embed_data,
                          top_servers, data_vals)
        page_iterator = Paginator(pages=pages, loop_pages=True)
        await page_iterator.respond(ctx.interaction, ephemeral=True)

    @commands.slash_command(
        name="info",
        description="Get info about the bot"
    )
    async def info(self, ctx: discord.ApplicationContext):
        """Get info about the bot"""
        await ctx.defer()
        embed = discord.Embed(
            title="N-Word Counter",
            description=f"A bot that counts n-word usage in your server\nFun fact: I have seen the n-word used "
                        f"{await self.db.get_nword_server_total(ctx.guild.id)} times!",
            color=await generate_color(ctx.author.avatar.url)
        )
        embed.add_field(
            name="Invite",
            value=f"[Click here](https://discord.com/oauth2/authorize?client_id=939483341684605018&permissions"
                  f"=412317244480&scope=bot)",
            inline=True
        )
        embed.add_field(
            name="Support Server",
            value="[Click here](https://discord.gg/Q2wjkGvXMk)",
            inline=True
        )
        embed.add_field(
            name="Source Code",
            value="[GitHub](https://github.com/Vaiterius/N-Word-Counter-Bot)",
            inline=True
        )
        embed.add_field(
            name="Developers",
            value="[@vaiterius](https://discord.gg/Q2wjkGvXMk), [@bemzlabs](https://bemz.info)",
            inline=False)
        embed.add_field(
            name="Database size",
            value=f"{await self.db.get_total_documents()} document{'s' if await self.db.get_total_documents() > 1 else ''}",
            inline=False
        )
        embed.add_field(
            name="Servers",
            value=f"{len(self.bot.guilds)}",
            inline=True
        )
        embed.add_field(
            name="Users",
            value=f"{len(self.bot.users)}",
            inline=True
        )
        embed.add_field(
            name="Shards",
            value=f"{self.bot.shard_count}",
            inline=True
        )
        shard: discord.ShardInfo = self.bot.get_shard(ctx.guild.shard_id)
        shard_count: int = shard.shard_count
        shard_ping: float = round(shard.latency * 1000, 1)
        num_servers = len(
            [guild for guild in self.bot.guilds
             if guild.shard_id == ctx.guild.shard_id]
        )
        embed.add_field(
            name="Shard Info",
            value=f"Shard ID: {ctx.guild.shard_id}\n"
                  f"Shard ping: {shard_ping} ms\n"
                  f"Shard Guild count: {num_servers}\n"
                  f"Total shards: {shard_count}",
            inline=True
        )
        embed.add_field(
            name="Server Info",
            value=f"Python version: {platform.python_version()}\n"
                  f"Pycord version: {discord.__version__}\n"
                  f"Platform: {platform.platform(terse=True, aliased=True)}\n"
                  f"Node: {platform.node()}\n",
            inline=True)
        embed.set_footer(
            text=f"Command ran by {ctx.author.display_name} | {ctx.bot.user.name}",
            icon_url=ctx.author.avatar.url)
        view = View()
        view.add_item(
            Button(
                label="Invite",
                url="https://discord.com/oauth2/authorize?client_id=939483341684605018"
                "&permissions=412317244480&scope=bot",
                style=discord.ButtonStyle.link, emoji="✉️"))
        view.add_item(
            Button(
                label="Support Server",
                url="https://discord.gg/Q2wjkGvXMk",
                style=discord.ButtonStyle.link, emoji="🐛"))
        view.add_item(
            Button(
                label="Source Code",
                url="https://github.com/Vaiterius/N-Word-Counter-Bot",
                style=discord.ButtonStyle.link, emoji="🌐"))
        await ctx.respond(embed=embed, view=view, ephemeral=True, delete_after=40)


def setup(bot):
    bot.add_cog(Meta(bot))
