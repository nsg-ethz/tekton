#!/usr/bin/env python
import unittest

from ipaddress import ip_interface

from tekton.connected import ConnectedSyn
from tekton.connected import DuplicateAddressError
from tekton.connected import InterfaceIsDownError
from tekton.connected import NotValidSubnetsError
from tekton.graph import NetworkGraph
from tekton.utils import VALUENOTSET
from tekton.utils import is_empty


__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


class ConnectedTest(unittest.TestCase):

    def get_two_nodes(self):
        g = NetworkGraph()
        g.add_router('R1')
        g.add_router('R2')
        g.add_router_edge('R1', 'R2')
        g.add_router_edge('R2', 'R1')
        return g

    def test_correct_concrete(self):
        # Arrange
        graph = self.get_two_nodes()

        addr1 = ip_interface(u"192.168.0.1/24")
        addr2 = ip_interface(u"192.168.0.2/24")

        # Set Iface for R1 to R2
        iface = 'Fa0/0'
        graph.add_iface('R1', iface, is_shutdown=False)
        graph.set_iface_addr('R1', iface, addr1)
        graph.set_edge_iface('R1', 'R2', iface)
        graph.set_iface_description('R1', iface, ''"To {}"''.format('R2'))

        # Set Iface for R2 to R1
        iface = 'Fa0/0'
        graph.add_iface('R2', iface, is_shutdown=False)
        graph.set_iface_addr('R2', iface, addr2)
        graph.set_edge_iface('R2', 'R1', iface)
        graph.set_iface_description('R2', iface, ''"To {}"''.format('R1'))
        # Act
        syn = ConnectedSyn(graph, full=True)
        ret = syn.synthesize()
        # Assert
        self.assertTrue(ret)

    def test_wrong_subnets(self):
        # Arrange
        graph = self.get_two_nodes()

        addr1 = ip_interface(u"192.168.0.1/24")
        addr2 = ip_interface(u"192.168.0.2/25")

        # Set Iface for R1 to R2
        iface = 'Fa0/0'
        graph.add_iface('R1', iface, is_shutdown=False)
        graph.set_iface_addr('R1', iface, addr1)
        graph.set_edge_iface('R1', 'R2', iface)
        graph.set_iface_description('R1', iface, ''"To {}"''.format('R2'))

        # Set Iface for R2 to R1
        iface = 'Fa0/0'
        graph.add_iface('R2', iface, is_shutdown=False)
        graph.set_iface_addr('R2', iface, addr2)
        graph.set_edge_iface('R2', 'R1', iface)
        graph.set_iface_description('R2', iface, ''"To {}"''.format('R1'))

        # Act
        syn = ConnectedSyn(graph, full=True)
        # Assert
        with self.assertRaises(NotValidSubnetsError):
            syn.synthesize()

    def test_duplicate_address(self):
        # Arrange
        graph = self.get_two_nodes()

        addr1 = ip_interface(u"192.168.0.1/24")
        addr2 = ip_interface(u"192.168.0.1/24")

        # Set Iface for R1 to R2
        iface = 'Fa0/0'
        graph.add_iface('R1', iface, is_shutdown=False)
        graph.set_iface_addr('R1', iface, addr1)
        graph.set_edge_iface('R1', 'R2', iface)
        graph.set_iface_description('R1', iface, ''"To {}"''.format('R2'))

        # Set Iface for R2 to R1
        iface = 'Fa0/0'
        graph.add_iface('R2', iface, is_shutdown=False)
        graph.set_iface_addr('R2', iface, addr2)
        graph.set_edge_iface('R2', 'R1', iface)
        graph.set_iface_description('R2', iface, ''"To {}"''.format('R1'))
        # Act
        syn = ConnectedSyn(graph, full=True)
        # Assert
        with self.assertRaises(DuplicateAddressError):
            syn.synthesize()

    def test_shutdown(self):
        # Arrange
        graph = self.get_two_nodes()

        addr1 = ip_interface(u"192.168.0.1/24")
        addr2 = ip_interface(u"192.168.0.2/24")

        # Set Iface for R1 to R2
        iface = 'Fa0/0'
        graph.add_iface('R1', iface, is_shutdown=True)
        graph.set_iface_addr('R1', iface, addr1)
        graph.set_edge_iface('R1', 'R2', iface)
        graph.set_iface_description('R1', iface, ''"To {}"''.format('R2'))

        # Set Iface for R2 to R1
        iface = 'Fa0/0'
        graph.add_iface('R2', iface, is_shutdown=False)
        graph.set_iface_addr('R2', iface, addr2)
        graph.set_edge_iface('R2', 'R1', iface)
        graph.set_iface_description('R2', iface, ''"To {}"''.format('R1'))
        # Act
        syn1 = ConnectedSyn(graph, full=False)
        ret1 = syn1.synthesize()
        syn2 = ConnectedSyn(graph, full=True)
        # Assert
        self.assertTrue(ret1)
        with self.assertRaises(InterfaceIsDownError):
            syn2.synthesize()

    def test_one_side_concrete(self):
        # Arrange
        graph = self.get_two_nodes()
        addr1 = ip_interface(u"192.168.0.1/24")
        # Set Iface for R1 to R2
        iface = 'Fa0/0'
        graph.add_iface('R1', iface, is_shutdown=False)
        graph.set_iface_addr('R1', iface, addr1)
        graph.set_edge_iface('R1', 'R2', iface)
        graph.set_iface_description('R1', iface, ''"To {}"''.format('R2'))

        # Set Iface for R2 to R1
        iface = 'Fa0/0'
        graph.add_iface('R2', iface, is_shutdown=False)
        graph.set_iface_addr('R2', iface, VALUENOTSET)
        graph.set_edge_iface('R2', 'R1', iface)
        graph.set_iface_description('R2', iface, ''"To {}"''.format('R1'))
        # Act
        syn = ConnectedSyn(graph, full=True)
        syn.synthesize()
        # Assert
        self.assertFalse(is_empty(graph.get_iface_addr('R2', iface)))

    def test_one_extra(self):
        # Arrange
        graph = self.get_two_nodes()
        graph.add_router('R3')
        graph.add_router_edge('R1', 'R3')
        graph.add_router_edge('R2', 'R3')
        graph.add_router_edge('R3', 'R1')
        graph.add_router_edge('R3', 'R2')

        # Set Iface for R1 to R3
        iface1 = 'Fa0/0'
        addr1 = ip_interface(u"192.168.0.1/24")
        graph.add_iface('R1', iface1, is_shutdown=False)
        graph.set_iface_addr('R1', iface1, addr1)
        graph.set_edge_iface('R1', 'R3', iface1)
        graph.set_iface_description('R1', iface1, ''"To {}"''.format('R3'))

        # Set Iface for R3 to R1
        iface2 = 'Fa0/0'
        addr2 = ip_interface(u"192.168.0.2/24")
        graph.add_iface('R3', iface2, is_shutdown=False)
        graph.set_iface_addr('R3', iface2, addr2)
        graph.set_edge_iface('R3', 'R1', iface2)
        graph.set_iface_description('R3', iface2, ''"To {}"''.format('R1'))

        # Set Iface for R2 to R3
        iface3 = 'Fa0/0'
        addr3 = ip_interface(u"192.168.1.1/24")
        graph.add_iface('R2', iface3, is_shutdown=True)
        graph.set_iface_addr('R2', iface3, addr3)
        graph.set_edge_iface('R2', 'R3', iface3)
        graph.set_iface_description('R2', iface3, ''"To {}"''.format('R3'))

        # Set Iface for R3 to R2
        iface4 = 'Fa0/1'
        addr4 = ip_interface(u"192.168.1.2/24")
        graph.add_iface('R3', iface4, is_shutdown=True)
        graph.set_iface_addr('R3', iface4, addr4)
        graph.set_edge_iface('R3', 'R2', iface4)
        graph.set_iface_description('R3', iface4, ''"To {}"''.format('R1'))
        # Act
        syn = ConnectedSyn(graph, full=False)
        ret = syn.synthesize()
        # Asserts
        self.assertTrue(ret)
