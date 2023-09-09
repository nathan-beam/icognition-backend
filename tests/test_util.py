import unittest
from app.icog_util import remove_stop_words


class TestUtil(unittest.TestCase):

    def test_remove_stop_words(self):
        text = "Nick likes to play football however he is not too fond of tennis"
        answer = "Nick likes play football however fond tennis"
        assert (remove_stop_words(text) == answer)


if __name__ == '__main__':
    unittest.main()
