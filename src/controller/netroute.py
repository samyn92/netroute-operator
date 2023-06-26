from typing import Any

from client import KubernetesClient
from controller.schema.route import Route

class NetRoute:

    client = KubernetesClient()

    def __init__(self, cr: Any):
        self.name = cr['metadata']['name']
        self.namespace = cr['metadata']['namespace']
        self.spec = cr['spec']

        self.route = Route(self.spec["destination"], self.spec["gateway"])
    
    @classmethod
    def get_netroute(cls, namespace: str, name: str) -> 'NetRoute':
        cr = cls.client.get_custom_resource("dev.nitsche.io", "v1", namespace, "netroutes", name)
        return NetRoute(cr)

    @classmethod
    def list_netroutes(cls, namespace: str) -> list['NetRoute']:
        crs = cls.client.custom_api.list_namespaced_custom_object("dev.nitsche.io", "v1", namespace, "netroutes")["items"]
        return [NetRoute(cr) for cr in crs]

    # def update_spec(self, new_spec: dict[str, Any]) -> None:
    #     self.spec = new_spec
    #     self.cr["spec"] = new_spec
    #     self.client.patch_namespaced_custom_object("dev.nitsche.io", "v1", self.namespace, "netroutes", self.name, self.cr)

    @classmethod
    async def get_all_netroutes_in_cluster(cls) -> list['NetRoute']:
        namespaces = cls.client.core_api.list_namespace().items
        netroutes = []
        for ns in namespaces:
            netroutes.extend(cls.list_netroutes(ns.metadata.name))
        return netroutes
