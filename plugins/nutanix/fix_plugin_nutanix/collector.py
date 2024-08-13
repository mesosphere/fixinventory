import logging

import ntnx_clustermgmt_py_client
from ntnx_clustermgmt_py_client import ApiClient as ClusterClient

from typing import Tuple, List, Dict, Callable

import ntnx_vmm_py_client
from ntnx_vmm_py_client import ApiClient as VMMClient
from fix_plugin_nutanix.resources import (
    PrismCentralAccount,
    PrismElement,
    ViraualMachine,
)
from fixlib.graph import Graph

log = logging.getLogger("fix." + __name__)
 

class PrismCentralCollector:
    """
    Collects data from single Nutanix Prism Central instance
    """

    def __init__(
        self,
        prismCentral: PrismCentralAccount,
        vmmClient: VMMClient,
        clusterClient: ClusterClient,
    ) -> None:
        self.vmmClient = vmmClient
        self.clusterClient = clusterClient
        self.prismCentral = prismCentral
        # pe_collectors collectors that are always collected
        self.mandatoryCollectors: List[Tuple[str, Callable[..., None]]] = [
            ("prism_elements", self.collect_prism_element)
        ]
        # Global collectors are resources that are specified across all PE
        self.globalCollectors: List[Tuple[str, Callable[..., None]]] = [
            # ("images", self.collect_images)
        ]
        # Prism Element collectors are resources that are specific to PE
        self.prismElementCollectors: List[Tuple[str, Callable[..., None]]] = [
            ("virtual_machines", self.collect_virtual_machines)
        ]
        self.allCollectors = dict(self.mandatoryCollectors)
        self.allCollectors.update(dict(self.globalCollectors))
        self.allCollectors.update(dict(self.prismElementCollectors))
        self.collecter_set = set(self.allCollectors.keys())
        self.graph = Graph(root=self.prismCentral)

    def collect(self) -> Graph:
        """
        Runs resource collectors across all PE
        Resource collectors add their resources to the local `self.graph` graph
        """
        log.info(f"Collecting data from Nutanix Prism Central: {self.prismCentral.name}")
        collectors = set(self.collecter_set)
        for collectorName, collector in self.mandatoryCollectors:
            if collectorName in collectors:
                log.info(f"Running collector: {collectorName} in {self.prismCentral.name}")
                collector()

        prismElements = [pe for pe in self.graph.nodes if isinstance(pe, PrismElement)]
        for collectorName, collector in self.prismElementCollectors:
            for pe in prismElements:
                if collectorName in collectors:
                    log.info(f"Running collector: {collectorName} in {pe.name}")
                    collector(pe)
        return self.graph

    def collect_prism_element(self) -> None:
        log.info("Collecting data from all Prism Elements")
        clusterApi = ntnx_clustermgmt_py_client.api.ClusterApi(self.clusterClient)
        clusters = clusterApi.get_clusters()
        log.info(f"Found PEs: {clusters.metadata.total_available_results}")
        for cluster in clusters.data:
            log.debug(f"Processing PE. uuid: {cluster['extId']}" f", name: {cluster['name']}")
            pe = PrismElement(
                id=cluster["extId"],
                name=cluster["name"],
                tags={"cluster_uuid": cluster["extId"]},
            )
            self.graph.add_resource(self.prismCentral, pe)

    def collect_images(self) -> None:
        """
        Collects data from all images
        """
        log.info("Collecting data from all images")

    def collect_virtual_machines(self, pe: PrismElement) -> None:
        log.info(f"Collecting data from all virtual machines in {pe.name}")
        # Get all virtual machines in the PE
        vmm_instance = ntnx_vmm_py_client.api.VmApi(self.vmmClient)
        filter = f"contains(cluster/extId, '{pe.id}')"
        response = vmm_instance.list_vms(_filter=filter)
        log.info(
            f"{pe.name}: Found virtual machines: {response.metadata.total_available_results}"
        )
        if response.metadata.total_available_results == 0:
            return
        for vm in response.data:
            log.debug(
                f"VM: {vm.name}"
                f", uuid: {vm.ext_id}"
                f", power_state: {vm.power_state}"
                f", create_time: {vm.create_time}"
            )
            vm = ViraualMachine(
                id=vm.ext_id,
                name=vm.name,
                tags={"power_state": vm.power_state},
                power_state=vm.power_state,
                ctime=vm.create_time,
                mtime=vm.update_time,
            )
            self.graph.add_resource(pe, vm)
