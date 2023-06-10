from typing import Callable
import os

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream


class KubernetesClient:
    USE_INCLUSTER = os.environ.get('USE_INCLUSTER')

    if USE_INCLUSTER:
        config.load_incluster_config()
    else:
        config.load_kube_config()
    try:
        c = Configuration().get_default_copy()
    except AttributeError:
        c = Configuration()
        c.assert_hostname = False
    Configuration.set_default(c)
    api = core_v1_api.CoreV1Api()

    def __init__(self, namespace: str, pod: str):
        self.namespace = namespace
        self.pod = pod

    def __enter__(self) -> Callable:
        return self.exec_commands

    def __exit__(self, type, value, traceback):
        pass

    def patch_annotation(self, annotation: dict):
        self.api.patch_namespaced_pod(self.pod, self.namespace, body={ "metadata": {"annotations": annotation}})

    def exec_commands(
        self,
        commands: list
    ):
        resp = None
        try:
            resp = self.api.read_namespaced_pod(name=self.pod, namespace=self.namespace)
        except ApiException as e:
            if e.status != 404:
                print("Unknown error: %s" % e)
                exit(1)

        if not resp:
            print(f"Pod {self.namespace}/{self.pod} does not exist.")

        commands = [ cmd+"\n" for cmd in commands ]
        commands.insert(0, "/bin/sh")
        commands.insert(1, "-c")
        

        # Calling exec and waiting for response
        resp = stream(
            self.api.connect_get_namespaced_pod_exec,
            self.pod,
            self.namespace,
            command=commands,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        
        return resp
