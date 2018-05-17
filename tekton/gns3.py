"""
Handles GNS3 topology generation
"""

import itertools
import os
import shutil

from tekton.cisco import CiscoConfigGen
from tekton.graph import NetworkGraph


__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


class GNS3Config(object):
    """Helper class to set the parameters of GNS3"""

    default_dynampis_addr = '127.0.0.1:7200'
    default_console_start_port = 2501
    default_working_dir = '/tmp'
    default_ios_image = '/home/ahassany/GNS3/images/IOS/c7200-advipservicesk9-mz.152-4.S5.image'
    default_router_model = '7200'
    default_idlepc = '0x631868a4'
    default_idelmax = '500'
    default_ram = '256'
    default_nvram = '50'
    default_npe = 'npe-400'

    def __init__(
            self,
            dynampis_addr=None,
            console_start_port=None,
            working_dir=None,
            ios_image=None,
            router_model=None,
            idlepc=None,
            idelmax=None,
            ram=None,
            nvram=None,
            npe=None):
        self.dynampis_addr = dynampis_addr or GNS3Config.default_dynampis_addr
        self.console_start_port = console_start_port or GNS3Config.default_console_start_port
        self.working_dir = working_dir or GNS3Config.default_working_dir
        self.ios_image = ios_image or GNS3Config.default_ios_image
        self.router_model = router_model or GNS3Config.default_router_model
        self.idlepc = idlepc or GNS3Config.default_idlepc
        self.idelmax = idelmax or GNS3Config.default_idelmax
        self.ram = ram or GNS3Config.default_ram
        self.nvram = nvram or GNS3Config.default_nvram
        self.npe = npe or GNS3Config.default_npe


class GNS3Topo(object):
    """To Generate GNS3 configs"""

    def __init__(self, graph, prefix_map=None, gns3_config=None):
        assert isinstance(graph, NetworkGraph)
        self.prefix_map = prefix_map if prefix_map else {}
        self.graph = graph
        if not gns3_config:
            gns3_config = GNS3Config()
        self.gns3_config = gns3_config
        self.router_info = {
            'image': self.gns3_config.ios_image,
            'npe': self.gns3_config.npe,
            'ram': self.gns3_config.ram,
            'nvram': self.gns3_config.nvram,
            'idlepc': self.gns3_config.idlepc,
            'idlemax': self.gns3_config.idelmax,
        }
        self.next_console = itertools.count(self.gns3_config.console_start_port)
        self.config_gen = CiscoConfigGen(self.graph, prefix_map=self.prefix_map)

    def _annotate_node(self, node):
        """
        For each router annotate it with topological information needed to
        generate the topology file
        """
        assert self.graph.is_router(node), "'%s' is not a router" % node
        if 'dyn' not in self.graph.node[node]:
            self.graph.node[node]['dyn'] = {}
        dyn = self.graph.node[node]['dyn']
        dyn['model'] = self.gns3_config.router_model
        dyn['console'] = self.next_console.next()
        dyn['cnfg'] = "configs/%s.cfg" % node

    def get_gns3_topo(self):
        """Returns the content of topo.ini"""
        topo = ""
        topo += "autostart = False\n"
        topo += "ghostios = True\n"
        topo += "sparsemem = False\n"
        topo += "[%s]\n" % self.gns3_config.dynampis_addr
        topo += "\tworkingdir = %s\n" % self.gns3_config.working_dir
        topo += "\tudp = 15000"
        topo += "\n"
        topo += "\t[[ %s ]]\n" % self.gns3_config.router_model
        for key, value in self.router_info.iteritems():
            topo += "\t\t%s = %s\n" % (key, value)
        for node in sorted(list(self.graph.routers_iter())):
            topo += "\t[[ ROUTER %s ]]\n" % node
            self._annotate_node(node)
            for key, value in self.graph.node[node]['dyn'].iteritems():
                topo += "\t\t%s = %s\n" % (key, value)
            for neighbor in self.graph.neighbors(node):
                siface = self.graph.get_edge_iface(node, neighbor)
                diface = self.graph.get_edge_iface(neighbor, node)
                topo += "\t\t%s = %s %s\n" % (siface, neighbor, diface)
        return topo

    def gen_router_config(self, node):
        """Get the config for a give router"""
        return self.config_gen.gen_router_config(node)

    def write_configs(self, out_folder):
        """Generate the routers configs"""
        # Generating interface addresses
        self.graph.set_iface_names()

        # Clean up
        shutil.rmtree(out_folder, True)
        os.mkdir(out_folder)

        topo_file = os.path.join(out_folder, 'topo.ini')
        topo_file_str = self.get_gns3_topo()
        with open(topo_file, 'w') as fhandle:
            fhandle.write(topo_file_str)

        configs_folder = os.path.join(out_folder, 'configs')
        os.mkdir(configs_folder)
        for node in sorted(list(self.graph.routers_iter())):
            cfg = self.gen_router_config(node)
            cfg_file = os.path.join(configs_folder, "%s.cfg" % node)
            with open(cfg_file, 'w') as fhandle:
                fhandle.write(cfg)
