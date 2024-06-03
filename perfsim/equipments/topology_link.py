#  Copyright (C) 2020 Michel Gokan Khan
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#  This file is a part of the PerfSim project, which is now open source and available under the GPLv2.
#  Written by Michel Gokan Khan, February 2020


from __future__ import annotations

from typing import Union

from perfsim import TopologyLinkPrototype, Host, Router


class TopologyLink(TopologyLinkPrototype):
    """
    This class represents a link between two nodes in a network topology. It has a latency and a bandwidth.
    """

    def __init__(self,
                 name: str,
                 latency: int,
                 # bandwidth: int,
                 source: Union[Host, Router],
                 destination: Union[Host, Router]):
        super().__init__(name=name, latency=latency)  # , bandwidth)
        self.name = name
        self.source = source
        self.destination = destination

    @classmethod
    def from_prototype(cls,
                       name: str,
                       prototype: TopologyLinkPrototype,
                       src: Union[Host, Router],
                       dest: Union[Host, Router]):
        """
        Create a new TopologyLink object from a TopologyLinkPrototype object.

        :param name:
        :param prototype:
        :param src:
        :param dest:
        :return:
        """

        return cls(name=name,
                   latency=prototype.latency,
                   # prototype.bandwidth,
                   source=src,
                   destination=dest)

    @staticmethod
    def to_dict(links_list: list[TopologyLink]) -> dict[str, TopologyLink]:
        """
        Convert a list of TopologyLink objects to a dictionary where the key is the name of the link and the value is the
        link object.

        :param links_list:
        :return:
        """

        links_dict = {}

        for link in links_list:
            links_dict[link.name] = link

        return links_dict

    @staticmethod
    def get_node_from_dicts_by_name(node: Union[Host, Router],
                                    hosts_dict: dict[str, Host],
                                    routers_dict: dict[str, Router]):
        """
        Get the node object from the hosts and routers dictionaries by the name of the node.

        :param node:
        :param hosts_dict:
        :param routers_dict:
        :return:
        """

        if type(node) is Host:
            return hosts_dict[node.name]
        elif type(node) is Router:
            return routers_dict[node.name]
        else:
            raise Exception("Unknown node type " + str(type(node)) + " in link ")
