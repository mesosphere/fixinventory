import fixlib.logger
import os
import ntnx_prism_py_client
import ntnx_clustermgmt_py_client
import ntnx_vmm_py_client

from ntnx_prism_py_client import Configuration as PrismConfiguration
from ntnx_prism_py_client import ApiClient as PrismClient

from ntnx_clustermgmt_py_client import Configuration as ClusterConfiguration
from ntnx_clustermgmt_py_client import ApiClient as ClusterClient

from ntnx_vmm_py_client import Configuration as VMMConfiguration
from ntnx_vmm_py_client import ApiClient as VMMClient

from attrs import define, field
from datetime import datetime
from typing import ClassVar, Dict, List, Optional
from fixlib.baseplugin import BaseCollectorPlugin
from fixlib.graph import ByNodeId, Graph, EdgeType, BySearchCriteria
from fixlib.args import ArgumentParser
from fixlib.config import Config
from fixlib.baseresources import (
    BaseAccount,
    BaseRegion,
    BaseInstance,
    BaseNetwork,
    BaseResource,
    BaseVolume,
    InstanceStatus,
    VolumeStatus,
)

log = fixlib.logger.getLogger("fix." + __name__)


class NutanixCollectorPlugin(BaseCollectorPlugin):
    # The cloud attribute is used to identify the cloud provider in the fix data model
    # The BaseCollectorPlugin will use this create a new cloud node in the graph
    cloud = "nutanix"

    def collect(self) -> None:
        """This method is being called by fix whenever the collector runs

        It is responsible for querying the cloud APIs for remote resources and adding
        them to the plugin graph.
        The graph root (self.graph.root) must always be followed by one or more
        accounts. An account must always be followed by a region.
        A region can contain arbitrary resources.
        """
        log.debug("plugin: collecting nutanix resources")

        sherlockDev = PrismCentral(id="sherlock_dev", name="Sherlock Dev", tags={"url": "https://prismcentral.dev.ntnxsherlock.com:9440/"})
        self.graph.add_resource(self.graph.root, sherlockDev)

        bowser = PrismElement(id="bowser", name="bowser", tags={"Some Tag": "Some Value"})
        self.graph.add_resource(sherlockDev, bowser)
        self.collect_virtual_machines()
        log.info(f"graph: {self.graph.export_model()}")

    @staticmethod
    def add_args(arg_parser: ArgumentParser) -> None:
        """Example of how to use the ArgumentParser

        Can be accessed via ArgumentParser.args.example_arg
        Note: almost all plugin config should be done via add_config()
        so it can be changed centrally and at runtime.
        """
        #        arg_parser.add_argument(
        #            "--example-arg",
        #            help="Example Argument",
        #            dest="example_arg",
        #            type=str,
        #            default=None,
        #            nargs="+",
        #        )
        pass

    @staticmethod
    def add_config(config: Config) -> None:
        """Add any plugin config to the global config store.

        Method called by the PluginLoader upon plugin initialization.
        Can be used to introduce plugin config arguments to the global config store.
        """
        #        config.add_config(ExampleConfig)
        pass
    
    def collect_virtual_machines(self) -> None:
        """Example of how to collect resources in a region"""
        # Get all virtual machines in the PE
        vmmClient = vmm_client("prismcentral.dev.ntnxsherlock.com", False)
        vmm_instance = ntnx_vmm_py_client.api.VmApi(vmmClient)
        print("\nGet all virtual machines in the PE\n")
        response = vmm_instance.list_vms()
        log.info(f"Found virtual machines: {response.metadata.total_available_results}")
        for vm in response.data:
            log.info(f"VM: {vm.name}" f", uuid: {vm.ext_id}" f", power_state: {vm.power_state}" f", create_time: {vm.create_time}")
            
        


@define
class ExampleConfig:
    """Example of how to use the fixcore config service

    Can be accessed via Config.example.region
    """

    kind: ClassVar[str] = "example"
    region: Optional[List[str]] = field(default=None, metadata={"description": "Example Region"})


@define(eq=False, slots=False)
class PrismCentral(BaseAccount):
    """Prism Central Account"""

    kind: ClassVar[str] = "prism_central"

    def delete(self, graph: Graph) -> bool:
        return NotImplemented


@define(eq=False, slots=False)
class PrismElement(BaseRegion):
    """Prism Element"""

    kind: ClassVar[str] = "prism_element"

    def delete(self, graph: Graph) -> bool:
        """PEs can usually not be deleted so we return NotImplemented"""
        return NotImplemented


@define(eq=False, slots=False)
class NutanixResource(BaseResource):
    """A class that implements the abstract method delete() as well as update_tag()
    and delete_tag().

    delete() must be implemented. update_tag() and delete_tag() are optional.
    """

    kind: ClassVar[str] = "nutanix_resource"
    kind_display: ClassVar[str] = "Nutanix Resource"

    def delete(self, graph: Graph) -> bool:
        """Delete a resource in the cloud"""
        log.debug(f"Deleting resource {self.id} in account {self.account(graph).id} region {self.region(graph).id}")
        return True

    def update_tag(self, key, value) -> bool:
        """Update a resource tag in the cloud"""
        log.debug(f"Updating or setting tag {key}: {value} on resource {self.id}")
        return True

    def delete_tag(self, key) -> bool:
        """Delete a resource tag in the cloud"""
        log.debug(f"Deleting tag {key} on resource {self.id}")
        return True


@define(eq=False, slots=False)
class NutanixVMs(NutanixResource):
    """An Example Instance Resource"""

    kind: ClassVar[str] = "ViMachines"



def prism_client(endpoint: str, insecure: bool) -> PrismClient:
  prism_config = PrismConfiguration()
  prism_config.host = endpoint
  prism_config.verify_ssl = not insecure
  prism_config.username = os.environ.get("NUTANIX_USER")
  prism_config.password = os.environ.get("NUTANIX_PASSWORD")
  prism_client = PrismClient(configuration=prism_config)
  prism_client.add_default_header(
            header_name="Accept-Encoding", header_value="gzip, deflate, br"
        )
  prism_client.add_default_header(header_name="Content-Type", header_value="application/json")
  return prism_client


def cluster_client(endpoint: str, insecure: bool) -> ClusterClient:
    cluster_config = ClusterConfiguration()
    cluster_config.host = endpoint
    cluster_config.verify_ssl = not insecure
    cluster_config.username = os.getenv("NUTANIX_USER")
    cluster_config.password = os.getenv("NUTANIX_PASSWORD")
    cluster_client = PrismClient(configuration=cluster_config)
    cluster_client.add_default_header(
        header_name="Accept-Encoding", header_value="gzip, deflate, br"
    )
    cluster_client.add_default_header(header_name="Content-Type", header_value="application/json")
    return cluster_client

def vmm_client(endpoint: str, insecure: bool) -> VMMClient:
    vmm_config = VMMConfiguration()
    vmm_config.host = endpoint
    vmm_config.port = 9440
    vmm_config.verify_ssl = not insecure
    vmm_config.username = os.getenv("NUTANIX_USER")
    vmm_config.password = os.getenv("NUTANIX_PASSWORD")
    vmm_client = VMMClient(configuration=vmm_config)
    vmm_client.add_default_header(
        header_name="Accept-Encoding", header_value="gzip, deflate, br"
    )
    vmm_client.add_default_header(header_name="Content-Type", header_value="application/json")
    return vmm_client