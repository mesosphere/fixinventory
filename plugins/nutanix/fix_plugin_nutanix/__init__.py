import fixlib.logger
import os

from ntnx_clustermgmt_py_client import Configuration as ClusterConfiguration
from ntnx_clustermgmt_py_client import ApiClient as ClusterClient

from ntnx_vmm_py_client import Configuration as VMMConfiguration
from ntnx_vmm_py_client import ApiClient as VMMClient

from attrs import define, field
from typing import List, Optional, cast
from fixlib.baseplugin import BaseCollectorPlugin
from fixlib.graph import Graph
from fixlib.args import ArgumentParser
from fixlib.config import Config

from fix_plugin_nutanix.collector import PrismCentralCollector
from fix_plugin_nutanix.resources import PrismCentralAccount
from fix_plugin_nutanix.config import PrismCentalCredentials, PrismCentralColletorConfig

log = fixlib.logger.getLogger("fix." + __name__)


class NutanixCollectorPlugin(BaseCollectorPlugin):
    """Nutanix Collector Plugin"""

    def collect(self) -> None:
        """This method is being called by fix whenever the collector runs

        It is responsible for querying the cloud APIs for remote resources and adding
        them to the plugin graph.
        The graph root (self.graph.root) must always be followed by one or more
        accounts. An account must always be followed by a region.
        A region can contain arbitrary resources.
        """
        log.debug("plugin: collecting nutanix resources")

        pcConfigs = cast(
            List[PrismCentalCredentials], Config.PrismCentralColletorConfig.credentials
        )
        for pc in pcConfigs:
            pcAccount = PrismCentralAccount(
                id=pc.name.replace(" ", "_"),
                name=pc.name,
                endpoint=pc.endpoint,
                username=pc.username,
                password=pc.password,
            )
            pc_graph = self.collect_pc(pcAccount)
            self.graph.add_resource(self.graph.root, pc_graph)

    def collect_pc(self, prismCentral: PrismCentralAccount) -> Optional[Graph]:
        log.info(f"Collecting data from Nutanix Prism Central {prismCentral.name}")
        vmmClient = vmm_client(prismCentral)
        clusterClient = cluster_client(prismCentral)
        prismCentralCollector = PrismCentralCollector(
            prismCentral, vmmClient, clusterClient
        )
        return prismCentralCollector.collect()

    @staticmethod
    def add_config(config: Config) -> None:
        """Add any plugin config to the global config store.

        Method called by the PluginLoader upon plugin initialization.
        Can be used to introduce plugin config arguments to the global config store.
        """
        config.add_config(PrismCentralColletorConfig)

    @staticmethod
    def add_args(arg_parser: ArgumentParser) -> None:
        """Example of how to use the ArgumentParser

        Can be accessed via ArgumentParser.args.example_arg
        Note: almost all plugin config should be done via add_config()
        so it can be changed centrally and at runtime.
        """
        pass


def cluster_client(pc: PrismCentralAccount) -> ClusterClient:
    cluster_config = ClusterConfiguration()
    cluster_config.host = pc.endpoint
    cluster_config.port = pc.port
    cluster_config.verify_ssl = not pc.insecure
    cluster_config.username = pc.username
    cluster_config.password = pc.password
    cluster_client = ClusterClient(configuration=cluster_config)
    cluster_client.add_default_header(
        header_name="Accept-Encoding", header_value="gzip, deflate, br"
    )
    cluster_client.add_default_header(
        header_name="Content-Type", header_value="application/json"
    )
    return cluster_client


def vmm_client(pc: PrismCentralAccount) -> VMMClient:
    vmm_config = VMMConfiguration()
    vmm_config.host = pc.endpoint
    vmm_config.port = pc.port
    vmm_config.verify_ssl = not pc.insecure
    vmm_config.username = pc.username
    vmm_config.password = pc.password
    vmm_client = VMMClient(configuration=vmm_config)
    vmm_client.add_default_header(
        header_name="Accept-Encoding", header_value="gzip, deflate, br"
    )
    vmm_client.add_default_header(
        header_name="Content-Type", header_value="application/json"
    )
    return vmm_client
