#!/usr/bin/env python
"""
Examples of using Tekton for a network of two routers connected via eBGP
"""

from ipaddress import ip_interface
from ipaddress import ip_network

from tekton.connected import ConnectedSyn
from tekton.gns3 import GNS3Topo
from tekton.graph import NetworkGraph

__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


def ebgp_net():
    graph = NetworkGraph()
    r1, r2 = 'R1', 'R2'
    graph.add_router(r1)
    graph.add_router(r2)
    graph.add_router_edge(r1, r2)
    graph.add_router_edge(r2, r1)

    # BGP configs
    graph.set_bgp_asnum(r1, 100)
    graph.set_bgp_asnum(r2, 200)
    graph.add_bgp_neighbor(r1, r2)

    # Some internal to be announced network
    net = ip_network(u'128.0.0.0/24')
    prefix = '128_0_0_0'
    lo0 = 'lo10'
    prefix_map = {prefix: net}
    loaddr = ip_interface("%s/%d" % (net.hosts().next(), net.prefixlen))
    graph.set_loopback_addr(r1, lo0, loaddr)
    graph.add_bgp_announces(r1, lo0)

    # Synthesize all the interfaces and link configurations
    connecte_syn = ConnectedSyn(graph, full=True)
    assert connecte_syn.synthesize()

    graph.set_iface_names()

    gns3 = GNS3Topo(graph=graph, prefix_map=prefix_map)
    gns3.write_configs('out-configs/ebgp-simple')


if __name__ == '__main__':
    ebgp_net()
