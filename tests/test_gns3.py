import unittest
import random

from tekton.graph import NetworkGraph
from tekton.gns3 import GNS3Config
from tekton.gns3 import GNS3Topo


__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


class GNS3ConfigTest(unittest.TestCase):
    def test_defualt(self):
        # Arrange
        # Act
        config = GNS3Config()
        # Assert
        for attr in dir(config):
            if attr.startswith('__'):
                continue
            if attr.startswith('default'):
                continue
            default = 'default_%s' % attr
            self.assertTrue(hasattr(GNS3Config, default))
            self.assertEquals(getattr(config, attr), getattr(GNS3Config, default))

    def test_non_default(self):
        # Arrange
        attrs = [attr for attr in dir(GNS3Config())
                 if not (attr.startswith('_') or attr.startswith('default'))]
        rand_vals = dict([(attr, "val_%d" % random.randint(1, 1000000)) for attr in attrs])
        # Act
        config = GNS3Config(**rand_vals)
        # Assert
        for attr, value in rand_vals.items():
            self.assertEquals(getattr(config, attr), value)


class GNS3TopoTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        graph = NetworkGraph()
        graph.add_router('R1')
        # Act
        gns3 = GNS3Topo(graph)
        # Assert
        self.assertIsNotNone(gns3.get_gns3_topo())
