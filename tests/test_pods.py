import unittest

from src.controller.pod import Pod


class TestPods(unittest.TestCase):
       
    def test_pod(self):
        assert type(Pod("default", "busybox-test")) is Pod
