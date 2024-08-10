import logging
from typing import ClassVar, Dict, List, Optional, Tuple, Any
from attrs import define
from fixlib.baseresources import BaseAccount, BaseResource, ModelReference
from fixlib.graph import Graph

log = logging.getLogger("fix." + __name__)


@define(eq=False, slots=False)
class PrismCentralAccount(BaseAccount):
    """PrismCentral Account"""

    kind: ClassVar[str] = "prismcenteral_account"
    kind_display: ClassVar[str] = "Prism Central"
    kind_description: ClassVar[str] = (
        "Prism Central is a multi-cluster management solution that enables you to manage multiple Nutanix clusters "
    )
    reference_kinds: ClassVar[ModelReference] = {
        "successors": {
            "default": [
                "prism_element",
            ],
            "delete": [],
        }
    }
    endpoint: str
    username: str
    password: str
    port: Optional[str] = "9440"
    insecure: Optional[bool] = False


@define(eq=False, slots=False)
class PrismElement(BaseResource):
    """Prism Element"""

    kind: ClassVar[str] = "prism_element"
    kind_display: ClassVar[str] = "Prism Element"
    kind_description: ClassVar[str] = (
        "A Nutanix Prism Element is like a region in public clouds"
    )
    reference_kinds: ClassVar[ModelReference] = {
        "successors": {
            "default": [
                "virtual_machine",
            ],
            "delete": [],
        }
    }

    def delete(self, graph: Graph) -> bool:
        """PEs can usually not be deleted so we return NotImplemented"""
        return NotImplemented


@define(eq=False, slots=False)
class ViraualMachine(BaseResource):
    kind: ClassVar[str] = "virtual_machine"
    kind_display: ClassVar[str] = "Virtual Machine"
    kind_description: ClassVar[str] = "A virtual machine in Nutanix"
    reference_kinds: ClassVar[ModelReference] = {
        "predecessors": {
            "default": ["prism_element"],
            "delete": [],
        }
    }
    power_state: str

    def delete(self, graph: Graph) -> bool:
        log.info(f"delete virtual machine {self.id}: {self.name}")
        return NotImplemented
