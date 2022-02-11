"""Cog for n-word counting and storing logic"""
import string
from json import load
from pathlib import Path

import pymongo
from discord.ext import commands

# Fetch MongoDB token for database access.
with Path("../config.json").open() as f:
    config = load(f)
    mongo_url = config["MONGO_URL"]


class NWordCounter(commands.Cog):
    """Category for n-word occurrences
    
    TODO (✔️) (❌)
    ❌ complete database functionality
    ✔️ complete count_nwords unittest
    ❌ comlpete pymongo unittest
    ❌ implement server total n-words lookup command
    ❌ implement voting system
    ❌ implement single user n-word lookup
    ❌ implement bigger table for count_nword translate method
    ❌ implement new cluster solely for member votes
    """

    def __init__(self, bot):
        self.bot = bot

        # Initialize Mongo database.
        self.cluster = pymongo.MongoClient(mongo_url)
        self.db = self.cluster["NWordCounter"]
        self.collection = self.db["guild_users_db"]
    

    @staticmethod
    def count_nwords(msg: str) -> int:
        """Return occurrences of n-words in a given message"""
        count = 0
        msg = msg.lower().strip().translate(  # Cleanse all whitespaces.
            {ord(char): "" for char in string.whitespace}
        )

        n_words = ["nigga", "nigger"]  # Don't cancel me for typing this.
        for word in n_words:
            count += msg.count(word)

        return count
    

    def guild_in_database(self, guild) -> bool:
        """Return True if guild is already recorded in database"""
        return self.collection.count_documents(
            {"guild_id": guild.id}
        ) != 0
    

    def create_database(self, guild) -> None:
        """Initialize guild template in database"""
        self.collection.insert_one(
            {
                "guild_id": guild.id,
                "guild_name": guild.name,
                "members": []
            }
        )
    

    def member_in_database(self, guild, member) -> bool:
        """Return True if member is already recorded in guild database"""
        # Query a member from specific guild.
        find_member_cursor = self.collection.aggregate(
            [
                {
                    "$match": {
                        "guild_id": guild.id,
                        "members.id": member.id
                    }
                },
                {"$unwind": "$members"},
                {
                    "$match": {
                        "members.id": member.id
                    }
                },
                {"$replaceWith": "$members"}
            ]
        )
        return len(list(find_member_cursor)) != 0
    

    def create_member(self, guild, member) -> None:
        """Initialize member data in guild database"""
        self.collection.update_one(
            {"guild_id": guild.id}, {
                "$push": {
                    "members": {
                        "id": member.id,
                        "name": member.name,
                        "nword_count": 0,
                        "is_black": False,
                    }
                }
            }
        )
    

    def increment_nword_count(self, guild, member, count):
        """Add to n-word count of person's data info in server"""
        self.collection.update_one(
            {
                "guild_id": guild.id,
                "members.id": member.id
            },
            {
                "$inc": {
                    "members.$.nword_count": count
                }
            },
            upsert=False  # Don't create new document if not found.
        )
    

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect n-words"""
        if message.author == self.bot.user:
            return
        
        guild = message.guild
        msg = message.content
        author = message.author  # Should fetch user by ID instead of name.

        # Ensure guild has its own place in the database.
        if not self.guild_in_database(guild):
            self.create_database(guild)
        
        # Bot reaction to any n-word occurrence.
        num_nwords = self.count_nwords(msg)
        if num_nwords > 0:

            if not self.member_in_database(guild, author):
                self.create_member(guild, author)
            
            self.increment_nword_count(guild, author, num_nwords)

            await message.reply(
                f":camera_with_flash: Detected **{num_nwords}** n-words!"
            )
    

    @commands.command()
    async def testview(self, ctx, *, bruh):
        pass


    @commands.command()
    async def count(self, ctx, mention):
        """Return total nword count of a person in a server"""
        member_id = mention.id
        # If person is not found in server, abort.
        # if self.member_in_database(ctx.guild, mention)
        # Else return embedded formatted number.
        pass
    

    @commands.command()
    async def servercount(self, ctx):
        """Return server accumulated nword count"""
        pass


    @commands.command()
    async def vote(self, ctx, mention):
        """Vouch for someone being black and thus can say the n-word"""
        pass


    # @commands.command()
    # async def unvote(self, ctx, mention):
    #     """Attempt to remove a vouch for a person"""
    #     if not self.user_voted_for(ctx.author.id, mention):
    #         await ctx.reply("You did not vote for this person!")
    #     await ctx.reply("Sorry, but once you go black you never go back!")


def setup(bot):
    bot.add_cog(NWordCounter(bot))

