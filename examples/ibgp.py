#!/usr/bin/env python
"""
Examples of using Tekton for a network of iBGP network with external Peer
"""

from ipaddress import ip_interface
from ipaddress import ip_network

from tekton.bgp import Access
from tekton.bgp import ActionSetLocalPref
from tekton.bgp import RouteMap
from tekton.bgp import RouteMapLine
from tekton.connected import ConnectedSyn
from tekton.gns3 import GNS3Topo
from tekton.graph import NetworkGraph

__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


def ibgp_net():
    graph = NetworkGraph()
    peer, r1, r2, r3, r4 = 'Ext', 'R1', 'R2', 'R3', 'R4'
    # Add routers
    graph.add_peer(peer)
    graph.add_router(r1)
    graph.add_router(r2)
    graph.add_router(r3)
    graph.add_router(r4)
    # Connect routers
    graph.add_peer_edge(peer, r1)
    graph.add_peer_edge(r1, peer)
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
    # Set BGP ASN
    graph.set_bgp_asnum(peer, 200)
    graph.set_bgp_asnum(r1, 100)
    graph.set_bgp_asnum(r2, 100)
    graph.set_bgp_asnum(r3, 100)
    graph.set_bgp_asnum(r4, 100)
    # Establish BGP peering
    graph.add_bgp_neighbor(peer, r1)
    graph.add_bgp_neighbor(r1, r2)
    graph.add_bgp_neighbor(r1, r3)
    graph.add_bgp_neighbor(r1, r4)
    graph.add_bgp_neighbor(r2, r3)
    graph.add_bgp_neighbor(r2, r4)
    graph.add_bgp_neighbor(r3, r4)
    # Assign interfaces
    graph.set_iface_names()
    # Some internal to be announced network
    net = ip_network(u'128.0.0.0/24')
    prefix = '128_0_0_0'
    lo0 = 'lo0'
    prefix_map = {prefix: net}
    loaddr = ip_interface("%s/%d" % (net.hosts().next(), net.prefixlen))
    graph.set_loopback_addr(peer, lo0, loaddr)
    graph.add_bgp_announces(peer, lo0)

    # Synthesize connectivity
    syn = ConnectedSyn(graph, full=True, default_ibgp_lo='lo10')
    assert syn.synthesize()

    # Some route map
    actions = [ActionSetLocalPref(200)]
    line = RouteMapLine(matches=None, actions=actions, access=Access.permit, lineno=100)
    route_map = RouteMap(name="ImpPolicy", lines=[line])
    graph.add_route_map(r1, route_map)
    graph.add_bgp_import_route_map(r1, peer, route_map.name)
    # Add networks
    # Note, some of the loop back interfaces where generated due to
    # ibgp peering in ConnectedSyn
    for router in graph.local_routers_iter():
        for iface in graph.get_ifaces(router):
            graph.add_ospf_network(router, iface, 0)
        for lo in graph.get_loopback_interfaces(router):
            graph.add_ospf_network(router, lo, 0)

    # Write the configs
    gns3 = GNS3Topo(graph, prefix_map=prefix_map)
    gns3.write_configs('out-configs/ibgp')


if __name__ == '__main__':
    ibgp_net()
