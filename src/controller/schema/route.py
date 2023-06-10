import ipaddress
from typing import Union
from dataclasses import dataclass

@dataclass
class Route:
    """Class representing a Route."""

    network: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
    gateway: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]

    def __init__(self, network, gateway):
        self.network = ipaddress.ip_network(network)
        self.gateway = ipaddress.ip_address(gateway)

    def __str__(self):
        return f"{self.network} -> {self.gateway}"

    def __eq__(self, other):
        return self.network == other.network and self.gateway == other.gateway

    @property
    def version(self) -> int: 
        """Returns IP version of a Route"""
        return self.gateway.version

    def serialize_add_cmd(self) -> str:
        """Serializes the string representation of the Route add command."""
        return f"ip route add {self.network} via {self.gateway}"

    def serialize_delete_cmd(self) -> str:
        """Serializes the string representation of the Route delete command."""
        return f"ip route delete {self.network} via {self.gateway}"

    @classmethod
    def deserialize_v4_route(cls, route_entry: str):
        """Deserializes the single line string representation of a Route."""
        network = f"{route_entry.split()[0]}/{route_entry.split()[2]}"
        gateway = route_entry.split()[1]

        return cls(network, gateway)

    @classmethod
    def deserialize_v6_route(cls, route_entry: str):
        """Deserializes the single line string representation of a ipv6 Route."""
        network = f"{route_entry.split()[0]}"
        gateway = route_entry.split()[1]

        return cls(network, gateway)

    
@dataclass
class RouteMissingError(Exception):
    """Custom error that is raised when a route is missing in a routing table."""

    network: str
    gateway: str
    message: str = "Route is missing."


@dataclass
class RouteExistingError(Exception):
    """Custom error that is raised when a route is existing."""

    network: str
    gateway: str
    message: str = "Route is existing."
