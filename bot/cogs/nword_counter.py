"""Cog for n-word counting and storing logic"""
import re
import random
import string
from pprint import pprint

import discord
from discord import option
from discord.ext import commands
from utils.database import Database
from utils.discord import convert_color, generate_message_embed

# Create the n-word lists from ASCII, so I don't have to type it.
NWORDS_LIST = [
    (chr(110) + chr(105) + chr(103) + chr(103) + chr(97)),
    (chr(47) + chr(92) + chr(47) + chr(105) + chr(103) + chr(103) + chr(97)),
    (chr(124) + chr(92) + chr(47) + chr(105) + chr(103) + chr(103) + chr(97))
]
HARD_RS_LIST = [
    (chr(110) + chr(105) + chr(103) + chr(103) + chr(101) + chr(114)),
    (chr(47) + chr(92) + chr(47) + chr(105) + chr(103) + chr(103) + chr(101) +
     chr(114)),
    (chr(124) + chr(92) + chr(47) + chr(105) + chr(103) + chr(103) + chr(101) +
     chr(114))]


class NWordCounter(commands.Cog):
    """Commands for n-word count tracking"""

    def __init__(self, bot):
        self.bot = bot

        # Get singleton database connection.
        self.db = Database()

        self.sacred_n_words = NWORDS_LIST
        self.sacred_hard_r_words = HARD_RS_LIST

    def count_nwords(self, msg: str) -> int:
        """Return occurrences of n-words in a given message"""
        count = 0
        msg = msg.lower().strip().translate(
            {ord(char): "" for char in string.whitespace})

        for n_word in self.sacred_n_words:
            count += msg.count(n_word)
        for hard_r in self.sacred_hard_r_words:
            count += msg.count(hard_r)

        return count

    def is_black(self, guild_id, author_id) -> bool:
        """Check if user is verified to be black"""
        member = self.db.member_in_database(guild_id, author_id)
        if member["is_black"]:
            return True
        return False

    def get_member_nword_count(self, guild_id, member_id) -> int:
        """Return number of n-words said by member if tracked in database"""
        member: object | None = self.db.member_in_database(guild_id, member_id)
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
                ["Bro wtf :face_with_raised_eyebrow:", ":expressionless:",
                 "CHILL",
                 ":camera_with_flash::camera_with_flash::camera_with_flash:",
                 "..."])
        else:
            msg = random.choice(
                [
                    "I have no words.",
                    "Tf?",
                    ":exploding_head:",
                    ":flushed:",
                    "I'm calling your employer",
                    "This gotta affect your credit score somehow",
                    "Quit this madness",
                    "Bro you ARE the n-word pass",
                    ":farmer:"
                ]
            )

        return msg

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect n-words"""
        # Prevent missing permissions stdout clogging.
        in_guild: bool = message.guild is not None
        if not in_guild:
            return
        has_message_perms: bool = message.channel.permissions_for(
            message.guild.me).send_messages

        if message.author == self.bot.user:  # Ignore reading itself.
            return
        if message.author.bot:  # Ignore spammy bots.
            return

        guild = message.guild
        msg = message.content
        author = message.author  # Should fetch user by ID instead of name.

        # Add notice of migration to slash commands.
        if msg.startswith("n!") and has_message_perms:
            await message.reply(embed=generate_message_embed(
                f"**{message.author.display_name.title()}** we've moved to slash commands! Use `/` to get started.",
                color=convert_color("#ff2222")), delete_after=10)
            # If we have permission to delete the original message, do so.
            if message.channel.permissions_for(
                    message.guild.me).manage_messages:
                await message.delete(delay=10)

        # Ensure guild has its own place in the database.
        if not self.db.guild_in_database(guild.id):
            self.db.create_database(guild.id, guild.name)

        # Bot reaction to any n-word occurrence.
        num_nwords = self.count_nwords(msg)

        # No n-words found.
        if num_nwords <= 0:
            return

        if message.webhook_id and has_message_perms:  # Ignore webhooks.
            await message.reply(
                content="Not a person, I won't count this.",
                delete_after=30
            )
            return

        if not self.db.member_in_database(guild.id, author.id):
            self.db.create_member(guild.id, author.id, author.name)

        self.db.increment_nword_count(guild.id, author.id, num_nwords)

        # Don't react to someone already verified.
        if self.is_black(guild.id, author.id):
            return

        # Mitigate ratelimiting, usually this amount is just spam.
        if num_nwords >= 50:
            return

        # CAUGHT in 4k.
        response = self.get_msg_response(nword_count=num_nwords)
        if has_message_perms:
            await message.channel.send(f"{message.author.mention} {response}")

    def get_id_from_mention(self, mention: str) -> int:
        """Extract user ID from mention string"""
        # STORED IN DB AS INTEGER, NOT STRING.
        # use regex to remove any non-numeric characters
        print(mention, re.sub("[^0-9]", "", mention))
        return int(re.sub("[^0-9]", "", mention))

    def verify_mentions(self, mentions: discord.Member,
                        ctx: discord.ApplicationContext) -> str:
        """Check if mention being passed into command is valid. This is no longer needed as discord does this for us.
        With slash commands.

        This code now checks if the user is in the guild, and if not, returns an error message.
        """

        # Ensure user is part of guild.
        guild = ctx.guild
        if not guild.get_member(mentions.id):
            return "User not in server"
        else:
            return ""

    @commands.slash_command(
        name="count",
        description="Get a person's total n-word count")
    @option(name="user", description="User to get count of", required=False)
    async def count(self, ctx, user: discord.Member = None):
        """Get a person's total n-word count"""
        await ctx.defer()
        user = user if user else ctx.author
        # Validate mention.
        invalid_mention_msg = self.verify_mentions(user, ctx)
        if invalid_mention_msg:
            await ctx.respond(invalid_mention_msg)
            return

        # Fetch n-word count of user if they have a count.
        nword_count = self.get_member_nword_count(ctx.guild.id, user.id)
        await ctx.respond(embed=generate_message_embed(
            f"**{user.display_name}** has said the n-word **{nword_count:,}** time{'' if nword_count == 1 else 's'}",
            type="info", ctx=ctx), ephemeral=True, delete_after=30)

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

    def user_voted_for(self, voter_id: int, member: dict) -> bool:
        """Return whether the user voted for the member"""
        if member is None:
            return False

        voter_list = member["voters"]
        if voter_id in voter_list:
            return True

        return False

    @commands.slash_command(
        name="vote",
        description="Vouch for someone's blackness")
    @option(name="user", description="User to vote for", required=False)
    async def vote(self, ctx, user: discord.Member = None):
        """Vouch to verify someone's blackness"""
        await ctx.defer()
        if not user:
            vote_status_msg, type = self.perform_vote(ctx, "vote")
        else:
            vote_status_msg, type = self.perform_vote(ctx, "vote", user)
        await ctx.respond(embed=generate_message_embed(vote_status_msg, type=type, ctx=ctx), ephemeral=True,
                          delete_after=30)

    @commands.slash_command(
        name="unvote",
        description="Remove a vouch for a person")
    @option(name="user", description="User to unvote", required=False)
    async def unvote(self, ctx, user: discord.Member = None):
        """Remove a vouch for a person"""
        await ctx.defer()
        if not user:
            vote_status_msg, type = self.perform_vote(ctx, "unvote")
        else:
            vote_status_msg, type = self.perform_vote(ctx, "unvote", user)
        await ctx.respond(embed=generate_message_embed(vote_status_msg, type=type, ctx=ctx), ephemeral=True,
                          delete_after=30)

    def get_vote_return_msgs(self, type, votes, vote_threshold) -> dict:
        """Get vote responses messages based on action"""
        msgs_dict = dict()
        if type == "vote":
            msgs_dict[
                "already_performed_msg"] = f"You already voted for this person!\n({votes}/{vote_threshold}) required " \
                                           f"votes so far!"
            msgs_dict["error_performed_msg"] = "Couldn't vote for person"
            msgs_dict[
                "success_performed_msg"] = f"Successfully voted!\n({votes}/{vote_threshold}) required votes so far!"
        else:
            msgs_dict[
                "already_performed_msg"] = f"You never voted for this person!\n({votes}/{vote_threshold}) required " \
                                           f"votes so far!"
            msgs_dict["error_performed_msg"] = "Couldn't unvote person"
            msgs_dict[
                "success_performed_msg"] = f"Successfully removed vote!\n({votes}/{vote_threshold}) required votes so " \
                                           f"far!"
        return msgs_dict

    def perform_vote(self, ctx: discord.ApplicationContext, type: str,
                     user: discord.Member = None) -> tuple[str, str]:
        """Main logic for voting and unvoting
           user = user to vote for
           user_d = user data from database
           type = vote or unvote"""
        user = user if user else ctx.author

        # Must mention someone.
        invalid_mention_msg = self.verify_mentions(user, ctx)
        if invalid_mention_msg:
            return invalid_mention_msg, "error"

        # Can't vote for yourself.
        if user.id == ctx.author.id:
            return "You can't vote/unvote for yourself bozo", "error"

        # Create member if not already in database.
        user_d = self.db.member_in_database(ctx.guild.id, user.id)
        if not user_d:
            self.db.create_member(ctx.guild.id, user.id, user.name)

        # Use ctx.guild.members to get a list of members in the server and remove any bots.
        member_count = len(
            [member for member in ctx.guild.members if not member.bot])
        vote_threshold = self.get_vote_threshold(member_count)
        votes = len(user_d["voters"])

        # Check whether user has a vote casted on them already.
        if type == "vote":
            if self.user_voted_for(ctx.author.id, user_d):
                msg = self.get_vote_return_msgs(type, votes, vote_threshold)
                return msg["already_performed_msg"], "error"
        else:
            if not self.user_voted_for(ctx.author.id, user_d):
                msg = self.get_vote_return_msgs(type, votes, vote_threshold)
                return msg["already_performed_msg"], "error"

        # Perform and let know result.
        voted = self.db.cast_vote(
            type, ctx.guild.id, vote_threshold, ctx.author.id, user.id)
        member = self.db.member_in_database(ctx.guild.id, user.id)
        votes = len(member["voters"])
        if not voted:
            msg = self.get_vote_return_msgs(type, votes, vote_threshold)
            return msg["error_performed_msg"], "error"
        else:
            msg = self.get_vote_return_msgs(type, votes, vote_threshold)
            return msg["success_performed_msg"], "success"

    @commands.slash_command(
        name="whoblack",
        description="See who's verified black in this server")
    async def whoblack(self, ctx):
        """See who's verified black in this server"""
        await ctx.defer()
        member_list = [
            member["name"]
            for member in self.db.get_member_list(ctx.guild.id)
            if member["is_black"]
        ]
        msg = "Verified black members in this server:\n"
        if len(member_list) == 0:
            msg += "`None`"
        else:
            for member in member_list:
                msg += f" `{member}`"
        await ctx.respond(embed=generate_message_embed(msg, type="info", ctx=ctx), delete_after=30)

    @commands.slash_command(
        name="whohaspass",
        aliases=["whopass"],
        description="See who has an n-word pass in this server")
    async def whohaspass(self, ctx):
        """See who has an n-word pass in this server"""
        await ctx.defer()
        member_list = [
            member["name"]
            for member in self.db.get_member_list(ctx.guild.id)
            if member["has_pass"]
        ]
        msg = "Verified pass holders in this server:\n"
        if len(member_list) == 0:
            await ctx.respond(embed=generate_message_embed("No one in this server has any passes!", type="warning",
                                                           ctx=ctx),
                              delete_after=30)
            return True
        else:
            for member in member_list:
                msg += f" `{member}`"
        await ctx.respond(embed=generate_message_embed(msg, type="info", ctx=ctx),
                          delete_after=30)
        return True

    @commands.slash_command(
        name="passes",
        description="See your or someone else's total passes available")
    @option(name="user", description="User to see passes for", required=False)
    async def passes(self, ctx, mention: discord.Member = None):
        """See your or someone else's total passes available"""
        await ctx.defer()
        if not mention:  # Passes for author.
            member = self.db.member_in_database(ctx.guild.id, ctx.author.id)
            if not member:
                self.db.create_member(
                    ctx.guild.id, ctx.author.id, ctx.author.name)
                member = self.db.member_in_database(
                    ctx.guild.id, ctx.author.id)
            await ctx.respond(embed=generate_message_embed(
                f"N-word passes for {ctx.author.display_name}: `{member['passes']}`", type="info", ctx=ctx),
                delete_after=30)
        else:  # Passes for mentioned member.
            invalid_mention_msg = self.verify_mentions(mention, ctx)
            if invalid_mention_msg:
                await ctx.send(invalid_mention_msg)
                return
            member = self.db.member_in_database(ctx.guild.id, mention.id)
            if not member:
                self.db.create_member(ctx.guild.id, mention.id, mention.name)
                member = self.db.member_in_database(ctx.guild.id, mention.id)
            await ctx.respond(embed=generate_message_embed(
                f"N-word passes for {mention.display_name}: `{member['passes']}`", type="info", ctx=ctx),
                delete_after=30)

    @commands.slash_command(
        name="givepass",
        description="Give n-word pass to another user")
    @option(name="user", description="User to give pass to", required=True)
    async def givepass(self, ctx, user: discord.User):
        """Give n-word passes to another person"""
        await ctx.defer()
        await ctx.respond("Feature coming soon!")


def setup(bot):
    bot.add_cog(NWordCounter(bot))
