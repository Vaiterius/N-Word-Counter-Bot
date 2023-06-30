"""Cog for storing n-word count stats and bot meta stuff"""
import discord
from discord.ext import commands
from discord import option
from utils.database import Database
from utils.paginator import paginator
from utils.discord import convert_color, generate_message_embed
from discord.ext.pages import Paginator
from discord.ui import Button, View

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

    @commands.slash_command(
        name="shardinfo",
        description="Get info about this guild's belonging shard"
    )
    async def shardinfo(self, ctx: discord.ApplicationContext):
        """Get info about this guild's belonging shard"""
        await ctx.defer()

        shard_id: int = ctx.guild.shard_id
        shard: discord.ShardInfo = self.bot.get_shard(shard_id)
        shard_count: int = shard.shard_count
        shard_ping: float = round(shard.latency * 1000, 1)
        num_servers = len(
            [guild for guild in self.bot.guilds
             if guild.shard_id == shard_id]
        )

        text: str = f"__Shard Info for this server__\n" \
                    f"**Shard ID:** {shard_id}\n" \
                    f"**Total shards:** {shard_count}\n" \
                    f"**Shard ping:** {shard_ping} ms\n" \
            f"**Total servers in this shard:** {num_servers}"

        await ctx.respond(embed=generate_message_embed(
            text=text,
            type="info",
            ctx=ctx),
            ephemeral=True, delete_after=20)

    @commands.slash_command(
        name="servercount",
        description="Return server accumulated nword count")
    async def servercount(self, ctx):
        """Return server accumulated nword count"""
        await ctx.defer()
        # Database, not client, should handle summing as a large member
        # count would put great strain.
        sum: int = self.db.get_nword_server_total(ctx.guild.id)
        await ctx.respond(embed=generate_message_embed(
            f"*Since bot join*, there have been a total of **{sum:,}** "
            "n-words said in this server", type="info", ctx=ctx), ephemeral=True, delete_after=20)

    @commands.slash_command(
        name="totalservers",
        description="Return total number of servers the bot is in")
    async def totalservers(self, ctx):
        """Return total number of servers the bot is in"""
        await ctx.defer()
        view = View()
        button = Button(label="Invite", url=self.invite_url,
                        style=discord.ButtonStyle.link, emoji="🔗")
        view.add_item(button)
        await ctx.respond(embed=generate_message_embed(
            f"I am in **{len(self.bot.guilds)}** servers,"
            f"add your server by clicking the invite button!", type="info", ctx=ctx), ephemeral=True, delete_after=20,
            view=view)

    @commands.slash_command(
        name="invite",
        description="Invite the bot to your server")
    async def invite(self, ctx):
        """Invite the bot to your server"""
        await ctx.defer()
        view = View()
        button = Button(label="Invite", url=self.invite_url,
                        style=discord.ButtonStyle.link, emoji="🔗")
        view.add_item(button)
        await ctx.respond(embed=generate_message_embed(
            f"Click the invite button to invite me to your server!", type="info", ctx=ctx), ephemeral=True,
            view=view)

    @commands.slash_command(
        name="totaldocs",
        description="Return total number of documents in database")
    async def totaldocs(self, ctx):
        """Return total number of documents in database"""
        await ctx.defer()
        await ctx.respond(embed=generate_message_embed(
            f"There are **{self.db.get_total_documents()}** total MongoDB documents", type="info", ctx=ctx),
            ephemeral=True, delete_after=20)

    @commands.slash_command(
        name="topservers",
        description="Show a list of global top servers by n-word count")
    @option(
        name="limit",
        description="Number of servers shown, limited to 10-100", type=int,
        required=False)
    async def topservers(self, ctx, limit: int = 50):
        """Show a list of global top servers by n-word count.
        May also specify number of servers shown, limited to 10-100
        e.g. *n!topservers 50*
        """
        await ctx.defer()
        if limit < 10:
            await ctx.respond(embed=generate_message_embed("Limit should be at least 10!", type="error", ctx=ctx),
                              ephemeral=True, delete_after=5)
            return
        elif limit > 100:
            await ctx.respond(
                embed=generate_message_embed("Limit cannot exceed 100!", type="error", ctx=ctx),
                ephemeral=True, delete_after=5)
            return

        top_servers = self.db.get_all_time_servers(limit)
        embed_data = {
            "title": "All-time Server N-word Counts",
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
        name="topcounts",
        description="Show a list of global top users by n-word count")
    @option(
        name="limit",
        description="Number of users shown, limited to 10-100", type=int,
        required=False)
    async def topcounts(self, ctx, limit: int = 50):
        """Show a list of global top users by n-word count.
        May also specify number of users shown, limited to 10-100
        e.g. *n!topcounts 50*
        """
        await ctx.defer()
        if limit < 10:
            await ctx.respond(embed=generate_message_embed("Limit should be at least 10!", type="error", ctx=ctx),
                              ephemeral=True, delete_after=5)
            return
        elif limit > 100:
            await ctx.respond(
                embed=generate_message_embed("Limit cannot exceed 100!", type="error", ctx=ctx),
                ephemeral=True, delete_after=5)
            return

        top_members = self.db.get_all_time_counts(limit)
        embed_data = {
            "title": "All-time User N-word Counts",
            "description": f"",
            "url": "https://bit.ly/3JmG6cD",
            "color": HEX_OG_BLURPLE
        }
        data_vals = {"type": "topcounts"}
        pages = paginator(limit, self.MAX_PER_PAGE, embed_data,
                          top_members, data_vals)
        page_iterator = Paginator(pages=pages, loop_pages=True)
        await page_iterator.respond(ctx.interaction, ephemeral=True)

    @commands.slash_command(
        name="rankings",
        description="Show a list of top users in this server by n-word count")
    @option(
        name="limit",
        description="Number of users shown, limited to 10-100", type=int,
        required=False)
    async def rankings(self, ctx, limit: int = 50):
        """Show a list of top users in this server by n-word count.
        May also specify number of users shown, limited to 10-100
        e.g. *n!rankings 50*
        """
        await ctx.defer()
        if limit < 10:
            await ctx.respond(embed=generate_message_embed("Limit should be at least 10!", type="error", ctx=ctx),
                              ephemeral=True, delete_after=5)
            return
        elif limit > 100:
            await ctx.respond(
                embed=generate_message_embed("Limit cannot exceed 100!", type="error", ctx=ctx),
                ephemeral=True, delete_after=5)
            return

        top_members = self.db.get_member_list(ctx.guild.id)
        server_nword_total = self.db.get_nword_server_total(ctx.guild.id)
        embed_data = {
            "title": f"Server N-word Count Rankings",
            "description": f"Total n-words: **{server_nword_total}**\n \
                _* next to name is verified black_\n \
                *~ has an n-word pass*",
            "url": "https://bit.ly/3JmG6cD",
            "color": HEX_OG_BLURPLE
        }
        data_vals = {"type": "rankings"}
        pages = paginator(limit, self.MAX_PER_PAGE, embed_data,
                          top_members, data_vals)
        page_iterator = Paginator(pages=pages, loop_pages=True)
        await page_iterator.respond(ctx.interaction, ephemeral=True)


def setup(bot):
    bot.add_cog(Meta(bot))
