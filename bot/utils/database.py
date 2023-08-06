"""~~Pymongo~~ Motor utility class with database commands"""
import os
import logging
from json import load
from pathlib import Path
import os
import json
from pprint import pprint
from typing import Dict, Any

import motor.motor_asyncio as motor  # Asyncio version of pymongo.

# In case people want to run this on different platforms.
config_filepath: str = "\\config.json"
if os.name == "posix":  # Linux or macOS.
    config_filepath = config_filepath.replace("\\", "/")

# Fetch MongoDB token for database access.
# using OS module ensures that the path is relative to the file that is being executed.
with Path(
        os.path.abspath(
            os.path.join(os.getcwd(), os.pardir)
        ) + config_filepath).open() as f:
    config = load(f)
    mongo_url = config["MONGO_URL"]

# DO NOT TOUCH - for running on hosting platform:
if mongo_url == "":
    mongo_url = os.environ.get("MONGO_URL")


class Database:
    """MongoDB database"""
    _cluster = motor.AsyncIOMotorClient(mongo_url)

    # _cluster.admin.command("enableSharding", "NWordCounter")
    # _cluster.admin.command(
    #     "shardCollection", "NWordCounter.guild_users_db", key=1)

    _db = _cluster.NWordCounter
    _collection = _db["guild_users_db"]
    try:
        _cluster.admin.command('ping')
        logging.info(
            "Pinged your deployment. You successfully connected to MongoDB!")
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        logging.error(
            f"Failed to connect to MongoDB, please check settings! Error: {e}")

    @classmethod
    async def guild_in_database(cls, guild_id: int) -> bool:
        """Return True if guild is already recorded in database"""
        count = await cls._collection.count_documents(
            {"guild_id": guild_id}
        )
        return count > 0

    @classmethod
    async def create_database(cls, guild_id: int, guild_name: str) -> None:
        """Initialize guild template in database"""
        await cls._collection.insert_one(
            {
                "guild_id": guild_id,
                "guild_name": guild_name,
                "members": [],
                "settings": "[]"  # JSON string
            }
        )
        logging.info(f"Guild added! {guild_name} with id {guild_id}")

    @classmethod
    async def update_guilds(cls):
        """Update all guilds in database to have a settings field if they don't already."""
        async for doc in cls._collection.find({}):
            if "settings" not in doc:
                await cls._collection.update_one(
                    {"guild_id": doc["guild_id"]}, {
                        "$set": {
                            "settings": "[]"
                        }
                    }
                )

    @classmethod
    async def get_internal_guild_settings(cls, guild_id: int) -> list:
        """Return guild settings as a list"""
        async for doc in cls._collection.find(
            {"guild_id": guild_id}
        ):
            try:
                return json.loads(doc["settings"])
            except KeyError:
                # If the guild doesn't have a settings field, add it.
                await cls._collection.update_one(
                    {"guild_id": guild_id}, {
                        "$set": {
                            "settings": "[]"
                        }
                    }
                )
                return []

    @classmethod
    async def update_guild_settings(cls, guild_id: int, settings: list) -> None:
        """Update guild settings"""
        await cls._collection.update_one(
            {"guild_id": guild_id}, {
                "$set": {
                    "settings": json.dumps(settings)
                }
            }
        )

    @classmethod
    async def get_guild_settings(cls, guild_id: int):
        new_settings = {}
        settings = await cls.get_internal_guild_settings(guild_id)
        for setting in settings:
            new_settings[setting["int_name"]] = setting
        return new_settings

    @classmethod
    async def member_in_database(
            cls, guild_id: int, member_id: int) -> object | None:
        """Return True if member is already recorded in guild database"""
        async for doc in cls._collection.aggregate(
            [
                {
                    "$match": {
                        "guild_id": guild_id,
                        # STORED AS AN INTEGER NOT STRING.
                        "members.id": member_id
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
        ):
            return doc

    @classmethod
    async def create_member(cls, guild_id, member_id, member_name) -> None:
        """Initialize member data in guild database"""
        await cls._collection.update_one(
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

    @classmethod
    async def increment_nword_count(cls, guild_id, member_id, count) -> None:
        """Add to n-word count of person's data info in server"""
        await cls._collection.update_one(
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

    @classmethod
    async def increment_passes(cls, guild_id, member_id, count) -> None:
        """Add to user's total available n-word passes in server"""
        await cls._collection.update_one(
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

    @classmethod
    async def get_total_documents(cls) -> int:
        """Return total number of documents in database"""
        return await cls._collection.count_documents({})

    @classmethod
    async def get_nword_server_total(cls, guild_id) -> int:
        """Return integer sum of total n-words said in a server"""
        async for doc in cls._collection.aggregate(
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
        ):
            return doc["total_nwords"]

    @classmethod
    async def get_all_time_servers(cls, limit: int):
        """Return the servers with the highest recorded n-word count out of all servers"""
        out = []
        async for doc in cls._collection.aggregate(
            [
                {
                    "$unwind": "$members"
                },
                {
                    "$group": {
                        "_id": {
                            "guild_id": "$guild_id",
                            "guild_name": "$guild_name"
                        },
                        "nword_count": {"$sum": "$members.nword_count"}
                    }
                },
                {
                    "$sort": {"nword_count": -1}
                },
                {
                    "$limit": limit
                }
            ]
        ):
            out.append(doc)
        return out

    @classmethod
    async def get_all_time_counts(cls, limit: int):
        """Return the member with the highest recorded n-word count out of all servers"""
        out = []
        async for doc in cls._collection.aggregate(
            [
                {
                    "$unwind": "$members"
                },
                {
                    "$sort": {"members.nword_count": -1}
                },
                {
                    "$limit": limit
                },
                {
                    "$project": {
                        "_id": None,
                        "member": "$members.name",
                        "nword_count": "$members.nword_count"
                    }
                }
            ]
        ):
            out.append(doc)
        return out

    @classmethod
    async def get_member_list(cls, guild_id) -> list[object] | list[None]:
        """Return sorted ranked list of member objects based on n-word frequency"""
        async for doc in cls._collection.aggregate(
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
        ):
            return doc["member_object_list"]

    @classmethod
    async def cast_vote(
        cls, type: str, guild_id: int, vote_threshold: int,
        voter_id: int, votee_id: int
    ) -> None | object:
        """Insert voter id into votee's voter list in database"""
        action = None
        if type == "vote":
            action = {
                # Add vote count to user's voters.
                "$push": {"members.$.voters": voter_id}
            }
        else:
            action = {
                "$pull": {"members.$.voters": voter_id}  # Remove vote count.
            }

        # Update member object.
        voted = await cls._collection.update_one(
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
        member = await cls.member_in_database(guild_id, votee_id)
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
        cls._collection.update_one({"guild_id": guild_id, "members.id": votee_id}, set_black, upsert=False)

        return member

    # A function that returns a total count of all n-words said by everyone, everywhere.
    @classmethod
    async def get_global_nword_count(cls) -> int:
        """Return integer sum of total n-words said in all servers"""
        async for doc in cls._collection.aggregate(
            [
                {
                    "$unwind": "$members"
                },
                {
                    "$group": {
                        "_id": "global",
                        "total_nwords": {
                            "$sum": "$members.nword_count"
                        }
                    }
                }
            ]
        ):
            return doc["total_nwords"]