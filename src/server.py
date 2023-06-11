import asyncio

import kopf

from controller.pod import Pod
from k8s import KubernetesClient
from controller.schema.route import Route, RouteExistingError, RouteMissingError

OBSERVED: set[list[tuple]] = set([])

@kopf.on.startup()
async def startup_fn(logger, **kwargs):
    logger.info("netroute-operator started.. checking states")
    #TODO: Implement state reconciliation of existing netroutes

@kopf.on.create("pods")
async def create_pod(name, namespace, logger, **kwargs):
    await asyncio.sleep(3)
    logger.info(f"Checking for Pod({namespace}/{name})")
    if ((namespace, name)) in OBSERVED:
        logger.info(f"Watched created Pod({namespace}, {name}")
        pod = Pod.from_name(namespace, name)
        pod.reconcile("IPV4_ROUTES")
        logger.info(
            f"Reconciled {pod} to {pod.get_current_podconfigs('IPV4_ROUTES').get_config()}"
        )


@kopf.on.create("netroutes")
async def create_route(spec, logger, annotations, patch, **kwargs):
    await asyncio.sleep(1)
    namespace, pod_name = spec["targetNamespace"], spec["targetPod"]
    network, gateway = spec["network"], spec["gateway"]
    pod = Pod.from_name(namespace, pod_name)
    OBSERVED.add((namespace, pod_name))
    logger.info(f"Currently observed {', '.join([str(item) for item in OBSERVED])}")
    logger.info(
        f"Request to create Route {network} -> {gateway} on {namespace} / {pod_name}"
    )

    try:
        route = Route(network, gateway)
        pod.add_desired_routes(config=route)
    except RouteMissingError:
        logger.warning(f"New Route {network} -> {gateway} existing")
    except Exception as e: 
        logger.error(f"New Route {network} -> {gateway} couldn't be added!")
        logger.error(e)
    else:
        logger.info(
            f"New Route {network} -> {gateway} successfully created on Pod {namespace} / {pod_name}"
        )
    finally:
        logger.debug(f"Current routes: {pod.current_routes}")

        return {
            "ready": str(True),
            "route": str(route),
            "applied_to": str(pod),
        }


@kopf.on.delete("netroutes")
async def delete_route(spec, logger, **kwargs):
    await asyncio.sleep(1)
    namespace, pod_name = spec["targetNamespace"], spec["targetPod"]
    network, gateway = spec["network"], spec["gateway"]
    pod = Pod.from_name(namespace, pod_name)

    OBSERVED.discard((namespace, pod_name))

    logger.info(f"Currently observed {', '.join([str(item) for item in OBSERVED])}")

    logger.info(
        f"Request to remove Route (prune={spec['prune']}) {network} -> {gateway} from Pod {namespace} / {pod_name}"
    )
    try:
        route = Route(network, gateway)
        pod.remove_desired_routes(
            prune=spec["prune"], config=route
        )
    except RouteMissingError:
        logger.warning(
            f"Existing Route {network} -> {gateway} not found, couldn't remove"
        )
    except RouteExistingError:
        logger.warning(
            f"Existing Route {network} -> {gateway} was not deleted successfully"
        )
    else:
        logger.info(
            f"Existing Route {network} -> {gateway} successfully deleted from Pod {namespace} / {pod_name}"
        )
    finally:
        logger.debug(f"Current routes: {pod.current_routes}")
