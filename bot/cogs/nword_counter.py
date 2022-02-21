"""Cog for n-word counting and storing logic"""
import random
import string
from json import load
from pathlib import Path
from typing import List

import pymongo
import discord
from discord.ext import commands

# Fetch MongoDB token for database access.
with Path("../config.json").open() as f:
    config = load(f)
    mongo_url = config["MONGO_URL"]


class NWordCounter(commands.Cog):
    """Category for n-word occurrences
    
    TODO (✔️) (❌)
    ✔️ complete database functionality
    ✔️ complete count_nwords unittest
    ✔️ comlpete pymongo unittest
    ✔️ implement server total n-words lookup command
    ✔️ implement server ranking lookup
    ✔️ implement voting system
    ✔️ implement single user n-word lookup
    ❌ implement bigger table for count_nword translate method
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

        n_words = [  # Don't cancel me for typing this.
            "nigga", "/\/igga", "|\/igga",
            "nigger", "/\/igger", "|\/igger"
        ]
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
        find_member_cursor = self.collection.aggregate(
            [
                {
                    "$match": {
                        "guild_id": guild_id,
                        "members.id": member_id  # STORED AS AN INTEGER NOT STRING.
                    }
                },
                {
                    "$unwind": "$members"
                },
                {
                    "$match": {
                        "members.id": member_id
                    }
                },
                {
                    "$replaceWith": "$members"
                }
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
                        "has_pass": False,
                        "passes": 0,
                        "voters": []
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
    

    def increment_passes(self, guild_id, member_id, count) -> None:
        """Add to user's total available n-word passes in server"""
        self.collection.update_one(
            {
                "guild_id": guild_id,
                "members.id": member_id
            },
            {
                "$inc": {
                    "members.$.passes": count
                }
            },
            upsert=False  # Don't create new document if not found.
        )

    
    def is_black(self, guild_id, author_id) -> bool:
        """Check if user is verified to be black"""
        member = self.member_in_database(guild_id, author_id)
        if member["is_black"]:
            return True
        return False
    

    def get_member_nword_count(self, guild_id, member_id) -> int:
        """Return number of n-words said by member if tracked in database"""
        member: object | None = self.member_in_database(guild_id, member_id)
        if not member:
            return 0
        return member["nword_count"]
    

    def get_msg_response(self, nword_count: int) -> str:
        """Return bot message response based on n-words said"""
        msg = None
        if nword_count < 5:
            msg = random.choice(
                [
                    "Bro? :face_with_raised_eyebrow::camera_with_flash:",
                    "??? :face_with_raised_eyebrow::camera_with_flash:",
                    "CAUGHT :camera_with_flash:",
                    "4K :camera_with_flash:",
                    ":face_with_raised_eyebrow:"
                ]
            )
        elif nword_count < 25:
            msg = random.choice(
                [
                    "Bro chill with it :camera_with_flash:",
                    "?????????? :camera_with_flash:",
                    "Bro cmon :neutral_face:",
                    "Bro..."
                ]
            )
        elif nword_count < 100:
            msg = random.choice(
                [
                    "Bro wtf :face_with_raised_eyebrow:",
                    ":expressionless:",
                    "CHILL",
                    ":camera_with_flash::camera_with_flash::camera_with_flash:",
                    "..."
                ]
            )
        else:
            msg = random.choice(
                [
                    "I have no words.",
                    "Tf?",
                    ":exploding_head:",
                    ":flushed:",
                    "I'm calling your employer"
                ]
            )
        
        return msg
    

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect n-words"""
        if message.author == self.bot.user:  # Ignore reading itself.
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
            if message.webhook_id:  # Ignore webhooks.
                await message.reply("Not a person, I won't count this.")
                return

            if not self.member_in_database(guild.id, author.id):
                self.create_member(guild.id, author.id, author.name)
            
            self.increment_nword_count(guild.id, author.id, num_nwords)

            if self.is_black(guild.id, author.id):  # Don't react to someone already verified.
                return

            # response = f":camera_with_flash: Detected **{num_nwords}** n-words!"
            response = self.get_msg_response(nword_count=num_nwords)
            await message.reply(f"{message.author.mention} {response}")
    

    def get_id_from_mention(self, mention: str) -> int:
        """Extract user ID from mention string"""
        # STORED IN DB AS INTEGER, NOT STRING.
        return int(mention.replace("<@!", "").replace("<@", "").replace(">", ""))
    

    def verify_mentions(self, mentions, ctx) -> str:
        """Check if mention being passed into command is valid.
        
        Return error message if not validated
        Return "" if validated
        """
        if not mentions:
            return "Mention not found"
        elif len(mentions) > 1:
            return "Only mention one user"
        
        id_from_mention = mentions[0].id

        # Ensure user is part of guild.
        guild = ctx.guild
        if not guild.get_member(id_from_mention):
            return "User not in server"
        
        return ""
    

    @commands.command()
    async def count(self, ctx, mention=None):
        """Get a person's total n-word count"""
        mentions: list = ctx.message.mentions
        member_id = None
        mention_name = None

        if not mention:  # No mention = get author.
            member_id = ctx.author.id
            mention_name = ctx.author.mention
        else:  # Validate mention.
            invalid_mention_msg = self.verify_mentions(mentions, ctx)
            if invalid_mention_msg:
                await ctx.reply(invalid_mention_msg)
                return
            member_id = mentions[0].id
            mention_name = mention

        # Fetch n-word count of user if they have a count.
        nword_count = self.get_member_nword_count(ctx.guild.id, member_id)
        await ctx.send(f"Total n-word count for {mention_name}: `{nword_count:,}`")


    def get_nword_server_total(self, guild_id) -> int:
        """Return integer sum of total n-words said in a server"""
        cursor = self.collection.aggregate(
            [
                {
                    "$match": {
                        "guild_id": guild_id
                    }
                },
                {
                    "$unwind": "$members"
                },
                {
                    "$group": {
                        "_id": guild_id,
                        "total_nwords": {
                            "$sum": "$members.nword_count"
                        }
                    }
                }
            ]
        )

        cursor_as_list = list(cursor)
        if len(cursor_as_list) == 0:
            return 0
        return cursor_as_list[0]["total_nwords"]


    @commands.command()
    async def servercount(self, ctx):
        """Return server accumulated nword count"""
        # Database, not client, should handle summing as a large member count would put great strain.
        sum: int = self.get_nword_server_total(ctx.guild.id)
        await ctx.send(f"(since bot join)\nThere have been a total of `{sum:,}` n-words said in this server")
    

    def get_member_list(self, guild_id) -> List[object] | List[None]:
        """Return sorted ranked list of member objects based on n-word frequency"""
        cursor = self.collection.aggregate(
            [
                {
                    "$match": {"guild_id": guild_id}  # Get guild document.
                },
                {
                    "$unwind": "$members"  # Unravel array of member objects.
                },
                {
                    "$sort": {  # Sort in descending order.
                        "members.nword_count": -1
                    }
                },
                {
                    "$group": {  # Create custom group of member objects.
                        "_id": None,
                        "member_object_list": {  # To be included per member object.
                            "$push": {
                                "name": "$members.name",
                                "is_black": "$members.is_black",
                                "has_pass": "$members.has_pass",
                                "nword_count": "$members.nword_count"
                            }
                        },
                    }
                },
                {
                    "$project": {  # Only include member array.
                        "_id": False,
                        "member_object_list": True
                    }
                }
            ]
        )
        cursor_as_list = list(cursor)
        if len(cursor_as_list) == 0:
            return []
        return cursor_as_list[0]["member_object_list"]
    

    # TODO: refactor
    @commands.command()
    async def rankings(self, ctx, num_rankings=10):
        """View server's member rankings by n-word count"""

        # Possible range to display.
        if num_rankings < 10 or num_rankings > 100:
            await ctx.reply("Can only show 10 to 100 member rankings")
            return

        # Fetch server members from database.
        member_list: List[object] = self.get_member_list(ctx.guild.id)

        # Dummy fill list.
        num_members_left = len(member_list)
        if num_members_left > num_rankings:  # Resize to fit ranking size.
            member_list = member_list[:num_rankings]
        elif num_members_left < num_rankings:  # Fill up remaining slots.
            remaining = num_rankings - num_members_left
            for i in range(remaining):
                member_list.append(
                    {"name": None, "is_black": False, "has_pass": False, "nword_count": None}
                )
        num_members_left = len(member_list)

        # Store embeds in a list depending on how many member objects have been retrieved.
        MAX_MEMBERS_PER_PAGE = 10
        pagination_list = []

        # Splice up to 10 members per pagination embed.
        # TODO: maybe come up with a better algorithm for fetching batches.
        member_idx_start = 0
        member_idx_end = MAX_MEMBERS_PER_PAGE
        curr_rank_num = 1
        while num_members_left > 0:
            # Current embed page content.
            embedded_msg = discord.Embed(
                title=f"Server N-word Rankings",
                description=f"Total n-words: **{self.get_nword_server_total(ctx.guild.id):,}**\n_* next to name are verified black_\n_~ has an n-word pass_",
                color=discord.Color.blurple(),
                url="https://bit.ly/3JmG6cD"
            )

            # Fill up page content with next batch of rankings.
            page_content = ""
            num_members_in_page_content = 0
            next_batch = member_list[member_idx_start:member_idx_end]
            for curr_member in next_batch:

                # Top 3 have medal emojis lol.
                rank_emojis = ["🥇", "🥈", "🥉"]
                emoji = None
                match curr_rank_num:
                    case 1:
                        emoji = rank_emojis[0]
                    case 2:
                        emoji = rank_emojis[1]
                    case 3:
                        emoji = rank_emojis[2]
                
                # * next to name signifies they are black.
                signifier = ""
                if curr_member["name"] is not None:
                    if curr_member["is_black"]:
                        signifier += "*"
                    elif curr_member["has_pass"]:
                        signifier += "~"

                if curr_member["name"] is None:
                    page_content += f"**{curr_rank_num}** N/A\n"
                elif curr_rank_num <= 3:
                    page_content += f"**{emoji}** {signifier}{curr_member['name']} - **{curr_member['nword_count']:,}** n-words\n"
                else:
                    page_content += f"**{curr_rank_num}** {signifier}{curr_member['name']} - **{curr_member['nword_count']:,}** n-words\n"
                num_members_in_page_content += 1
                curr_rank_num += 1

            embedded_msg.add_field(name=f"Showing Top {num_rankings}", value=page_content, inline=False)
            embedded_msg.set_footer(text=f"Requested by {ctx.author.name}")
            num_members_left -= MAX_MEMBERS_PER_PAGE  # Move on to next batch of members.
            member_idx_start += MAX_MEMBERS_PER_PAGE
            member_idx_end += MAX_MEMBERS_PER_PAGE
            pagination_list.append(embedded_msg)
        
        # Add reaction buttons.
        message = await ctx.send(embed=pagination_list[0])
        await message.add_reaction('⏮')
        await message.add_reaction('◀')
        await message.add_reaction('▶')
        await message.add_reaction('⏭')

        # Only the message author may react to the message.
        def check(reaction, user):
            return (user == ctx.message.author)
        
        # Handle user reactions to navigate embedded pages.
        i = 0
        reaction = None
        while True:
            if str(reaction) == '⏮':
                i = 0
                await message.edit(embed=pagination_list[i])
            elif str(reaction) == '◀':
                if i > 0:
                    i -= 1
                    await message.edit(embed=pagination_list[i])
            elif str(reaction) == '▶':
                if i < len(pagination_list) - 1:
                    i += 1
                    await message.edit(embed=pagination_list[i])
            elif str(reaction) == '⏭':
                i = len(pagination_list) - 1
                await message.edit(embed=pagination_list[i])
            
            # Wait for reaction to be added and break if timeout.
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                await message.remove_reaction(reaction, user)
            except Exception as e:
                break
        
        # Signify that user can no longer navigate pages due to timeout.
        await message.clear_reactions()
    

    def get_vote_threshold(self, member_count: int) -> int:
        """Return votes required to verify based on server member count"""
        if member_count < 3:
            return 1
        elif member_count < 10:
            return 2
        elif member_count < 50:
            return 3
        elif member_count < 100:
            return 4
        elif member_count < 250:
            return 5
        else:
            return 10
    

    def user_voted_for(self, voter_id: int, member: object) -> bool:
        """Return whether or not user voted for the member"""
        if member is None:
            return False

        voter_list = member["voters"]
        if voter_id in voter_list:
            return True

        return False
    

    def cast_vote(
        self, type: str, guild_id: int, vote_threshold: int, voter_id: int, votee_id: int
    ) -> None | object:
        """Insert voter id into votee's voter list in database"""
        action = None
        if type == "vote":
            action = {
                "$push": {"members.$.voters": voter_id}  # Add vote count to user's voters.
            }
        else:
            action = {
                "$pull": {"members.$.voters": voter_id}  # Remove vote count.
            }

        # Update member object.
        voted = self.collection.update_one(
            {
                "guild_id": guild_id,
                "members.id": votee_id
            },
            action,
            upsert=False
        )
        
        if not voted:  # User doesn't exist.
            return None
        
        # Check if enough votes to be verified black.
        member = self.member_in_database(guild_id, votee_id)
        set_black = None
        if len(member["voters"]) >= vote_threshold:  # Enough votes.
            set_black = {
                "$set": {"members.$.is_black": True}
            }
        else:
            set_black = {
                "$set": {"members.$.is_black": False}
            }

        # Update member object.
        self.collection.update_one(
            {
                "guild_id": guild_id,
                "members.id": votee_id
            },
            set_black,
            upsert=False
        )

        return member
    

    @commands.command()
    async def vote(self, ctx, mention=None):
        """Vouch to verify someone's blackness"""
        vote_status_msg = ""
        if not mention:
            vote_status_msg = self.perform_vote(ctx, "vote")
        else:
            vote_status_msg = self.perform_vote(ctx, "vote", mention)
        await ctx.reply(vote_status_msg)


    @commands.command()
    async def unvote(self, ctx, mention=None):
        """Remove a vouch for a person"""
        vote_status_msg = ""
        if not mention:
            vote_status_msg = self.perform_vote(ctx, "unvote")
        else:
            vote_status_msg = self.perform_vote(ctx, "unvote", mention)
        await ctx.reply(vote_status_msg)
    

    def get_vote_return_msgs(self, type, votes, vote_threshold) -> dict:
        """Get vote responses messages based on action"""
        msgs_dict = dict()
        if type == "vote":
            msgs_dict["already_performed_msg"] = f"You already voted for this person!\n({votes}/{vote_threshold}) required votes so far!"
            msgs_dict["error_performed_msg"] = "Couldn't vote for person"
            msgs_dict["success_performed_msg"] = f"Successfully voted!\n({votes}/{vote_threshold}) required votes so far!"
        else:
            msgs_dict["already_performed_msg"] = f"You never voted for this person!\n({votes}/{vote_threshold}) required votes so far!"
            msgs_dict["error_performed_msg"] = "Couldn't unvote person"
            msgs_dict["success_performed_msg"] = f"Successfully removed vote!\n({votes}/{vote_threshold}) required votes so far!"
        return msgs_dict



    def perform_vote(self, ctx, type, mention=None) -> str:
        """Main logic for voting and unvoting"""
        mentions: list = ctx.message.mentions
        mention_id = None
        mention_name = None

        # Must mention someone.
        invalid_mention_msg = self.verify_mentions(mentions, ctx)
        if invalid_mention_msg:
            return invalid_mention_msg
        
        mention_id = mentions[0].id
        mention_name = mentions[0].name
        
        # Can't vote for yourself.
        if mention_id == ctx.author.id:
            return "You can't vote/unvote for yourself bozo"

        # Create member if not already in database.
        member = self.member_in_database(ctx.guild.id, mention_id)
        if not member:
            self.create_member(ctx.guild.id, mention_id, mention_name)
        
        member_count = len(ctx.guild.members)
        vote_threshold = self.get_vote_threshold(member_count)
        votes = len(member["voters"])

        # Check whether user has a vote casted on them already.
        if type == "vote":
            if self.user_voted_for(ctx.author.id, member):
                msg = self.get_vote_return_msgs(type, votes, vote_threshold)
                return msg["already_performed_msg"]
        else:
            if not self.user_voted_for(ctx.author.id, member):
                msg = self.get_vote_return_msgs(type, votes, vote_threshold)
                return msg["already_performed_msg"]
            
        # Perform and let know result.
        voted = self.cast_vote(type, ctx.guild.id, vote_threshold, ctx.author.id, mention_id)
        member = self.member_in_database(ctx.guild.id, mention_id)
        votes = len(member["voters"])
        if not voted:
            msg = self.get_vote_return_msgs(type, votes, vote_threshold)
            return msg["error_performed_msg"]
        else:
            msg = self.get_vote_return_msgs(type, votes, vote_threshold)
            return msg["success_performed_msg"]


    @commands.command()
    async def whoblack(self, ctx):
        """See who's verified black in this server"""
        member_list = [
            member["name"]
            for member in self.get_member_list(ctx.guild.id)
            if member["is_black"]
        ]
        msg = "Verified black members in this server:\n"
        if len(member_list) == 0:
            msg += "`None`"
        else:
            for member in member_list:
                msg += f" `{member}`"
        await ctx.send(msg)
    

    @commands.command()
    async def whohaspass(self, ctx):
        """See who has an n-word pass in this server"""
        member_list = [
            member["name"]
            for member in self.get_member_list(ctx.guild.id)
            if member["has_pass"]
        ]
        msg = "Verified pass holders in this server:\n"
        if len(member_list) == 0:
            msg += "`None`"
        else:
            for member in member_list:
                msg += f" `{member}`"
        await ctx.send(msg)
    

    @commands.command()
    async def passes(self, ctx, mention=None):
        """See your or someone else's total passes available"""
        mentions: list = ctx.message.mentions

        if not mention:  # Passes for author.
            member = self.member_in_database(ctx.guild.id, ctx.author.id)
            if not member:
                self.create_member(ctx.guild.id, ctx.author.id, ctx.author.name)
                member = self.member_in_database(ctx.guild.id, ctx.author.id)
            await ctx.send(f"Your n-word passes: `{member['passes']}`")
        else:  # Passes for mentioned member.
            invalid_mention_msg = self.verify_mentions(mentions, ctx)
            if invalid_mention_msg:
                await ctx.send(invalid_mention_msg)
                return

            mention_id = mentions[0].id
            mention_name = mentions[0].name
            member = self.member_in_database(ctx.guild.id, mention_id)
            if not member:
                self.create_member(ctx.guild.id, mention_id, mention_name)
                member = self.member_in_database(ctx.guild.id, mention_id)
            await ctx.send(f"N-word passes for {mention_name}: `{member['passes']}`")


    @commands.command()
    async def givepass(self, ctx):
        """Give n-word passes to another person"""
        await ctx.send("Feature coming soon!")


def setup(bot):
    bot.add_cog(NWordCounter(bot))

