"""Unit test the n-word counter function with various text"""
import unittest
from . import bot
from bot.cogs import nword_counter


class TestNWordOccurrences(unittest.TestCase):
    """Tests for the staticmethod count_nwords()"""

    def setUp(self):
        self.count_nwords = nword_counter.NWordCounter.count_nwords
    
    def test_nwords(self):
        pass
        # self.assertEqual(self.count_nwords(words), 3), "Should be equal to 3"


if __name__ == "__main__":
    unittest.main()
