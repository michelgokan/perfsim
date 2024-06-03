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

from typing import TYPE_CHECKING, List, Tuple, Union, Dict, Any

import networkx as nx

from perfsim import Observable, TransmissionLogObserver

if TYPE_CHECKING:
    from perfsim import MicroserviceReplica, Request


class Transmission(Observable):
    def __init__(self,
                 id: int,
                 payload_size: float,  # in bytes
                 src_replica: MicroserviceReplica,
                 dst_replica: MicroserviceReplica,
                 subchain_id_request_pair: Tuple[Request, int],
                 recalculate_bandwidths_in_links: bool = False):
        from perfsim import Router

        self.id = id
        self.original_payload_size = payload_size
        self.remaining_payload_size = payload_size
        self.src_replica = src_replica
        self.dst_replica = dst_replica
        self.src_replica.process.active_outgoing_transmissions.add(self)
        self.dst_replica.process.active_incoming_transmissions.add(self)
        self.topology = self.src_replica.host.cluster.topology
        self.subchain_id_request_pair = subchain_id_request_pair
        self._source_nic = self.src_replica.host.nic["egress"]
        self._dest_nic = self.dst_replica.host.nic["ingress"]
        self.__path = nx.shortest_path(G=self._source_nic.equipment.cluster.topology,
                                       source=self._source_nic.equipment,
                                       target=self._dest_nic.equipment)
        self.__links = list(zip(self.__path, self.__path[1:]))
        self.__links_data = [self.get_link_data(_) for _ in self.__links]
        self.__links_accumulated_latency = sum([_["latency"] for _ in self.__links_data])
        self.__intermediate_routers = set(node for node in sum(self.links, ()) if isinstance(node, Router))
        self.__intermediate_routers_accumulated_latency = sum(router.latency for router in self.__intermediate_routers)
        self.total_latency = self.__links_accumulated_latency + self.__intermediate_routers_accumulated_latency + self.src_replica.process.egress_latency + self.dst_replica.process.ingress_latency
        self.current_link_id = 0
        self.requested_bw = None  # The bandwidth that transmission originally requested
        self._current_bw = self.requested_bw if len(self.__links) != 0 else float('inf')  # The actual bw of this trans
        self.__add_self_to_links(recalculate_bandwidths_in_links)
        self.transmission_time = None
        self.transmission_exact_time = None
        super().__init__()
        if self.src_replica.host.cluster.sim.debug_level > 0:
            self.attach_observer(TransmissionLogObserver(transmission=self))

    def register_events(self):
        self.register_event(event_name="on_current_bw_change")

    def __add_self_to_links(self, recalculate_bandwidths_in_links):
        for link in self.__links:
            _link = self.src_replica.host.cluster.topology[link[0]][link[1]][0]
            _link["transmissions"].add(self)
            self.topology.active_edges.add(link)

        if recalculate_bandwidths_in_links:
            # TODO: only recalculate incoming+outgoing links of intermediate nodes
            self.src_replica.host.cluster.topology.recalculate_transmissions_bw_on_all_links()

    def get_link_data(self, link):
        """
        Get the data of a link.

        :param link:
        :return:
        """

        return self.src_replica.host.cluster.topology.get_edge_data(link[0], link[1])[0]

    @staticmethod
    def recalc_bw_considering_err(bandwidth: float, error: float):
        return bandwidth - bandwidth * error

    def calculate_requested_bw(self):
        """
        Calculate the requested bandwidth of this transmission.

        :return:
        """

        requested_bw = 0

        if self._source_nic.equipment is not self._dest_nic.equipment:
            egress_bw = self.recalc_bw_considering_err(self.src_replica.process.egress_bw, self.topology.egress_err)
            ingress_bw = self.recalc_bw_considering_err(self.dst_replica.process.ingress_bw, self.topology.ingress_err)

            tpob = [link_data["transmissions_portion_of_bandwidth"] for link_data in self.__links_data]
            # :Assuming that link_data["transmissions_portion_of_bandwidth"] is up-to-date before calling this function
            requested_bw = min(
                # *[Transmission.get_bandwidth_on_link(_[0], _[1]) for _ in self.__links],
                *tpob,
                self._source_nic.bandwidth,
                self._dest_nic.bandwidth,
                egress_bw / len(self.src_replica.process.active_outgoing_transmissions),
                ingress_bw / len(self.dst_replica.process.active_incoming_transmissions))
        # self._source_nic.host.cluster.sim.logger.log("      ****** Transmission time = 0", 3)

        self.requested_bw = requested_bw
        return requested_bw

    def transmit(self, duration: float):
        self.notify_observers(event_name="on_all_transmissions_start", duration=duration)

        if self.total_latency > 0:
            if duration > self.total_latency:
                duration -= self.total_latency
                self.total_latency = 0
            else:
                self.total_latency -= duration
                return self.calculate_transmission_time()

        if self.current_bw != float('inf'):
            _bytes_of_data_to_be_transmitted = self.current_bw * (duration / 1000000000)
            self.remaining_payload_size -= _bytes_of_data_to_be_transmitted  # * 1000000000 #in nanoseconds
        else:
            _bytes_of_data_to_be_transmitted = self.remaining_payload_size
            self.remaining_payload_size = 0

        if -1 < self.remaining_payload_size < 1:
            self.remaining_payload_size = 0
        elif self.remaining_payload_size < 0:
            raise Exception("remaining_payload_size is less than zero! Something is wrong! Probably a bug.")

        _transmission_time = self.calculate_transmission_time()
        self.notify_observers(event_name="on_all_transmissions_end",
                              duration=duration,
                              bytes_of_data_transmitted=_bytes_of_data_to_be_transmitted)

        return _transmission_time

    @property
    def links(self) -> List:
        return self.__links

    def calculate_transmission_time(self) -> float:
        self.notify_observers(event_name="on_transmission_time_calculation")

        if self._source_nic.equipment is self._dest_nic.equipment:
            self.transmission_time = 0
        else:
            # min_host_bw = self.current_bw if self.current_bw < self._dest_nic.bandwidth else self._destination_nic.bandwidth
            # min_replica_bw = self.src_replica.process.egress_bw \
            #     if self.src_replica.process.egress_bw < self.dst_replica.process.ingress_bw \
            #     else self.dst_replica.process.ingress_bw
            # min_bw = min_host_bw if min_host_bw < min_replica_bw else min_replica_bw
            self.transmission_time = (self.remaining_payload_size / self.current_bw) * 1000000000 + self.total_latency

        self.transmission_exact_time = self.transmission_time + self.src_replica.host.cluster.sim.time
        self.notify_observers(event_name="on_after_transmission_time_calculation")

        return self.transmission_time
        # transmission_time = (self.remaining_payload_size / self.current_bw) * 1000000000 + self.total_latency
        # path_len = len(path)
        # latency = 0
        # transmission_str = ""
        #
        # for node_id in np.arange(path_len - 1):
        #     if isinstance(path[node_id], Router):
        #         latency += path[node_id].latency
        #         transmission_str += str(path[node_id].latency) + " + "
        #
        #     link_data = self.host.cluster.topology.get_edge_data(path[node_id], path[node_id + 1])[0]
        #     latency += link_data['latency']
        #     transmission_str += str(link_data['latency']) + " + "
        #
        # transmission_str += str(transmission_time)
        #
        # # for edge in edges:
        # #     self.host.cluster.topology.get_edge_data()
        # #     latency += edge['latency']
        # transmission_time += latency
        #
        # self.host.cluster.sim.logger.log("      ****** Transmission time = " + str(transmission_str) +
        #                                             " = " + str(transmission_time), 3)
        #
        # return transmission_time  # if not 0 <= transmission_time < 1 else 1  # in nanoseconds

    def finish(self):
        if self.src_replica.host.cluster.sim.debug:
            self.src_replica.host.cluster.sim.logger.log("       ******* Finishing transmission " +
                                                         str(self), 10)
        self.src_replica.process.active_outgoing_transmissions.remove(self)
        self.dst_replica.process.active_incoming_transmissions.remove(self)
        for link in self.__links:
            _link = self.src_replica.host.cluster.topology[link[0]][link[1]][0]
            _link["transmissions"].remove(self)
            if len(_link["transmissions"]) == 0:
                self.topology.active_edges.remove(link)
                self.topology.zombie_edges.add(link)
        self.topology.active_transmissions.remove(self)

    @staticmethod
    def get_bandwidth_on_link(source, destination):
        # from perfsim import MicroserviceReplica
        source_type = type(source).__name__
        destination_type = type(destination).__name__

        if source_type == "Host" and destination_type == "Router":
            bandwidth = min(source.nic["egress"].bandwidth, destination.get_nics_by_host(source)["ingress"].bandwidth)
        elif source_type == "Router" and destination_type == "Host":
            bandwidth = min(source.get_nics_by_host(destination)["egress"].bandwidth,
                            destination.nic["ingress"].bandwidth)
        elif source_type == "MicroserviceReplica" and destination_type == "Host":
            bandwidth = min(source.process.egress_bw, destination.nic["ingress"].bandwidth)
        elif source_type == "Host" and destination_type == "MicroserviceReplica":
            bandwidth = min(source.nic["egress"].bandwidth, destination.process.ingress_bw)
        elif source_type == "Router" and destination_type == "Router":
            bandwidth = min(source.get_nics_by_router(destination)["egress"].bandwidth,
                            destination.get_nics_by_router(source)["ingress"].bandwidth)
        else:
            raise Exception(
                "Source or destination of this topology is not a valid type ({}. {})".format(source_type,
                                                                                             destination_type))

        return bandwidth

    @property
    def source_nic(self):
        return self._source_nic

    @property
    def dest_nic(self):
        return self._dest_nic

    @property
    def current_bw(self):
        return self._current_bw

    @current_bw.setter
    def current_bw(self, value):
        self._current_bw = value

    def set_current_bw(self, new_bw: Union[int, float], edge_data: Dict[str, Any]):
        self.notify_observers(event_name="on_current_bw_change", new_bw=new_bw, edge_data=edge_data)
        self._current_bw = new_bw

    def __str__(self):
        return str(self.id)
