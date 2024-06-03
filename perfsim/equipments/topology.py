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

from copy import deepcopy
from typing import TYPE_CHECKING, Dict

from perfsim import Host, Router, Transmission, Observable, TopologyPrototype, TopologyLogObserver, TopologyLink

if TYPE_CHECKING:
    from perfsim import Simulation


class Topology(TopologyPrototype, Observable):
    """
    This class represents a network topology. A network topology is the arrangement of the various elements (links,
    nodes, etc.) of a computer network. It has a name and a dictionary of nodes (hosts and routers) that are part of the
    topology.
    """

    #: The dictionary of hosts that are part of the topology. The key is the host name and the value is the host object.
    before_recalculate_transmissions_bw_on_all_links: str

    def __init__(self,
                 name: str,
                 simulation: 'Simulation',
                 egress_err: float,
                 ingress_err: float,
                 incoming_graph_data=None,
                 hosts: Dict[str, Host] = None,
                 routers: Dict[str, Router] = None,
                 links: Dict[str, TopologyLink] = None,
                 copy: bool = False,
                 **attr):
        if copy:
            hosts = deepcopy(hosts)
            routers = deepcopy(routers)
            if links is not None:
                for link in links.values():
                    link.source = TopologyLink.get_node_from_dicts_by_name(node=link.source,
                                                                           hosts_dict=hosts,
                                                                           routers_dict=routers)
                    link.destination = TopologyLink.get_node_from_dicts_by_name(node=link.destination,
                                                                                hosts_dict=hosts,
                                                                                routers_dict=routers)

        super().__init__(name=name,
                         egress_err=egress_err,
                         ingress_err=ingress_err,
                         incoming_graph_data=deepcopy(incoming_graph_data) if copy else incoming_graph_data,
                         hosts=hosts,
                         routers=routers,
                         links=links,
                         **attr)
        self.sim = simulation
        Observable.__init__(self)
        if self.sim.debug_level > 0:
            self.attach_observer(TopologyLogObserver(topology=self))

    def register_events(self):
        """
        Register the events for the topology.

        :return:
        """

        self.register_event(event_name="before_recalculate_transmissions_bw_on_all_links")

    def recalculate_transmissions_bw_on_all_links(self):
        """
        Recalculate the bandwidth of all the transmissions on all the links in the topology.

        :return:
        """

        all_modified_transmissions = set()

        self.notify_observers(event_name=self.before_recalculate_transmissions_bw_on_all_links)

        # for edge in self.edges:
        for edge in self.active_edges:
            edge_data = self.get_edge_data(edge[0], edge[1])[0]
            is_edge_modified = self.recalculate_transmissions_portion_of_bandwidth_on_link(edge)

            for transmission in edge_data["transmissions"]:
                if is_edge_modified or transmission.current_bw is None:
                    # if transmission not in all_modified_transmissions:
                    all_modified_transmissions.add(transmission)
                    new_bw = transmission.calculate_requested_bw()
                    transmission.set_current_bw(new_bw=new_bw, edge_data=edge_data)

        for edge in self.zombie_edges:
            self.recalculate_transmissions_portion_of_bandwidth_on_link(edge)

        self.zombie_edges = set()

        # If we only check modified transmissions, we can have a problem with the transmission times.
        self.recalculate_transmissions_times(self.active_transmissions)

    def recalculate_transmissions_portion_of_bandwidth_on_link(self, link):
        """
        Recalculate the bandwidth portion of all the transmissions on the given link.

        :param link:
        :return:
        """

        edge_data = self.get_edge_data(link[0], link[1])[0]

        """
        A link has a maximum bandwidth
        """
        link_bw = Transmission.get_bandwidth_on_link(link[0], link[1])

        if len(edge_data["transmissions"]) == 0:
            edge_data["transmissions_portion_of_bandwidth"] = link_bw
            return

        """
        An active transmission on a link, has a maximum portion of bandwidth. At the beginning, this portion is
         equal to link_bw/count(transmission).
        """
        portion_of_bandwidth = link_bw / len(edge_data["transmissions"])

        """ 
        Transmissions will be considered as best_effort if they request to exceeds their portion
        """
        best_effort_transmissions_count = 0

        """
        If other transmissions choose to use lower bandwidth than their available portion, then their extra portion
         will be shared among best_effort transmissions.
        """
        unused_portions = 0
        sum_requested_bw = 0

        for transmission in edge_data["transmissions"]:
            transmission.calculate_requested_bw()
            if transmission.requested_bw > portion_of_bandwidth:
                best_effort_transmissions_count += 1
            else:
                unused_portions += portion_of_bandwidth - transmission.requested_bw
                # sum_requested_bw += transmission.requested_bw

        if best_effort_transmissions_count != 0:
            """
            Recalculating bandwidth portion of best_effort transmissions based on unused portions 
            """
            # portion_of_bandwidth = (link_bw - sum_requested_bw) / best_effort_transmissions_count
            portion_of_bandwidth += unused_portions / best_effort_transmissions_count
        # else:
        #     best_effort_bw = 0

        modified = False
        if portion_of_bandwidth != edge_data["transmissions_portion_of_bandwidth"]:
            modified = True
            edge_data["transmissions_portion_of_bandwidth"] = portion_of_bandwidth

        return modified

    @classmethod
    def from_prototype(cls, simulation: Simulation, prototype: TopologyPrototype, copy: bool = False):
        """
        Create a new topology from a prototype.

        :param simulation:
        :param prototype:
        :param copy:
        :return:
        """

        return cls(name=prototype.name,
                   simulation=simulation,
                   egress_err=prototype.egress_err,
                   ingress_err=prototype.ingress_err,
                   incoming_graph_data=prototype.incoming_graph_data,
                   hosts=prototype.hosts_dict,
                   routers=prototype.routers_dict,
                   links=prototype.topology_links_dict,
                   copy=copy,
                   **prototype.attr)
