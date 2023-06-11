import ipaddress
from dataclasses import dataclass

from k8s import KubernetesClient
from controller.schema.route import Route, RouteExistingError, RouteMissingError
from controller.pod_config import PodConfig

@dataclass
class Routing(PodConfig):
    
    v4_routes: list[Route]
    v6_routes: list[Route]

    def __iter__(self):
        yield from self.v4_routes
        yield from self.v6_routes

    def __contains__(self, route: Route):
        return route in self.v4_routes or route in self.v6_routes

    def get_config(self) -> list[Route]:
        pass

    def add_config(self) -> None:
        pass

    def remove_config(self) -> None:
        pass

@dataclass
class DesiredRouting(Routing):

    def get_config(self) -> list[Route]:
        return [*self.v4_routes, *self.v6_routes]

    def add_config(self, route: Routing) -> None:
        if route.version == 4:
            self.v4_routes.append(route)
        elif route.version == 6:
            self.v6_routes.append(route)

    def remove_config(self, route: Routing) -> None:
        if route.version == 4:
            self.v4_routes.remove(route)
        elif route.version == 6:
            self.v6_routes.remove(route)

@dataclass
class CurrentRouting(Routing):
    """Class representing the current state of PodConfig - Routing. Methods are using Exec API"""

    pod_name: str
    pod_namespace: str

    def get_config(self) -> list[Route]:
        """Gets all current routes from a pod."""
        with KubernetesClient(self.pod_namespace, self.pod_name) as pod_exec:
            self.v4_routes = self.deserialize_routing_table(pod_exec(["route -n"]), 4)
            self.v6_routes = self.deserialize_routing_table(pod_exec(["route -A inet6 -n"]), 6)
        return [*self.v4_routes, *self.v6_routes]

    def add_config(self, route: Routing) -> None:
        """Adds a route to a Pod. If a route is already existing or the route was not successfully added an Exception is raised."""
        if route not in self.v4_routes or route not in self.v6_routes:
            with KubernetesClient(self.pod_namespace, self.pod_name) as pod_exec:
                pod_exec([route.serialize_add_cmd()])
            self.get_config()
            if not route in self.v4_routes or route in self.v6_routes:
                raise RouteMissingError(route.network, route.gateway)

    def remove_config(self, route: Routing) -> None:
        """Removes a route from a Pod. If a route is not existing or the route was not successfully removed an Exception is raised."""
        if route not in [*self.v4_routes, *self.v6_routes]:
            raise RouteMissingError(route.network, route.gateway)
        with KubernetesClient(self.pod_namespace, self.pod_name) as pod_exec:
            pod_exec([route.serialize_delete_cmd()])
        self.get_config()
        if route in self.v4_routes or route in self.v6_routes:
            raise RouteExistingError(route.network, route.gateway)

    @staticmethod
    def deserialize_routing_table(routing_table: str, ip_version: int):
        """Deserializes the string representation of the routing table"""
        fn = Route.deserialize_v4_route if ip_version == 4 else Route.deserialize_v6_route
        return [
            fn(route)
            for route in reversed(routing_table.splitlines())
            if not (route.startswith("Destination")) and not (route.startswith("Kernel"))
        ]
