import os
from typing import Any
from kubernetes import client, config, stream

class KubernetesClient:
    """
    Wrapper class for Kubernetes API client that provides methods to interact with the API.
    """
    def __init__(self):
        USE_INCLUSTER = os.environ.get('USE_INCLUSTER')

        if USE_INCLUSTER:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.core_api: client.CoreV1Api = client.CoreV1Api()
        self.custom_api: client.CustomObjectsApi = client.CustomObjectsApi()

    def get_custom_resource(self, group: str, version: str, namespace: str, plural: str, name: str) -> dict[str, Any]:
        return self.custom_api.get_namespaced_custom_object(group, version, namespace, plural, name)

    def exec_command(self, pod_name: str, pod_namespace: str, command: str) -> str:
        exec_command = [
            '/bin/sh',
            '-c',
            command]
        resp = stream.stream(self.core_api.connect_get_namespaced_pod_exec,
                             pod_name,
                             pod_namespace,
                             command=exec_command,
                             stderr=True, stdin=False,
                             stdout=True, tty=False)
        return resp