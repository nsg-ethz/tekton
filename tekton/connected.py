#!/usr/bin/env python
"""
Synthesize directly connected interfaces
"""

from ipaddress import IPv4Network
from ipaddress import IPv6Network
from ipaddress import ip_address
from ipaddress import ip_interface
from ipaddress import ip_network

from tekton.graph import NetworkGraph
from tekton.utils import VALUENOTSET
from tekton.utils import is_empty

__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


class InterfaceIsDownError(Exception):
    """The interface is configured to be shutdown, while it's required to be up"""

    def __init__(self, src, src_iface):
        super(InterfaceIsDownError, self).__init__()
        self.src = src
        self.src_iface = src_iface


class NotValidSubnetsError(Exception):
    def __init__(self, src, src_iface, src_net, dst, dst_iface, dst_net):
        """The two interfaces have IP addresses with different subnets"""
        super(NotValidSubnetsError, self).__init__()
        self.src = src
        self.src_iface = src_iface
        self.src_net = src_net
        self.dst = dst
        self.dst_iface = dst_iface
        self.dst_net = dst_net


class DuplicateAddressError(Exception):
    """The two interfaces are configured with the same IP addresses"""

    def __init__(self, src, src_iface, src_addr, dst, dst_iface, dst_addr):
        super(DuplicateAddressError, self).__init__()
        self.src = src
        self.src_iface = src_iface
        self.src_addr = src_addr
        self.dst = dst
        self.dst_iface = dst_iface
        self.dst_addr = dst_addr


class ConnectedSyn(object):
    def __init__(self, network_graph, full=True, start_net=None,
                 default_ibgp_lo='lo100', start_lo_net=None):
        """
        :param network_graph: tekton.graph.NetworkGraph
        :param full: Make sure every interface is up and connected
        :param start_net:
        :param prefix_len:
        """
        assert isinstance(network_graph, NetworkGraph)
        self.network_graph = network_graph
        self.full = full
        if not start_net:
            start_net = ip_network(u'10.0.0.0/31')
        assert isinstance(start_net, (IPv4Network, IPv6Network))
        self._start_net = start_net
        self._next_net = self._start_net
        self.default_ibgp_lo = default_ibgp_lo
        if not start_lo_net:
            start_lo_net = ip_network(u'192.0.0.0/32')
        self.start_lo_net = start_lo_net
        self._next_lo_net = start_lo_net

    def get_next_net(self, net):
        """Get the next subnet to be assigned to interfaces"""
        family = 32 if isinstance(net, IPv4Network) else 128
        base = int(net.network_address)
        next_addr = ip_address(base + (2 ** (family - net.prefixlen)))
        next_net = ip_network(u'%s/%d' % (next_addr, net.prefixlen))
        return next_net

    def get_bgp_connected_pairs(self):
        """Get the connected pairs due to direct BGP peering sessions"""
        connected_pairs = []
        for node in self.network_graph.routers_iter():
            for neigbor in self.network_graph.get_bgp_neighbors(node):
                if self.network_graph.has_edge(node, neigbor):
                    connected_pairs.append((node, neigbor))
        return connected_pairs

    def synthesize_connection(self, src, dst):
        """Synthesize connection between two routers"""
        err = "Routers (%s, %s) are not directly connected" % (src, dst)
        assert self.network_graph.has_edge(src, dst), err
        iface1 = self.network_graph.get_edge_iface(src, dst)
        iface2 = self.network_graph.get_edge_iface(dst, src)
        # Make sure interfaces are up
        if self.full and self.network_graph.is_iface_shutdown(src, iface1):
            raise InterfaceIsDownError(src, iface1)
        if self.full and self.network_graph.is_iface_shutdown(dst, iface2):
            raise InterfaceIsDownError(src, iface2)
        addr1 = self.network_graph.get_iface_addr(src, iface1)
        addr2 = self.network_graph.get_iface_addr(dst, iface2)
        err1 = "Address not set and not a hole for iface: %s-%s" % (src, iface1)
        err2 = "Address not set and not a hole for iface: %s-%s" % (dst, iface2)
        assert addr1, err1
        assert addr2, err2

        # Get the subnet for both ends of the line
        if is_empty(addr1) and is_empty(addr2):
            # No initial config is given
            # Then synthesize completely new subnet
            net1 = self._next_net
            self._next_net = self.get_next_net(net1)
            net2 = net1
        elif is_empty(addr1) or is_empty(addr2):
            # Only one side is concrete
            net = addr1.network if not is_empty(addr1) else addr2.network
            net1 = net
            net2 = net
        else:
            # Both sides are concrete
            net1 = addr1.network
            net2 = addr2.network

        # The two interfaces must have the same network
        if net1 != net2:
            raise NotValidSubnetsError(src, iface1, net1, dst, iface2, net2)

        # Assign IP addresses to the first interface (if needed)
        if is_empty(addr1):
            for host in net1.hosts():
                addr = ip_interface(u"%s/%d" % (host, net1.prefixlen))
                if addr == addr2:
                    continue
                addr1 = addr
                self.network_graph.set_iface_addr(src, iface1, addr)
                break
        # Assign IP addresses to the second interface (if needed)
        if is_empty(addr2):
            for host in net2.hosts():
                addr = ip_interface(u"%s/%d" % (host, net2.prefixlen))
                if addr != addr1:
                    addr2 = addr
                    self.network_graph.set_iface_addr(dst, iface2, addr)
                    break
        # The interfaces must have unique IP addresses
        if addr1 == addr2:
            raise DuplicateAddressError(src, iface1, addr1, dst, iface2, addr2)
        assert iface1

    def synthesize_next_hop(self, node, neighbor):
        """
        Synthesizes a next hop interface between two router
        :return the name of the interface (on the neighbor)
        """
        # TODO: Synthesize proper next hop
        asnum1 = self.network_graph.get_bgp_asnum(node)
        asnum2 = self.network_graph.get_bgp_asnum(neighbor)
        if asnum1 != asnum2 and self.network_graph.has_edge(neighbor, node):
            iface = self.network_graph.get_edge_iface(neighbor, node)
        else:
            loopbacks = self.network_graph.get_loopback_interfaces(neighbor)
            iface = self.default_ibgp_lo
            if iface not in loopbacks:
                self.network_graph.set_loopback_addr(neighbor, iface,
                                                     VALUENOTSET)
        return iface

    def compute_bgp_peerings(self):
        for node in self.network_graph.routers_iter():
            if not self.network_graph.get_bgp_asnum(node):
                # BGP is not configured on this router
                continue
            neighbors = self.network_graph.get_bgp_neighbors(node)
            for neighbor in neighbors:
                iface = self.network_graph.get_bgp_neighbor_iface(node, neighbor)
                if is_empty(iface):
                    iface = self.synthesize_next_hop(node, neighbor)
                self.network_graph.set_bgp_neighbor_iface(node, neighbor, iface)
                assert iface, "Synthesize connected first"

    def assign_loop_back_addresses(self):
        for node in sorted(self.network_graph.routers_iter()):
            loopbacks = self.network_graph.get_loopback_interfaces(node)
            for loopback in loopbacks:
                if not is_empty(self.network_graph.get_loopback_addr(node, loopback)):
                    continue
                net = self._next_lo_net
                self._next_lo_net = self.get_next_net(net)
                ipaddr = None
                for ipaddr in net.hosts():
                    break
                if not ipaddr:
                    ipaddr = net.network_address
                addr = ip_interface(ipaddr)
                self.network_graph.set_loopback_addr(node, loopback, addr)

    def synthesize(self):
        # Assign iface names between edges (if needed)
        self.network_graph.set_iface_names()

        for src, dst in self.network_graph.edges():
            if not self.network_graph.is_router(src):
                continue
            if not self.network_graph.is_router(dst):
                continue
            self.synthesize_connection(src, dst)
        self.compute_bgp_peerings()
        self.assign_loop_back_addresses()
        return True
