import unittest
from src import __version__

class TestPods(unittest.TestCase):

    def test_version(self):
        assert __version__ == "0.1.2"