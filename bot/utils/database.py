"""Pymongo utility class with database commands"""
import os

import pymongo

# Fetch MongoDB token for database access.
mongo_url = os.environ.get("MONGO_URL")


class Database:
    """MongoDB database"""
    
    def __init__(self):
        self._cluster = pymongo.MongoClient(mongo_url)
        self.db = self._cluster["NWordCounter"]
        self._collection = self.db["guild_users_db"]
    
    @property
    def collection(self):
        return self._collection
    
    def guild_in_database(self, guild_id: int) -> bool:
        """Return True if guild is already recorded in database"""
        return self.db.collection.count_documents(
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
    

    def get_member_list(self, guild_id) -> list[object] | list[None]:
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

