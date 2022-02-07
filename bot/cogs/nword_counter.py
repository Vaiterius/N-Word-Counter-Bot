"""Cog for n-word counting and storing logic"""
import string
from json import load
from pathlib import Path

import pymongo
from discord.ext import commands

# Fetch bot token.
with Path("../config.json").open() as f:
    config = load(f)

mongo_url = config["MONGO_URL"]


class NWordCounter(commands.Cog):
    """Command category for n-word occurrences"""

    def __init__(self, bot):
        self.bot = bot

        # Initialize Mongo database.
        # self.cluster = pymongo.MongoClient(mongo_url)
        # self.db = self.cluster["NWordCounter"]
        # self.collection = self.db["guild_users_db"]
    
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
        """Initialize all guild params in database"""
        # Upload base template.
        self.collection.insert_one(
            {
                "guild_id": guild.id,
                "guild_name": guild.name,
                "members": {}
            }
        )
    
    def member_in_database(self, guild_id, member) -> bool:
        """Return True if member is already recorded in guild database"""
        return self.collection.find_one(
            {"guild_id": guild_id}["members"]["name": member]
        )
    
    def create_member(self, guild_id, member) -> None:
        """Initialize member data in guild database"""
        self.collection.update(
            {"guild_id": guild_id}, {
                "$set": {
                    "members": {
                        "name": member,
                        "is_black": False,
                    }
                }
            }
        )
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect n-words"""
        if message.author == self.bot.user:
            return
        
        guild = message.guild
        msg = message.content
        author = message.author

        # Ensure guild has its own place in the database.
        # if not self.guild_in_database(guild):
        #     self.create_database(guild)
        
        # Bot reaction to any n-word occurrence.
        num_nwords = self.count_nwords(msg)
        if num_nwords > 0:

            # TODO

            await message.reply(
                f":camera_with_flash: Detected **{num_nwords}** n-words!"
            )
    
    # @commands.command()


def setup(bot):
    bot.add_cog(NWordCounter(bot))
