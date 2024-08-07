import logging
from typing import Dict, Any, List, cast

from fixlib.baseresources import  GraphRoot

from fixlib.graph import Graph
from fixlib.graph import sanitize
from fix_plugin_nutanix import NutanixCollectorPlugin


log = logging.getLogger("fix." + __name__)

def prepare_graph() -> Graph:
    plugin_instance = NutanixCollectorPlugin()
    plugin_instance.collect()
    graph = Graph(root=GraphRoot(id="root", tags={}))
    graph.merge(plugin_instance.graph)
    sanitize(graph)
    return graph

def test_collect_nutanix() -> None:
    graph = prepare_graph()