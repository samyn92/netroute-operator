from abc import ABC, abstractmethod
from enum import Enum, auto

class PodConfigType(Enum):
    IPV4_ROUTES = auto()
    IPV6_ROUTES = auto()
    VPP_ROUTES = auto()


class PodConfig(ABC):
    """Abstract Class representing a PodConfig entity"""

    @abstractmethod
    def get_config(self):
        pass

    @abstractmethod
    def add_config(self):
        pass

    @abstractmethod
    def remove_config(self):
        pass
