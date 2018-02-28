import unittest


from tekton.bgp import *
from tekton.utils import is_empty
from tekton.utils import VALUENOTSET

from ipaddress import ip_network

__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


class CommunityTest(unittest.TestCase):
    def test_community_init(self):
        # Arrange
        value1 = 13107866
        value2 = "200:666"
        value3 = 400
        # Act
        c1 = Community(value=value1)
        c2 = Community(value=value2)
        c3 = Community(value=value3, new_format=False)
        # Asserts
        self.assertEquals(c1.value, value2)
        self.assertEquals(c1.get_value(), value1)
        self.assertEquals(c2.value, value2)
        self.assertEquals(c2.get_value(), value1)
        self.assertEquals(c3.value, value3)
        self.assertEquals(c3.get_value(), value3)
        self.assertIsNotNone(c1.name)
        self.assertIsNotNone(c2.name)
        self.assertIsNotNone(c3.name)
        self.assertEquals(str(c1), "Community(%s)" % value2)
        self.assertEquals(str(c2), "Community(%s)" % value2)
        self.assertEquals(str(c3), "Community(%s)" % value3)

    def test_community_eq(self):
        # Arrange
        value1 = 13107866
        value2 = "200:666"
        value3 = 13107867
        value4 = "200:667"
        # Act
        c1 = Community(value=value1)
        c2 = Community(value=value2)
        c3 = Community(value=value3)
        c4 = Community(value=value4)
        # Asserts
        self.assertEquals(c1, c2)
        self.assertEquals(c3, c4)
        self.assertNotEquals(c1, c3)


class CommunityListTest(unittest.TestCase):
    def test_comm_list(self):
        # Arrange
        c1 = Community("200:666")
        c2 = Community("200:667")
        # Act
        clist1 = CommunityList(1, Access.permit, communities=(c1, c2))
        clist2 = CommunityList(2, Access.permit, (VALUENOTSET, VALUENOTSET))
        clist3 = CommunityList(3, Access.permit, (VALUENOTSET,))
        clist3.communities = (c1,)
        # Assert
        self.assertEquals(clist1.list_id, 1)
        self.assertEquals(clist2.list_id, 2)
        self.assertEquals(clist3.list_id, 3)
        self.assertEquals(clist1.access, Access.permit)
        self.assertEquals(clist2.access, Access.permit)
        self.assertEquals(clist3.access, Access.permit)
        self.assertEquals(clist1.communities, (c1, c2))
        self.assertEquals(clist2.communities, (VALUENOTSET, VALUENOTSET))
        self.assertEquals(clist3.communities, (c1,))

    def test_comm_eq(self):
        # Arrange
        c1 = Community("200:666")
        c2 = Community("200:667")
        clist1 = CommunityList(1, Access.permit, (c1, c2))
        clist2 = CommunityList(1, Access.permit, (c1, c2))
        clist3 = CommunityList(3, Access.permit, (c2, c1))
        # Act
        eq1 = clist1 == clist2
        eq2 = clist1 == clist3
        # Assert
        self.assertTrue(eq1)
        self.assertFalse(eq2)


class MatchCommunitiesListTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        c1 = Community("200:666")
        c2 = Community("200:667")
        clist1 = CommunityList(1, Access.permit, communities=(c1, c2))
        # Act
        match1 = MatchCommunitiesList(clist1)
        match2 = MatchCommunitiesList(VALUENOTSET)
        match2.match = clist1
        # Assert
        self.assertEquals(match1.match, clist1)
        self.assertEquals(match2.match, clist1)


class ASPathListTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        as1 = 100
        as2 = 200
        # Act
        as_path1 = ASPathList(list_id=1, access=Access.permit,
                              as_paths=(as1, as2))
        as_path2 = ASPathList(list_id=2, access=Access.permit,
                              as_paths=(VALUENOTSET, VALUENOTSET))
        as_path3 = ASPathList(list_id=3, access=Access.permit,
                              as_paths=VALUENOTSET)
        as_path3.as_paths = (as1,)
        # Assert
        self.assertEquals(as_path1.list_id, 1)
        self.assertEquals(as_path2.list_id, 2)
        self.assertEquals(as_path3.list_id, 3)
        self.assertEquals(as_path1.access, Access.permit)
        self.assertEquals(as_path2.access, Access.permit)
        self.assertEquals(as_path3.access, Access.permit)
        self.assertEquals(as_path1.as_paths, (as1, as2))
        self.assertEquals(as_path2.as_paths, (VALUENOTSET, VALUENOTSET))
        self.assertEquals(as_path3.as_paths, (as1,))
        with self.assertRaises(ValueError):
            as_path3.as_paths = (as1, as2)

    def test_eq(self):
        # Arrange
        as1 = 100
        as2 = 200
        as_path1 = ASPathList(list_id=1, access=Access.permit, as_paths=(as1, as2))
        as_path2 = ASPathList(list_id=1, access=Access.permit, as_paths=(as1, as2))
        as_path3 = ASPathList(list_id=3, access=Access.permit, as_paths=(as2, as1))
        # Act
        eq1 = as_path1 == as_path2
        eq2 = as_path1 == as_path3
        # Assert
        self.assertTrue(eq1)
        self.assertFalse(eq2)


class IpPrefixListTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        net1 = 'Prefix0'
        net2 = ip_network(u'128.0.0.0/16')
        # Act
        list1 = IpPrefixList(name=1, access=Access.permit, networks=(net1, net2))
        list2 = IpPrefixList(name=2, access=Access.permit, networks=(VALUENOTSET, VALUENOTSET))
        list3 = IpPrefixList(name=3, access=Access.permit, networks=(VALUENOTSET,))
        list3.networks = (net1,)
        # Assert
        self.assertEquals(list1.name, 1)
        self.assertEquals(list2.name, 2)
        self.assertEquals(list3.name, 3)
        self.assertEquals(list1.access, Access.permit)
        self.assertEquals(list2.access, Access.permit)
        self.assertEquals(list3.access, Access.permit)
        self.assertEquals(list1.networks, (net1, net2))
        self.assertEquals(list2.networks, (VALUENOTSET, VALUENOTSET))
        self.assertEquals(list3.networks, (net1,))

    def test_eq(self):
        # Arrange
        net1 = 'Prefix0'
        net2 = ip_network(u'128.0.0.0/16')
        list1 = IpPrefixList(name=1, access=Access.permit, networks=(net1, net2))
        list2 = IpPrefixList(name=1, access=Access.permit, networks=(net1, net2))
        list3 = IpPrefixList(name=3, access=Access.permit, networks=(net2,))
        # Act
        eq1 = list1 == list2
        eq2 = list1 == list3
        # Assert
        self.assertTrue(eq1)
        self.assertFalse(eq2)


class MatchPeerTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 'Value1'
        value2 = 'Value2'
        # Act
        match1 = MatchPeer(value1)
        match2 = MatchPeer(VALUENOTSET)
        match2.match = value2
        # Assert
        self.assertEquals(match1.match, value1)
        self.assertEquals(match2.match, value2)


class MatchNextHopTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 'Value1'
        value2 = 'Value2'
        # Act
        match1 = MatchNextHop(value1)
        match2 = MatchNextHop(VALUENOTSET)
        match2.match = value2
        # Assert
        self.assertEquals(match1.match, value1)
        self.assertEquals(match2.match, value2)


class MatchLocalPrefTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 100
        value2 = 200
        # Act
        match1 = MatchLocalPref(value1)
        match2 = MatchLocalPref(VALUENOTSET)
        match2.match = value2
        # Assert
        self.assertEquals(match1.match, value1)
        self.assertEquals(match2.match, value2)


class MatchAsPathTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = (100, 200)
        value2 = (200, 300)
        # Act
        match1 = MatchAsPath(value1)
        match2 = MatchAsPath(VALUENOTSET)
        match2.match = value2
        # Assert
        self.assertEquals(match1.match, value1)
        self.assertEquals(match2.match, value2)


class MatchAsPathLenTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 5
        value2 = 6
        # Act
        match1 = MatchAsPathLen(value1)
        match2 = MatchAsPathLen(VALUENOTSET)
        match2.match = value2
        # Assert
        self.assertEquals(match1.match, value1)
        self.assertEquals(match2.match, value2)


class MatchPermittedTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = Access.permit
        value2 = Access.deny
        # Act
        match1 = MatchPermitted(value1)
        match2 = MatchPermitted(VALUENOTSET)
        match2.match = value2
        # Assert
        self.assertEquals(match1.match, value1)
        self.assertEquals(match2.match, value2)


class MatchMEDTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 100
        value2 = 200
        # Act
        match1 = MatchMED(value1)
        match2 = MatchMED(VALUENOTSET)
        match2.match = value2
        # Assert
        self.assertEquals(match1.match, value1)
        self.assertEquals(match2.match, value2)


class MatchSelectOneTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = (MatchLocalPref(100), MatchPeer(VALUENOTSET))
        value2 = (MatchLocalPref(200), MatchPeer(VALUENOTSET))
        # Act
        match1 = MatchSelectOne(value1)
        match2 = MatchSelectOne(value2)
        # Assert
        self.assertEquals(match1.match, value1)
        self.assertEquals(match2.match, value2)
        with self.assertRaises(ValueError):
            match2.match = value2


class ActionPermittedTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = Access.permit
        value2 = Access.deny
        # Act
        action1 = ActionPermitted(value1)
        action2 = ActionPermitted(VALUENOTSET)
        action3 = ActionPermitted(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionSetLocalPrefTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 100
        value2 = 200
        # Act
        action1 = ActionSetLocalPref(value1)
        action2 = ActionSetLocalPref(VALUENOTSET)
        action3 = ActionSetLocalPref(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionSetNextHopTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 'Hop1'
        value2 = 'Hop2'
        # Act
        action1 = ActionSetNextHop(value1)
        action2 = ActionSetNextHop(VALUENOTSET)
        action3 = ActionSetNextHop(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionSetPrefixTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 'Prefix1'
        value2 = 'Prefix2'
        # Act
        action1 = ActionSetPrefix(value1)
        action2 = ActionSetPrefix(VALUENOTSET)
        action3 = ActionSetPrefix(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionASPathPrependTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = (100, 200)
        value2 = (200, 300)
        # Act
        action1 = ActionASPathPrepend(value1)
        action2 = ActionASPathPrepend(VALUENOTSET)
        action3 = ActionASPathPrepend(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionSetASPathTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = (100, 200)
        value2 = (200, 300)
        # Act
        action1 = ActionSetASPath(value1)
        action2 = ActionSetASPath(VALUENOTSET)
        action3 = ActionSetASPath(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionSetASPathLenTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 10
        value2 = 20
        # Act
        action1 = ActionSetASPathLen(value1)
        action2 = ActionSetASPathLen(VALUENOTSET)
        action3 = ActionSetASPathLen(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionSetPeerTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 'Peer1'
        value2 = 'Peer2'
        # Act
        action1 = ActionSetPeer(value1)
        action2 = ActionSetPeer(VALUENOTSET)
        action3 = ActionSetPeer(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionSetMEDTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = 100
        value2 = 200
        # Act
        action1 = ActionSetMED(value1)
        action2 = ActionSetMED(VALUENOTSET)
        action3 = ActionSetMED(value1)
        eq1 = action2 == action1
        action2.value = value2
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2


class ActionSetOneTest(unittest.TestCase):
    def test_init(self):
        # Arrange
        value1 = (ActionSetMED(VALUENOTSET), ActionPermitted(VALUENOTSET))
        value2 = (ActionSetNextHop(VALUENOTSET), ActionPermitted(VALUENOTSET))
        # Act
        action1 = ActionSetOne(value1)
        action2 = ActionSetOne(value2)
        action3 = ActionSetOne(value1)
        eq1 = action2 == action1
        eq2 = action2 == action1
        eq3 = action1 == action3
        # Assert
        self.assertEquals(action1.value, value1)
        self.assertEquals(action2.value, value2)
        self.assertFalse(eq1)
        self.assertFalse(eq2)
        self.assertTrue(eq3)
        with self.assertRaises(ValueError):
            action2.value = value2
