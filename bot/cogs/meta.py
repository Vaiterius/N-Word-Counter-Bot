"""Cog for storing n-word count stats and bot meta stuff"""
from discord.ext import commands
from discord import option
from utils.database import Database
from utils.paginator import paginator
from discord.ext.pages import Paginator

HEX_OG_BLURPLE = 0x7289DA


class Meta(commands.Cog):
    """Commands for bot stats and other meta stuff"""

    def __init__(self, bot):
        self.bot = bot

        # Get singleton database connection.
        self.db = Database()

        self.MAX_PER_PAGE = 10

    @commands.slash_command(name="servercount", description="Return server accumulated nword count")
    async def servercount(self, ctx):
        """Return server accumulated nword count"""
        # Database, not client, should handle summing as a large member count would put great strain.
        sum: int = self.db.get_nword_server_total(ctx.guild.id)
        await ctx.respond(f"(since bot join)\nThere have been a total of `{sum:,}` n-words said in this server")

    @commands.slash_command(name="totalservers", description="Return total number of servers the bot is in")
    async def totalservers(self, ctx):
        """Return total number of servers the bot is in"""
        await ctx.respond(f"I am in **{len(self.bot.guilds)}** servers")

    @commands.slash_command(name="totaldocs", description="Return total number of documents in database")
    async def totaldocs(self, ctx):
        """Return total number of documents in database"""
        await ctx.respond(f"**{self.db.get_total_documents()}** total MongoDB documents")

    @commands.slash_command(name="topservers", description="Show a list of global top servers by n-word count")
    @option(name="limit", description="Number of servers shown, limited to 10-100", type=int, required=False)
    async def topservers(self, ctx, limit: int = 10):
        """Show a list of global top servers by n-word count.
        May also specify number of servers shown, limited to 10-100
        e.g. *n!topservers 50*
        """
        if limit < 10:
            await ctx.respond("Limit number should be at least 10!")
            return
        elif limit > 100:
            await ctx.respond("Can only show top 100 servers")
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
        await page_iterator.respond(ctx.interaction)

    @commands.slash_command(name="topcounts", description="Show a list of global top users by n-word count")
    @option(name="limit", description="Number of users shown, limited to 10-100", type=int, required=False)
    async def topcounts(self, ctx, limit: int = 10):
        """Show a list of global top users by n-word count.
        May also specify number of users shown, limited to 10-100
        e.g. *n!topcounts 50*
        """
        if limit < 10:
            await ctx.respond("Limit number should be at least 10!")
            return
        elif limit > 100:
            await ctx.respond("Can only show top 100 users")
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
        await page_iterator.respond(ctx.interaction)

    @commands.slash_command(name="rankings", description="Show a list of top users in this server by n-word count")
    @option(name="limit", description="Number of users shown, limited to 10-100", type=int, required=False)
    async def rankings(self, ctx, limit: int = 10):
        """Show a list of top users in this server by n-word count.
        May also specify number of users shown, limited to 10-100
        e.g. *n!rankings 50*
        """
        if limit < 10:
            await ctx.respond("Limit number should be at least 10!")
            return
        elif limit > 100:
            await ctx.respond("Can only show top 100 users")
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
        await page_iterator.respond(ctx.interaction)


def setup(bot):
    bot.add_cog(Meta(bot))
