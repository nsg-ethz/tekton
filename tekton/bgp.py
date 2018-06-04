#!/usr/bin/env python
"""
Various helpers with configuring BGP related Policies
"""

from enum import Enum
from collections import Iterable
from ipaddress import IPv4Network
from ipaddress import IPv6Network

from tekton.utils import is_empty
from tekton.utils import is_symbolic
from tekton.utils import VALUENOTSET

__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


class Announcement(object):
    """
    Carry BGP Announcement information
    """
    attributes = [
        'prefix', 'peer', 'origin', 'as_path', 'as_path_len', 'next_hop',
        'local_pref', 'med', 'communities', 'permitted']

    def __init__(self, prefix, peer, origin,
                 as_path, as_path_len, next_hop, local_pref, med, communities,
                 permitted, prev_announcement=None):
        """
        :param prefix: the prefix that's being announced
        :param peer: the peer from whom that prefix has been received
                    (this is not technically in the BGP attributes set)
        :param origin: See BGP_ATTRS_ORIGIN
        :param as_path: List of AS numbers
        :param as_path_len: int
        :param next_hop:
            1. If the BGP Peers are in different AS then the next_hop IP address
               that will be sent in the update message will be the IP address of
               the advertising router.
            2. If the BGP peers are in the same AS (IBGP Peers),
                and the destination network being advertised in the update message
                is also in the same AS, then the next_hop IP address that will be sent
                in the update message will be the IP address of the advertising router
            3. If the BGP peers are in the same AS (IBGP Peers),
                and the destination network being advertised in the update message
                is in an external AS, then the next_hop IP address that will be
                sent in the update message will be the IP address of the external
                peer router which sent the advertisement to this AS.
        :param local_pref: is only used in updates sent to the IBGP Peers,
                It is not passed on to the BGP peers in other autonomous systems.
        :param med: MED value, int
        :param communities: dict Community values: Community->True/False
        :param permitted: Access.permit or Access.deny
        :param prev_announcement: keep track of the announcement that generated this one
        """
        #if isinstance(as_path, list):
        #    if not is_symbolic(as_path_len) and not is_empty(as_path_len):
        #        assert len(as_path) == as_path_len
        if prev_announcement:
            assert isinstance(prev_announcement, Announcement)
        assert is_symbolic or not is_empty(as_path)
        if not is_symbolic(as_path):
            for asnum in as_path:
                assert not is_empty(asnum)
        self.prefix = prefix
        self.peer = peer
        self.origin = origin
        self.as_path = as_path
        self.as_path_len = as_path_len
        self.next_hop = next_hop
        self.local_pref = local_pref
        self.med = med
        self.communities = communities
        self.permitted = permitted
        self.prev_announcement = prev_announcement
        self.__setattr__ = self._disable_mutations

    def _disable_mutations(self, key, value):
        assert hasattr(self, key), "Cannot assign new attributes"
        val = str(getattr(self, key))
        err = "Cannot assigned value to %s, existing value is %s" % (key, val)
        assert val == VALUENOTSET, err
        super(Announcement, self).__setattr__(key, value)

    def __str__(self):
        return "Announcement<%s, %s, %s, %s, %s, %s, %s>" % (
            self.prefix, self.peer, self.origin,
            self.as_path, self.next_hop, self.local_pref, self.communities
        )

    def copy(self):
        comms = {}
        for comm, fun in self.communities.iteritems():
            comms[comm] = fun
        return Announcement(
            prefix=self.prefix, peer=self.peer, origin=self.origin,
            as_path=self.as_path, next_hop=self.next_hop,
            as_path_len=self.as_path_len, local_pref=self.local_pref,
            med=self.med, communities=comms, permitted=self.permitted)


class BGP_ATTRS_ORIGIN(Enum):
    """Enum of BGP origin types"""
    IGP = 1
    EBGP = 2
    INCOMPLETE = 3


class Access(Enum):
    """Used to in various matches and route maps"""
    permit = 'permit'
    deny = 'deny'


class Community(object):
    """Represent a community value"""

    def __init__(self, value, new_format=True):
        """
        Creates a new community value, e.graph. 40:30
        :param value: the community value, e.graph. 10:20
        :param new_format: if true only accepts 10:30 but not 78
        """
        if isinstance(value, basestring):
            value = Community.string_to_int(value)
        assert isinstance(value, int)
        self._new_format = new_format
        self._value = value

    @property
    def value(self):
        """Community value string, ex. "10:30" """
        if self.is_new_format:
            return self.get_new_format()
        return self._value

    def get_value(self):
        """Get the actual integer value"""
        return self._value

    @property
    def is_new_format(self):
        """
        Returns True if the community is represented in the new BGP format
        """
        return self._new_format

    @staticmethod
    def string_to_int(value):
        assert ":" in value, value
        high, low = value.split(":")
        bin_high = '{0:016b}'.format(int(high))
        bin_low = '{0:016b}'.format(int(low))
        return int(bin_high + bin_low, 2)

    def get_new_format(self):
        bin_num = '{0:032b}'.format(self._value)
        high = int(bin_num[:16], 2)
        low = int(bin_num[16:], 2)
        return "%d:%d" % (high, low)

    @property
    def name(self):
        """String name, to make it easier print"""
        if self.is_new_format:
            val = self.get_new_format()
            val = val.replace(':', '_')
        else:
            val = self.value
        return "Comm_%s" % val

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == getattr(other, 'value', other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        if self.is_new_format:
            val = self.get_new_format()
        else:
            val = self.value
        return "Community(%s)" % val

    def __repr__(self):
        return self.__str__()


class CommunityList(object):
    """Represents a list of communities in a match"""

    def __init__(self, list_id, access, communities):
        assert list_id is None or isinstance(list_id, int)
        assert isinstance(communities, (list, tuple))
        if not (isinstance(access, Access) and access == Access.permit):
            raise NotImplementedError('Only permit access is supported.')
        if communities != [VALUENOTSET]:
            for community in communities:
                assert community == VALUENOTSET or isinstance(community, Community)
        self._list_id = list_id
        self._access = access
        self._communities = communities

    @property
    def list_id(self):
        return self._list_id

    @property
    def access(self):
        return self._access

    @property
    def communities(self):
        return self._communities

    @communities.setter
    def communities(self, value):
        if not all([is_empty(c) for c in self._communities]):
            raise ValueError("Communities already set to %s" % self._communities)
        for community in value:
            assert isinstance(community, Community)
        self._communities = value

    def __eq__(self, other):
        if not isinstance(other, CommunityList):
            return False
        comm_eq = set(self.communities) == set(other.communities)
        access_eq = self.access == other.access
        id_eq = self.list_id == other.list_id
        return id_eq and access_eq and comm_eq

    def __str__(self):
        return "CommunityList(id=%s, access=%s, communities=%s)" % \
               (self.list_id, self.access, self.communities)

    def __repr__(self):
        return self.__str__()


class ASPathList(object):
    """Represents a list of as paths in a match"""

    def __init__(self, list_id, access, as_paths):
        assert isinstance(list_id, int)
        assert isinstance(as_paths, Iterable)
        assert isinstance(access, Access)
        if not is_empty(as_paths):
            for as_path in as_paths:
                assert is_empty(as_path) or isinstance(as_path, int)
        self._list_id = list_id
        self._access = access
        self._as_paths = as_paths

    @property
    def list_id(self):
        return self._list_id

    @property
    def access(self):
        return self._access

    @property
    def as_paths(self):
        return self._as_paths

    @as_paths.setter
    def as_paths(self, value):
        if not is_empty(self._as_paths):
            raise ValueError("AS Paths already set to %s" % self._as_paths)
        for as_path in value:
            assert isinstance(as_path, int)
        self._as_paths = value

    def __eq__(self, other):
        if not isinstance(other, ASPathList):
            return False
        path_eq = set(self.as_paths) == set(other.as_paths)
        access_eq = self.access == other.access
        id_eq = self.list_id == other.list_id
        return id_eq and access_eq and path_eq

    def __str__(self):
        return "ASPathList(id=%s, access=%s, as_path=%s)" % \
               (self.list_id, self.access, self.as_paths)

    def __repr__(self):
        return self.__str__()


class IpPrefixList(object):
    def __init__(self, name, access, networks):
        self.nettype = (IPv4Network, IPv6Network)
        self._types = tuple(list(self.nettype) + [basestring])
        assert isinstance(access, Access)
        assert isinstance(networks, (list, tuple))
        assert not isinstance(networks, self.nettype)
        for net in networks:
            assert isinstance(net, self._types)
        self._networks = networks
        self._name = name
        self._access = access

    @property
    def name(self):
        """Name of the IP prefix list"""
        return self._name

    @property
    def networks(self):
        """List of prefixes"""
        return self._networks

    @networks.setter
    def networks(self, value):
        if not all([is_empty(net) for net in self._networks]):
            raise ValueError("Networks already set to %s" % self._networks)
        for net in value:
            assert isinstance(net, self._types)
        self._networks = value

    @property
    def access(self):
        return self._access

    def __eq__(self, other):
        if not isinstance(other, IpPrefixList):
            return False
        net_eq = set(self.networks) == set(other.networks)
        access_eq = self.access == other.access
        id_eq = self.name == other.name
        return id_eq and access_eq and net_eq

    def __str__(self):
        return "IpPrefixList(id=%s, access=%s, networks=%s)" % \
               (self.name, self.access, self.networks)

    def __repr__(self):
        return self.__str__()


class Match(object):
    """Represent match action in a route map"""

    @property
    def match(self):
        """The value of the match object"""
        raise NotImplementedError()

    @match.setter
    def match(self, value):
        raise NotImplementedError()

    def __eq__(self, other):
        return self.match == getattr(other, 'match', None)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.match)

    def __repr__(self):
        return self.__str__()


class Action(object):
    """Represent an action in route map lines"""
    pass


class MatchCommunitiesList(Match):
    def __init__(self, communities_list):
        assert communities_list == VALUENOTSET or \
               isinstance(communities_list, CommunityList)
        self._match = communities_list

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        assert isinstance(value, CommunityList)
        if self._match != VALUENOTSET:
            raise ValueError("Match already set to %s" % self._match)
        self._match = value


class MatchIpPrefixListList(Match):
    def __init__(self, prefix_list):
        assert prefix_list == VALUENOTSET or \
               isinstance(prefix_list, IpPrefixList)
        self._match = prefix_list

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        assert isinstance(value, IpPrefixList)
        if self._match != VALUENOTSET:
            raise ValueError("Match already set to %s" % self._match)
        self._match = value


class MatchPeer(Match):
    def __init__(self, peer):
        assert peer == VALUENOTSET or isinstance(peer, basestring)
        self._match = peer

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        if not is_empty(self._match):
            raise ValueError("Match already set to %s" % self._match)
        self._match = value


class MatchNextHop(Match):
    def __init__(self, next_hop):
        assert is_empty(next_hop) or isinstance(next_hop, basestring)
        self._match = next_hop

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        if not is_empty(self._match):
            raise ValueError("Match already set to %s" % self._match)
        self._match = value


class MatchLocalPref(Match):
    def __init__(self, local_pref):
        assert is_empty(local_pref) or isinstance(local_pref, int)
        self._match = local_pref

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        if not is_empty(self._match):
            raise ValueError("Match already set to %s" % self._match)
        assert isinstance(value, int)
        self._match = value


class MatchAsPath(Match):
    def __init__(self, as_path):
        assert is_empty(as_path) or isinstance(as_path, Iterable)
        self._match = as_path

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        if not is_empty(self._match):
            raise ValueError("Match already set to %s" % self._match)
        self._match = value


class MatchAsPathLen(Match):
    def __init__(self, as_path_len):
        assert is_empty(as_path_len) or isinstance(as_path_len, int)
        self._match = as_path_len

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        if not is_empty(self._match):
            raise ValueError("Match already set to %s" % self._match)
        self._match = value


class MatchPermitted(Match):
    def __init__(self, access):
        assert is_empty(access) or isinstance(access, Access)
        self._match = access

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        if not is_empty(self._match):
            raise ValueError("Match already set to %s" % self._match)
        self._match = value


class MatchMED(Match):
    def __init__(self, med):
        assert is_empty(med) or isinstance(med, int)
        self._match = med

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        if not is_empty(self._match):
            raise ValueError("Match already set to %s" % self._match)
        assert isinstance(value, int)
        self._match = value


class MatchSelectOne(Match):
    """Allow multiple matches"""

    def __init__(self, matches):
        assert isinstance(matches, Iterable)
        assert matches
        for match in matches:
            assert isinstance(match, Match)
        self._match = matches

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        raise ValueError("Match already set to %s" % str(self._match))

    @staticmethod
    def generate_symbolic(graph, router, num_comms=1, num_prefixes=1, match_types=None):
        if not match_types:
            match_types = [MatchNextHop,
                           MatchIpPrefixListList,
                           MatchCommunitiesList,
                           MatchAsPath,]
        matches = []
        for match_cls in match_types:
            if num_prefixes and match_cls == MatchIpPrefixListList:
                iplist = IpPrefixList(
                    name=None,
                    access=Access.permit,
                    networks=[VALUENOTSET for _ in range(num_prefixes)])
                graph.add_ip_prefix_list(router, iplist)
                match = MatchIpPrefixListList(iplist)
            elif num_comms and match_cls == MatchCommunitiesList:
                clist = CommunityList(
                    list_id=None,
                    access=Access.permit,
                    communities=[VALUENOTSET for _ in range(num_comms)])
                graph.add_bgp_community_list(router, clist)
                match = MatchCommunitiesList(clist)
            else:
                match = match_cls(VALUENOTSET)
            matches.append(match)
        return MatchSelectOne(matches)


class ActionPermitted(Action):
    def __init__(self, access):
        assert is_empty(access) or isinstance(access, Access)
        self._value = access

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % self._value)
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetPermitted(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionSetLocalPref(Action):
    def __init__(self, local_pref):
        assert is_empty(local_pref) or isinstance(local_pref, int)
        self._value = local_pref

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % self._value)
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetLocalPref(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionSetNextHop(Action):
    def __init__(self, next_hop):
        assert is_empty(next_hop) or isinstance(next_hop, basestring)
        self._value = next_hop

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % self._value)
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetNextHop(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionSetPrefix(Action):
    def __init__(self, prefix):
        assert is_empty(prefix) or isinstance(prefix, basestring)
        self._value = prefix

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % self._value)
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetPrefix(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionASPathPrepend(Action):
    """Prepend list of AS Paths"""

    def __init__(self, as_path):
        assert is_empty(as_path) or isinstance(as_path, Iterable)
        self._value = as_path

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % str(self._value))
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "ASPathPrepend(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionSetASPath(Action):
    """Prepend list of AS Paths"""

    def __init__(self, as_path):
        assert is_empty(as_path) or isinstance(as_path, Iterable)
        self._value = as_path

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % str(self._value))
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetASPath(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionSetASPathLen(Action):
    def __init__(self, as_path_len):
        assert is_empty(as_path_len) or isinstance(as_path_len, int)
        self._value = as_path_len

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % self._value)
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetASPathLen(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionSetPeer(Action):
    def __init__(self, peer):
        assert is_empty(peer) or isinstance(peer, basestring)
        self._value = peer

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % self._value)
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetPeer(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionSetMED(Action):
    def __init__(self, med):
        assert is_empty(med) or isinstance(med, int)
        self._value = med

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % self._value)
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetMED(%s)" % self.value

    def __repr__(self):
        return self.__str__()


class ActionSetOne(Action):
    def __init__(self, actions):
        assert actions
        assert isinstance(actions, Iterable)
        for action in actions:
            assert isinstance(action, Action)
        self._value = actions

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not is_empty(self._value):
            raise ValueError("Value already set to %s" % str(self._value))
        self._value = value

    def __eq__(self, other):
        if is_empty(self._value):
            return False
        return self.value == getattr(other, 'value', None)

    def __str__(self):
        return "SetActions(%s)" % self.value

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def generate_symbolic(graph, router, num_comms=1, comm_additiv=True, action_types=None):
        if not action_types:
            action_types = [ActionASPathPrepend,
                            ActionSetNextHop,
                            ActionSetCommunity,
                            ActionSetLocalPref,
                            ActionSetMED,]
        actions = []
        for action_cls in action_types:
            if num_comms and action_cls == ActionSetCommunity:
               action = ActionSetCommunity(
                   communities=[VALUENOTSET for _ in range(num_comms)],
                   additive=comm_additiv)
            else:
                action = action_cls(VALUENOTSET)
            actions.append(action)
        return ActionSetOne(actions)


class ActionString(Action):
    def __init__(self, value):
        assert isinstance(value, basestring)
        self._value = value

    @property
    def value(self):
        return self._value


class ActionSetCommunity(Action):
    def __init__(self, communities, additive=True):
        """
        Set a list of communities to a route
        :param communities: list of Community
        :param additive:
        """
        assert isinstance(communities, Iterable)
        for community in communities:
            assert is_empty(community) or isinstance(community, Community)
        self._communities = communities
        self._additive = additive

    @property
    def communities(self):
        return self._communities

    @property
    def additive(self):
        return self._additive

    def __eq__(self, other):
        return set(self._communities) == set(getattr(other, '_communities', []))

    def __str__(self):
        return "SetCommunity(%s)" % self._communities

    def __repr__(self):
        return self.__str__()


class RouteMapLine(object):
    """A single route map line"""

    def __init__(self, matches, actions, access, lineno=None):
        if matches is None:
            matches = []
        if actions is None:
            actions = []
        assert isinstance(matches, Iterable)
        assert isinstance(actions, Iterable)
        for match in matches:
            assert isinstance(match, Match), "Expected a match but found %s" % match
        for action in actions:
            assert isinstance(action, Action)
        assert is_empty(access) or isinstance(access, Access)

        self._matches = matches
        self._actions = actions
        self._access = access
        self._lineno = lineno

    @property
    def matches(self):
        """Matches in this line"""
        return self._matches

    @property
    def actions(self):
        """List of actions to be taken by this line"""
        return self._actions

    @property
    def access(self):
        """Permit or drop (see Access)"""
        return self._access

    @access.setter
    def access(self, value):
        """Set to drop to allow (see Access)"""
        if not is_empty(self._access):
            raise ValueError("Access already set to %s" % self._access)
        assert isinstance(value, Access)
        self._access = value

    @property
    def lineno(self):
        """Return the line no of this line"""
        return self._lineno

    def __eq__(self, other):
        matches = getattr(other, 'matches', None)
        actions = getattr(other, 'actions', None)
        access = getattr(other, 'access', None)
        lineno = getattr(other, 'lineno', None)
        return self.matches == matches and \
            self.actions == actions and \
            self.access == access and \
            self.lineno == lineno

    def __str__(self):
        return "lineno: %d\n\taccess: %s, \n\tMatches: \n\t\t%s, \n\tActions: \n\t\t%s>" \
               % (self.lineno, self.access, self.matches, self.actions)

    def __repr__(self):
        return "<lineno: %d, access: %s, Matches: %s, Actions: %s>" \
               % (self.lineno, self.access, self.matches, self.actions)


class RouteMap(object):
    """
    Route Map
    """

    def __init__(self, name, lines):
        assert isinstance(name, basestring)
        assert isinstance(lines, Iterable)
        for line in lines:
            assert isinstance(line, RouteMapLine)
        self._name = name
        self._lines = lines

    @property
    def name(self):
        """The name of the route map"""
        return self._name

    @property
    def lines(self):
        """Return the route map lines"""
        return self._lines

    def __eq__(self, other):
        return self.name == getattr(other, 'name', None) and \
               self.lines == getattr(other, 'lines', None)

    def __str__(self):
        ret = "RouteMap %s\n" % self.name
        for line in self.lines:
            ret += "\t%s\n" % line
        return ret

    def __repr__(self):
        return self.__str__()
