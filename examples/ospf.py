#!/usr/bin/env python
"""
Examples of using Tekton for a network of 4 routers connected via OSPF
"""

import tempfile

from tekton.connected import ConnectedSyn
from tekton.gns3 import GNS3Topo
from tekton.graph import NetworkGraph

__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


def ospf_net():
    graph = NetworkGraph()
    r1, r2, r3, r4 = 'R1', 'R2', 'R3', 'R4'
    # Add routers
    graph.add_router(r1)
    graph.add_router(r2)
    graph.add_router(r3)
    graph.add_router(r4)
    # Connect routers
    graph.add_router_edge(r1, r2)
    graph.add_router_edge(r2, r1)
    graph.add_router_edge(r1, r3)
    graph.add_router_edge(r3, r1)
    graph.add_router_edge(r4, r2)
    graph.add_router_edge(r2, r4)
    graph.add_router_edge(r4, r3)
    graph.add_router_edge(r3, r4)
    # Enable OSPF
    graph.enable_ospf(r1, 100)
    graph.enable_ospf(r2, 100)
    graph.enable_ospf(r3, 100)
    graph.enable_ospf(r4, 100)
    # Assign interfaces
    graph.set_iface_names()
    # Add networks
    for router in graph.routers_iter():
        for iface in graph.get_ifaces(router):
            graph.add_ospf_network(router, iface, 0)
    # Set the edge costs
    graph.set_edge_ospf_cost(r1, r2, 100)
    graph.set_edge_ospf_cost(r1, r3, 200)
    graph.set_edge_ospf_cost(r2, r4, 50)
    graph.set_edge_ospf_cost(r3, r4, 300)
    # Edge costs for the reverse direction
    graph.set_edge_ospf_cost(r4, r2, 100)
    graph.set_edge_ospf_cost(r4, r3, 100)
    graph.set_edge_ospf_cost(r2, r1, 100)
    graph.set_edge_ospf_cost(r3, r1, 100)
    # Synthesize connectivity
    syn = ConnectedSyn(graph, full=True)
    assert syn.synthesize()
    # Write the configs
    gns3 = GNS3Topo(graph)
    tmpdir = tempfile.mkdtemp(suffix='-ospf')
    gns3.write_configs(tmpdir)
    print("Wrote configurations to %s" % tmpdir)


if __name__ == '__main__':
    ospf_net()
