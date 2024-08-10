import logging
import os
from typing import Dict, Any, List, cast

from fixlib.baseresources import GraphRoot, Cloud

from fixlib.graph import Graph
from fixlib.graph import sanitize
from fix_plugin_nutanix.collector import PrismCentralCollector
from fix_plugin_nutanix.resources import PrismCentralAccount
import fix_plugin_nutanix


log = logging.getLogger("fix." + __name__)


def prepare_graph() -> Graph:
    sherlockDevAccount = PrismCentralAccount(
        id="sherlock_dev",
        name="Sherlock Dev",
        endpoint="prismcentral.dev.ntnxsherlock.com",
        username=os.getenv("NUTANIX_USER"),
        password=os.getenv("NUTANIX_PASSWORD"),
        tags={"url": "https://prismcentral.dev.ntnxsherlock.com:9440/"},
    )
    vmmClient = fix_plugin_nutanix.vmm_client(sherlockDevAccount)
    clusterClient = fix_plugin_nutanix.cluster_client(sherlockDevAccount)
    plugin_instance = PrismCentralCollector(
        sherlockDevAccount, vmmClient, clusterClient
    )
    plugin_instance.collect()
    cloud = Cloud(id="nutanix_test")
    cloud_graph = Graph(root=cloud)
    cloud_graph.merge(plugin_instance.graph)
    # create root and add cloud graph.
    graph = Graph(root=GraphRoot(id="root", tags={}))
    graph.merge(cloud_graph)
    sanitize(graph)
    for node in graph.nodes:
        log.info(f"Node ID: {node.id}" + f"Node name: {node.name}")
    for node_from, node_to, edge in graph.edges:
        log.info(f"Edge from: {node_from.name} to {node_to.name} with type {edge}")

    return graph


def test_collect_nutanix() -> None:
    graph = prepare_graph()
