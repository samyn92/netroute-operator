from __future__ import annotations
from typing import Any
from contextlib import suppress

from controller.pod_config import PodConfig, PodConfigType
from controller.routing import CurrentRouting, DesiredRouting


class Pod:
    """Class representing a K8s Pod which holds current and desired config"""

    PODS: dict[tuple[str, str], Pod] = {}

    def __init__(self, namespace: str, name: str):
        self.namespace = namespace
        self.name = name

        self.current_routes = CurrentRouting(
            v4_routes=[], v6_routes=[], pod_name=self.name, pod_namespace=self.namespace
        )
        self.desired_routes = DesiredRouting(v4_routes=[], v6_routes=[])

        self.current_config: dict[PodConfigType, PodConfig] = {
            "IPV4_ROUTES": self.current_routes.v4_routes,
            "IPV6_ROUTES": self.current_routes.v6_routes,
        }

        self.desired_config: dict[PodConfigType, PodConfig] = {
            "IPV4_ROUTES": self.desired_routes.v4_routes,
            "IPV6_ROUTES": self.desired_routes.v6_routes,
        }
        self.PODS[((namespace, name))] = self

    def __repr__(self):
        return f"Pod({self.namespace}, {self.name})"

    @classmethod
    def from_name(cls, namespace: str, name: str) -> Pod:
        return cls.PODS.get((namespace, name)) or cls(namespace, name)


    def refresh_current_routes(fn):
        def wrapper(self, *args, **kwargs):
            self.current_routes.get_config()
            return fn(self, *args, **kwargs)
        return wrapper


    @refresh_current_routes
    def add_desired_routes(self, config: PodConfig) -> None:
        self.desired_routes.add_config(config)
        if config not in self.current_routes:
            self.current_routes.add_config(config)

    @refresh_current_routes
    def remove_desired_routes(self, config: PodConfig, prune: bool) -> None:
        with suppress(ValueError):
            self.desired_routes.remove_config(config)
        if prune:
            self.current_routes.remove_config(config)

    @refresh_current_routes
    def reconcile_routes(self) -> None:
        for config in self.desired_routes:
            if config not in self.current_routes:
                self.current_routes.add_config(config)
