import unittest

from src.controller.schema.route import Route


class TestRouteSchema(unittest.TestCase):

    def test_successful_init_v4_route(self):
        assert type(Route("192.168.100.0/24", "192.168.100.1")) is Route

    def test_successful_init_v6_route(self):
        assert type(Route("::/0", "2a01:598:400:40a1:10:125:41:49")) is Route

    def test_successful_init_vpp_route(self):
        assert type(Route("192.168.100.0/24", "192.168.100.1")) is Route
        assert type(Route("::/0", "2a01:598:400:40a1:10:125:41:49")) is Route

    def test_bad_route(self):
        assert type(Route("192.168.100.0/24", "192.168.100.1")) is Route
        assert type(Route("::/0", "2a01:598:400:40a1:10:125:41:49")) is Route

        # bad routes
        with self.assertRaises(ValueError):
            assert Route("::/0", ":999999:")
            assert Route("ff999::1/64", "::")
            assert Route("vyxasf", "yxcvas")

