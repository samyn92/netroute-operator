from typing import Any
import logging

import kopf
from kubernetes.client.exceptions import ApiException

from client import KubernetesClient
from controller.pod import Pod
from controller.netroute import NetRoute
from controller.schema.route import RouteExistingError, RouteMissingError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@kopf.on.startup()
async def on_startup(**kwargs) -> None:
    logger.info("Operator has started!")
    global client
    client = KubernetesClient()
    
    netroutes = await NetRoute.get_all_netroutes_in_cluster()
    try:
        for netroute in netroutes:
            await Pod.handle_netroute_on_startup(netroute)
    except ApiException:
        target_pod_name = netroute.spec.get('targetPod')
        target_pod_namespace = netroute.spec.get('target_pod_namespace')
        logger.warning(f"Pod {target_pod_namespace}/{target_pod_name} doesn't exists.")


@kopf.on.cleanup()
async def on_cleanup(**kwargs) -> None:
    pods = Pod.list_all_observed_pods()
    for pod in pods:
        await pod.remove_netroute_annotation_from_pod(pod)


@kopf.on.create("pods")
async def pod_observer(namespace: str, name: str, **kwargs) -> None:
    pod = Pod.get_pod(namespace, name)
    
    if pod.is_observed_by_netroute:
        netroutes = NetRoute.list_netroutes(namespace)
        for netroute in netroutes:
            if netroute.spec.get('targetPod') == name and netroute.spec.get('targetNamespace') == namespace:
                await pod.annotate_pod_with_netroute(netroute)


@kopf.on.create("dev.nitsche.io", "v1", "netroutes")
async def netroute_creation_handler(namespace: str, name: str, spec: dict[str, Any], **kwargs) -> None:
    netroute = NetRoute.get_netroute(namespace, name)

    target_pod_name = spec.get('targetPod')
    target_pod_namespace = spec.get('targetNamespace')
    logger.info(f"Received request to create NetRoute {namespace}/{name} on Pod {target_pod_namespace}/{target_pod_name}.")

    try:
        pod = Pod.get_pod(target_pod_namespace, target_pod_name)
        await pod.annotate_pod_with_netroute(netroute)
        pod.add_route(netroute.route)
    except ApiException:
        logger.error(f"Pod {target_pod_namespace}/{target_pod_name} doesn't exists.")
    except RouteExistingError:
        logger.error(f"Pod {target_pod_namespace}/{target_pod_name} doesn't have NetRoute {namespace}/{name} configured.")
    else:
        logger.info(f"NetRoute {namespace}/{name} on Pod {target_pod_namespace}/{target_pod_name} successfully created.")

        return {
            "ready": True,
            "route": str(netroute.route),
            "applied_to": str(pod)
        }

@kopf.on.delete("dev.nitsche.io", "v1", "netroutes")
async def netroute_deletion_handler(namespace: str, name: str, spec: dict[str, Any], **kwargs) -> None:
    target_pod_name = spec.get('targetPod')
    target_pod_namespace = spec.get('targetNamespace')
    netroute = NetRoute.get_netroute(namespace, name)
    logger.info(f"Received request to delete NetRoute {namespace}/{name} on Pod {target_pod_namespace}/{target_pod_name}.")

    try:
        pod = Pod.get_pod(target_pod_namespace, target_pod_name)
        await pod.remove_netroute_annotation_from_pod(netroute)
        pod.remove_route(netroute.route)
    except ApiException:
        logger.error(f"Pod {target_pod_namespace}/{target_pod_name} doesn't exists.")
    except RouteMissingError:
        logger.error(f"Pod {target_pod_namespace}/{target_pod_name} doesn't have NetRoute {namespace}/{name} configured.")
    else:
        logger.info(f"NetRoute {namespace}/{name} with target Pod {target_pod_namespace}/{target_pod_name} successfully deleted.")
