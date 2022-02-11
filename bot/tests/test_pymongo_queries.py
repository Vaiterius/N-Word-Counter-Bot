"""Unit test pymongo queries with nested documents.

USAGE: cd bot, then py -m tests.test_pymongo_queries

- MAYBE: use mongomock instead for testing collection objects
"""
import random
import unittest
from json import load
from pathlib import Path
from pprint import pprint

import pymongo


class TestPyMongo(unittest.TestCase):
    """Test and ensure working pymongo functions before use"""

    def setUp(self):
        # Fetch token for MongoDB access.
        with Path("../config.json").open() as f:
            config = load(f)
            mongo_url = config["MONGO_URL"]

        # Initialize database for querying.
        self.cluster = pymongo.MongoClient(mongo_url)
        self.db = self.cluster["Tests"]
        self.collection = self.db["test_guild_users"]

        # Dummy guild templates - create and test diverse/different guilds.
        self.guild_template1 = {
            "guild_id": 1234,
            "guild_name": "Guild1",
            "members": []
        }
        self.guild_template2 = {
            "guild_id": 4321,
            "guild_name": "Guild2",
            "members": []
        }
        self.guild_template3 = {
            "guild_id": 1324,
            "guild_name": "Guild3",
            "members": []
        }

        # Dummy people info.
        self.test_many_members_list1 = ["John", "Jane", "Jack"]
        self.test_many_members_list2 = [
            "George", "Dominic", "Page", "Drew", "Bartholomew", "Melissa", "Pat",
            "Jackson", "Matt", "Darnelius", "Kristin", "Leo", "Ruby", "Noah"
        ]
    

    def tearDown(self):
        self.collection.delete_one({"guild_id": self.guild_template1["guild_id"]})
        self.collection.delete_one({"guild_id": self.guild_template2["guild_id"]})
        self.collection.delete_one({"guild_id": self.guild_template3["guild_id"]})
        # pass


    def test_guild_creation(self):
        self.collection.insert_one(self.guild_template1)
        found_guild1 = self.collection.find_one(self.guild_template1)
        self.assertTrue(found_guild1)


    def test_guild_with_many_members(self):
        self.collection.insert_one(self.guild_template2)

        # Insert sample members into newly-created guild.
        for member in self.test_many_members_list1:
            self.collection.update_one(
                {"guild_id": self.guild_template2["guild_id"]}, {
                    "$push": {
                        "members": {
                            "name": member,
                            "votes": 0,
                            "is_black": False
                        }
                    }
                }
            )
        
        found_guild2 = self.collection.find_one({"guild_id": self.guild_template2["guild_id"]})
        self.assertTrue(found_guild2)

        num_members = len(found_guild2["members"])
        self.assertEqual(num_members, len(self.test_many_members_list1))
    

    def test_update_member_info(self):
        self.collection.insert_one(self.guild_template3)
        for member in self.test_many_members_list2:
            self.collection.update_one(
                {"guild_id": self.guild_template3["guild_id"]}, {
                    "$push": {
                        "members": {
                            "name": member,
                            "votes": random.randint(0, 5),
                            "is_black": random.choice([True, False])
                        }
                    }
                }
            )
        
        found_guild3 = self.collection.find_one({"guild_id": self.guild_template3["guild_id"]})
        self.assertTrue(found_guild3), "Guild3 does not exist"

        num_members = len(found_guild3["members"])
        self.assertEqual(num_members, len(self.test_many_members_list2)), "Number of members added incorrect"

        # Find and update specific member's data.
        name_to_find = random.choice(self.test_many_members_list2)
        print(f"Name to find: {name_to_find}")
        changed_name = "Timothy"
        self.collection.update_one(
            {
                "members.name": name_to_find
            },
            {
                "$set": {
                    "members.$.name": changed_name
                }
            },
            upsert=False
        )

        # Find and return specific member's data.
        # Thank you YuTing from StackOverflow for helping me with this.
        pipeline = [
            {
                "$match": {
                    "guild_id": self.guild_template3["guild_id"],
                    "members.name": changed_name
                }
            },
            {
                "$unwind": "$members"
            },
            {
                "$match": {"members.name": changed_name}
            },
            {
                "$replaceWith": "$members"
            }
        ]
        name_found = self.collection.aggregate(pipeline).next()
        pprint(name_found)
        self.assertEqual(changed_name, name_found["name"]), f"{name_to_find} does not equal {name_found['name']}"


    #


if __name__ == "__main__":
    unittest.main()
