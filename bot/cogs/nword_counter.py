"""Cog for n-word counting and storing logic"""
import string
from json import load
from pathlib import Path
from pprint import pprint

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
    ✔️ comlpete pymongo unittest
    ❌ implement server total n-words lookup command
    ❌ implement voting system
    ✔️ implement single user n-word lookup
    ❌ implement bigger table for count_nword translate method
    ❌ implement new db collection solely for member votes
    ❌ implement give n-word pass functionality
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
    

    def guild_in_database(self, guild_id: int) -> bool:
        """Return True if guild is already recorded in database"""
        return self.collection.count_documents(
            {"guild_id": guild_id}
        ) != 0
    

    def create_database(self, guild_id: int, guild_name: str) -> None:
        """Initialize guild template in database"""
        self.collection.insert_one(
            {
                "guild_id": guild_id,
                "guild_name": guild_name,
                "members": []
            }
        )


    def member_in_database(self, guild_id: int, member_id: int) -> object | None:
        """Return True if member is already recorded in guild database"""
        # return self.fetch_guild_member_info(guild, member) != None
        find_member_cursor = self.collection.aggregate(
            [
                {
                    "$match": {
                        "guild_id": guild_id,
                        "members.id": member_id  # STORED AS AN INTEGER NOT STRING.
                    }
                },
                {"$unwind": "$members"},
                {
                    "$match": {
                        "members.id": member_id
                    }
                },
                {"$replaceWith": "$members"}
            ]
        )
        cursor_as_list = list(find_member_cursor)
        if len(cursor_as_list) == 0:
            return None
        return cursor_as_list[0]


    def create_member(self, guild_id, member_id, member_name) -> None:
        """Initialize member data in guild database"""
        self.collection.update_one(
            {"guild_id": guild_id}, {
                "$push": {
                    "members": {
                        "id": member_id,  # STORED AS AN INTEGER NOT STRING.
                        "name": member_name,
                        "nword_count": 0,
                        "is_black": False,
                    }
                }
            }
        )
    

    def increment_nword_count(self, guild_id, member_id, count) -> None:
        """Add to n-word count of person's data info in server"""
        self.collection.update_one(
            {
                "guild_id": guild_id,
                "members.id": member_id
            },
            {
                "$inc": {
                    "members.$.nword_count": count
                }
            },
            upsert=False  # Don't create new document if not found.
        )
    

    def get_member_nword_count(self, guild_id, member_id) -> int:
        """Return number of n-words said by member if tracked in database"""
        member: object | None = self.member_in_database(guild_id, member_id)
        if not member:
            return 0
        return member["nword_count"]
    

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect n-words"""
        if message.author == self.bot.user:
            return
        
        guild = message.guild
        msg = message.content
        author = message.author  # Should fetch user by ID instead of name.

        # Ensure guild has its own place in the database.
        if not self.guild_in_database(guild.id):
            self.create_database(guild.id, guild.name)
        
        # Bot reaction to any n-word occurrence.
        num_nwords = self.count_nwords(msg)
        if num_nwords > 0:

            if not self.member_in_database(guild.id, author.id):
                self.create_member(guild.id, author.id, author.name)
            
            self.increment_nword_count(guild.id, author.id, num_nwords)

            await message.reply(
                f":camera_with_flash: Detected **{num_nwords}** n-words!"
            )
    

    @commands.command()
    async def count(self, ctx, mention):
        """Return total nword count of a person in a server"""
        try:
            # Ensure message contains only one mention.
            mentions: list = ctx.message.mentions
            if not mentions:
                raise Exception("Mention not found")
            elif len(mentions) > 1:
                raise Exception("Only mention one user")
        except Exception as e:
            await ctx.reply(e)
            return
        
        id_from_mention = int(mention.replace("<@!", "").replace(">", ""))  # STORED AS AN INTEGER NOT STRING.
        
        # Ensure user is part of guild.
        guild = ctx.guild
        if not guild.get_member(id_from_mention):
            await ctx.reply("User not in guild")
            return

        # Fetch n-word count of user if they have a count.
        nword_count = self.get_member_nword_count(ctx.guild.id, id_from_mention)
        await ctx.reply(f"Total n-word count for {mention}: {nword_count}")


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


    # # SPECIAL FEATURE TO BE ADDED SOON??
    # @commands.command()
    # async def givepass(self, ctx, mention, count):
    #     """Give n-word passes as a verified black person to another person"""
    #     pass


def setup(bot):
    bot.add_cog(NWordCounter(bot))

