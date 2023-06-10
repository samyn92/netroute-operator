import unittest
import warnings

from src.controller.pod import Pod
from src.controller.schema.route import Route
from src.controller.schema.route import RouteMissingError



route = Route(network="192.168.101.0/24", gateway="10.1.0.1")
bad_route = Route(network="192.168.102.0/24", gateway="10.2.0.1")

pod = Pod.from_name("default", "busybox-test")

def test_success_create_route(self):
    self.pod.add_desired_routes(config=self.route)
    assert self.route in self.pod.current_routes

def test_success_remove_route_prune(self):
    self.pod.add_desired_routes(config=self.route)
    self.pod.remove_desired_routes(config=self.route, prune=True)
    assert self.route not in self.pod.current_routes

def test_success_remove_route_noprune(self):
    self.pod.remove_desired_routes(config=self.route, prune=False)
    assert self.route in self.pod.current_routes

def test_fail_create_route(self):
    warnings.simplefilter("ignore", ResourceWarning)
    with self.assertRaises(RouteMissingError) as context:
        self.pod.add_desired_routes(config=self.bad_route)
    self.assertTrue(context.exception)

def test_fail_remove_route_nonexisting(self):
    warnings.simplefilter("ignore", ResourceWarning)
    with self.assertRaises(RouteMissingError) as context:
        self.pod.remove_desired_routes(config=self.bad_route, prune=True)
    self.assertTrue(context.exception)

def test_fail_remove_route_existing(self):
    warnings.simplefilter("ignore", ResourceWarning)
    with self.assertRaises(RouteMissingError) as context:
        self.pod.remove_desired_routes(config=self.bad_route, prune=True)
    self.assertTrue(context.exception)

