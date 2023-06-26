from typing import Any
import logging

from client import KubernetesClient
from controller.schema.route import Route, RouteMissingError, RouteExistingError
from controller.netroute import NetRoute

logger = logging.getLogger(__name__)

class Pod:

    client = KubernetesClient()

    def __init__(self, manifest: dict[str, Any]) -> None:
        self.metadata = manifest.metadata
        self.name = self.metadata.name
        self.namespace = self.metadata.namespace
    
        self.spec = manifest.spec

    def __str__(self):
        return f"Pod({self.namespace}/{self.name})"
    
    @classmethod
    def get_pod(cls, namespace: str, name: str) -> 'Pod':
        pod = cls.client.core_api.read_namespaced_pod(name, namespace)
        return cls(pod)
    
    @classmethod
    def list_pods(cls, namespace: str) -> list['Pod']:
        pods = cls.client.core_api.list_namespaced_pod(namespace).items
        return [Pod(pod) for pod in pods]
    
    @classmethod
    def list_all_observed_pods(cls) -> list['Pod']:
        pods = cls.list_pods(namespace='')
        return [pod for pod in pods if pod.is_observed_by_netroute]
    
    @property
    def is_observed_by_netroute(self) -> bool:
        netroutes = NetRoute.list_netroutes(self.namespace)
        for netroute in netroutes:
            if netroute.spec.get('targetPod') == self.name and netroute.spec.get('targetNamespace') == self.namespace:
                return True
        return False
    
    async def annotate_pod_with_netroute(self, netroute: NetRoute) -> None:
        netroute_annotation = self.metadata.annotations.get('netroute', '')
        netroute_list = netroute_annotation.split(',') if netroute_annotation else []
        if f'{netroute.name}@{netroute.namespace}' not in netroute_list:
            netroute_list.append(f'{netroute.name}@{netroute.namespace}')
        netroute_annotation = ','.join(netroute_list)
        body = {
            'metadata': {
                'annotations': {
                    'netroute': netroute_annotation,
                },
            },
        }
        self.client.core_api.patch_namespaced_pod(name=self.name, namespace=self.namespace, body=body)
        logger.info(f"Annotated Pod {self.name} in namespace {self.namespace} with NetRoute {netroute.name} in namespace {netroute.namespace}.")

    async def remove_netroute_annotation_from_pod(self, netroute: NetRoute) -> None:
        netroute_annotation = self.metadata.annotations.get('netroute', '')
        netroute_list = netroute_annotation.split(',') if netroute_annotation else []
        if f'{netroute.name}@{netroute.namespace}' in netroute_list:
            netroute_list.remove(f'{netroute.name}@{netroute.namespace}')
        netroute_annotation = ','.join(netroute_list)
        body = {
            'metadata': {
                'annotations': {
                    'netroute': netroute_annotation,
                },
            },
        }
        self.client.core_api.patch_namespaced_pod(name=self.name, namespace=self.namespace, body=body)
        logger.info(f"Removed NetRoute {netroute.name} in namespace {netroute.namespace} annotation from Pod {self.name} in namespace {self.namespace}")
      
    @classmethod
    async def handle_netroute_on_startup(cls, netroute: NetRoute) -> None:
        target_pod_name = netroute.spec.get('targetPod')
        target_pod_namespace = netroute.spec.get('targetNamespace')

        pod = cls.get_pod(target_pod_namespace, target_pod_name)
        await pod.annotate_pod_with_netroute(netroute)      

    @staticmethod
    def deserialize_routing_table(routing_table: str, ip_version: int):
        """Deserializes the string representation of the routing table"""
        fn = Route.deserialize_v4_route if ip_version == 4 else Route.deserialize_v6_route
        return [
            fn(route)
            for route in reversed(routing_table.splitlines())
            if not (route.startswith("Destination")) and not (route.startswith("Kernel"))
        ]
    
    def get_routes(self):
        """Gets routes from a Pod via `route -n` and `route -A inet6 -n`"""
        self.routes = []
        self.routes.extend(self.deserialize_routing_table(self.client.exec_command(self.name, self.namespace, "route -n"), 4))
        self.routes.extend(self.deserialize_routing_table(self.client.exec_command(self.name, self.namespace, "route -A inet6 -n"), 6))

    def add_route(self, route: Route) -> None:
        """Adds a route to a Pod. If a route is already existing or the route was not successfully added an Exception is raised"""
        self.get_routes()
        if route not in self.routes:
            self.client.exec_command(self.name, self.namespace, command=route.serialize_add_cmd())
            self.get_routes()
            if not route in self.routes:
                raise RouteMissingError(route.network, route.gateway)

    def remove_route(self, route: Route) -> None:
        """Removes a route from a Pod. If a route is not existing or the route was not successfully removed an Exception is raised"""
        self.get_routes()
        if route not in self.routes:
            raise RouteMissingError(route.network, route.gateway)
        self.client.exec_command(self.name, self.namespace, command=route.serialize_delete_cmd())
        self.get_routes()
        if route in self.routes:
            raise RouteExistingError(route.network, route.gateway)
