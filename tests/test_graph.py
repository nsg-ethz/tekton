#!/usr/bin/env python

import unittest

from nose.plugins.attrib import attr
import ipaddress

from tekton.bgp import Access
from tekton.bgp import CommunityList
from tekton.bgp import IpPrefixList

from tekton.utils import VALUENOTSET

from tekton.graph import EDGETYPE
from tekton.graph import EDGE_TYPE
from tekton.graph import VERTEX_TYPE
from tekton.graph import VERTEXTYPE
from tekton.graph import NetworkGraph


__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


@attr(speed='fast')
class TestNetworkGraph(unittest.TestCase):
    def get_add_one_peer(self, g, nodes, announcements):
        g.add_peer('ATT')
        g.set_bgp_asnum('ATT', 2000)
        for node in nodes:
            g.add_peer_edge(node, 'ATT')
            g.add_peer_edge('ATT', node)
            g.add_bgp_neighbor(node, 'ATT', VALUENOTSET, VALUENOTSET)
        for ann in announcements:
            g.add_bgp_advertise(ann.peer, ann)
        return g

    def test_add_node(self):
        g = NetworkGraph()
        with self.assertRaises(ValueError):
            g.add_node('R1')

    def test_add_router(self):
        # init
        g = NetworkGraph()
        router = 'R1'
        # Action
        g.add_router(router)
        # Asserts
        self.assertTrue(g.has_node(router))
        self.assertTrue(g.is_router(router))
        self.assertTrue(g.is_local_router(router))
        self.assertEqual(g.node[router][VERTEX_TYPE], VERTEXTYPE.ROUTER)
        self.assertEqual(list(g.routers_iter()), [router])
        self.assertEqual(list(g.local_routers_iter()), [router])
        self.assertFalse(g.is_network(router))
        self.assertFalse(g.is_peer(router))

    def test_add_network(self):
        # init
        g = NetworkGraph()
        network = 'NET1'
        # Action
        g.add_network(network)
        # Asserts
        self.assertTrue(g.has_node(network))
        self.assertTrue(g.is_network(network))
        self.assertEqual(g.node[network][VERTEX_TYPE], VERTEXTYPE.NETWORK)
        self.assertFalse(g.is_router(network))
        self.assertFalse(g.is_local_router(network))
        self.assertFalse(g.is_peer(network))
        self.assertEqual(list(g.networks_iter()), [network])

    def test_add_peer(self):
        # init
        g = NetworkGraph()
        peer = 'PEER1'
        # Action
        g.add_peer(peer)
        # Asserts
        self.assertTrue(g.has_node(peer))
        self.assertTrue(g.is_peer(peer))
        self.assertTrue(g.is_router(peer))
        self.assertEqual(g.node[peer][VERTEX_TYPE], VERTEXTYPE.PEER)
        self.assertEqual(list(g.peers_iter()), [peer])
        self.assertFalse(g.is_local_router(peer))
        self.assertFalse(g.is_network(peer))

    def test_add_edge(self):
        # init
        g = NetworkGraph()
        router1 = 'R1'
        router2 = 'R2'
        g.add_router(router1)
        g.add_router(router2)
        # Action
        g.add_edge('R1', 'R2', **{EDGE_TYPE: EDGETYPE.ROUTER})
        with self.assertRaises(ValueError):
            g.add_edge('R1', 'R2')

    def test_add_router_link(self):
        # init
        g = NetworkGraph()
        router1 = 'R1'
        router2 = 'R2'
        g.add_router(router1)
        g.add_router(router2)
        # Action
        g.add_router_edge(router1, router2)
        # Assert
        self.assertEqual(list(g.edges()), [(router1, router2)])
        self.assertEqual(g[router1][router2][EDGE_TYPE], EDGETYPE.ROUTER)

    def test_add_peer_link(self):
        # init
        g = NetworkGraph()
        router1 = 'R1'
        router2 = 'R2'
        g.add_router(router1)
        g.add_peer(router2)
        # Action
        g.add_peer_edge(router1, router2)
        # Assert
        self.assertEqual(list(g.edges()), [(router1, router2)])
        self.assertEqual(g[router1][router2][EDGE_TYPE], EDGETYPE.PEER)

    def test_router_id(self):
        # Arrange
        graph = NetworkGraph()
        router1 = 'R1'
        graph.add_router(router1)
        graph.set_bgp_asnum(router1, 100)
        value1 = VALUENOTSET
        value2 = 123
        value3 = ipaddress.IPv4Address(u'1.1.1.1')
        # Act
        rid0 = graph.get_bgp_router_id(router1)
        graph.set_bgp_router_id(router1, value1)
        rid1 = graph.get_bgp_router_id(router1)
        graph.set_bgp_router_id(router1, value2)
        rid2 = graph.get_bgp_router_id(router1)
        graph.set_bgp_router_id(router1, value3)
        rid3 = graph.get_bgp_router_id(router1)
        # Assert
        self.assertIsNone(rid0)
        self.assertEquals(value1, rid1)
        self.assertEquals(value2, rid2)
        self.assertEquals(value3, rid3)

    def test_add_ip_list(self):
        # Arrange
        net = ipaddress.ip_network(u'128.0.0.0/24')
        graph = NetworkGraph()
        router1 = 'R1'
        graph.add_router(router1)
        named = IpPrefixList(name='L1', access=Access.permit, networks=[net])
        dup = IpPrefixList(name='L1', access=Access.permit, networks=[net])
        unamed = IpPrefixList(name=None, access=Access.permit, networks=[net])
        # Act
        graph.add_ip_prefix_list(router1, named)
        graph.add_ip_prefix_list(router1, unamed)
        # Assert
        self.assertIn(named.name, graph.get_ip_preflix_lists(router1))
        self.assertIsNotNone(unamed.name)
        self.assertIn(unamed.name, graph.get_ip_preflix_lists(router1))

    def test_add_community_list(self):
        # Arrange
        graph = NetworkGraph()
        router1 = 'R1'
        graph.add_router(router1)
        named = CommunityList(list_id=1, access=Access.permit, communities=[VALUENOTSET])
        dup = CommunityList(list_id=1, access=Access.permit, communities=[VALUENOTSET])
        unamed = CommunityList(list_id=None, access=Access.permit, communities=[VALUENOTSET])
        # Act
        graph.add_bgp_community_list(router1, named)
        graph.add_bgp_community_list(router1, unamed)
        # Assert
        self.assertIn(named.list_id, graph.get_bgp_communities_list(router1))
        self.assertIsNotNone(unamed.list_id)
        self.assertIn(unamed.list_id, graph.get_bgp_communities_list(router1))

