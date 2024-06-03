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

from typing import TYPE_CHECKING, Union, Dict, Tuple

import networkx as nx
import numpy as np

from perfsim import Transmission

# from overloading import overload

if TYPE_CHECKING:
    from perfsim import Host, Request, MicroserviceEndpointFunction, MicroserviceReplica, Router


class Nic:
    """
    This class represents a Network Interface Card (NIC) in a host or a router. A NIC is a hardware component that
    connects the host or router to the network. It has a bandwidth that determines the maximum amount of data that can
    be transmitted over the network. The NIC can reserve and release bandwidth for transmissions.
    """

    #: A name for the NIC
    name: str

    #: The parent equipment object. E.g., the host or router object that this NIC belongs to it
    equipment: Union[Host, Router]

    #: Nic's bandwidth (Bps)
    bandwidth: int

    #: A dictionary consisting of all active transmissions, that can be accessed by tuple (subchain_id, request) as keys
    transmissions: Dict[(int, Request)]

    #: The total bandwidth requests on this NIC. Useful for scoring hosts.
    bandwidth_requests_total: int

    def __init__(self,
                 name: str,
                 bandwidth: int,
                 equipment: Union[Host, Router]):
        # super().__init__.py("nic", "nic_" + name, True, "bytes", bandwidth)
        self.name = name
        self.equipment = equipment
        self.bandwidth = bandwidth  # bytes per second
        self.transmissions = {}
        self.bandwidth_requests_total = 0

    # type hinting in overloading module is not compatible with python 3.7 annotations
    # @overload
    # def reserve_transmission(self, request):
    def reserve_transmission_for_request(self,
                                         request: Request,
                                         subchain_id: int,
                                         src_replica: MicroserviceReplica,
                                         source_node: Tuple[int, MicroserviceEndpointFunction],
                                         destination_replica: MicroserviceReplica,
                                         destination_node: Tuple[int, MicroserviceEndpointFunction]):
        if (subchain_id, request) not in self.transmissions:
            _link_data = request.scm.service_chain.get_edge_data(source_node[1], destination_node[1])
            self.transmissions[(subchain_id, request)] = \
                Transmission(id=self.equipment.cluster.sim.load_generator.last_transmission_id,
                             payload_size=_link_data[next(iter(_link_data))]["payload"],
                             src_replica=src_replica,
                             dst_replica=destination_replica,
                             subchain_id_request_pair=(request, subchain_id),
                             recalculate_bandwidths_in_links=False)
            self.transmissions[(subchain_id, request)].topology.active_transmissions.add(
                self.transmissions[(subchain_id, request)])

            self.equipment.cluster.sim.load_generator.last_transmission_id += 1
            return self.transmissions[(subchain_id, request)]
            # return self.requests[(subchain_id, request)].calculate_transmission_time()
        else:
            raise Exception("A request already exists in the NIC for (subchain_id, request) pair (" +
                            str(subchain_id) + ", " + str(request) + ")!")

    # type hinting in overloading module is not compatible with python 3.7 annotations
    # @overload
    # def release_transmission(self, request):
    def release_transmission_for_request(self, request: Request, subchain_id: int):
        if (subchain_id, request) in self.transmissions:
            result = self.release_transmission_in_nic(
                payload_size=self.transmissions[(subchain_id, request)],
                destination_nic=request._next_replicas_in_nodes[subchain_id][1].host.nic["ingress"])
            self.transmissions[(subchain_id, request)].finish()
            del self.transmissions[(subchain_id, request)]
            return result
        else:
            raise Exception(
                "NIC is trying to release a transmission for a request which is not exists. What the hell?!")
            # return True

    # type hinting in overloading module is not compatible with python 3.7 annotations
    # @overload
    # def reserve_transmission(self, payload_size, destination_nic):
    def reserve_transmission_in_nic(self,
                                    payload_size: float,
                                    src_replica: MicroserviceReplica,
                                    destination_replica: MicroserviceReplica):
        _transmission_time = self.calculate_transmission_time(payload_size=payload_size,
                                                              src_replica=src_replica,
                                                              destination_replica=destination_replica)
        if _transmission_time != 0:
            _destination_nic = destination_replica.host.nic["ingress"]
            _destination_nic.reserve(payload_size)
            return _transmission_time
        else:
            return False

    # type hinting in overloading module is not compatible with python 3.7 annotations
    # @overload
    # def release_transmission(self, payload_size, destination_nic):
    def release_transmission_in_nic(self, payload_size, destination_nic):
        return True

    def calculate_transmission_time(self,
                                    payload_size: float,
                                    src_replica: MicroserviceReplica,
                                    destination_replica: MicroserviceReplica) -> Union[int, float]:
        """
        This method calculates the transmission time between two replicas. It calculates the transmission time based on
        the minimum bandwidth between the source and destination replicas, the minimum bandwidth between the source and
        destination hosts, and the minimum bandwidth between the source and destination NICs. The transmission time is
        calculated as the time it takes to transmit the payload over the minimum bandwidth.

        :param payload_size:
        :param src_replica:
        :param destination_replica:
        :return:
        """

        if self.host.cluster.sim.debug:
            self.host.cluster.sim.logger.log(
                "     ***** [NIC] Calculating transmission time between " +
                str(self.host.name) + " -> " + str(destination_replica.host.name), 3)

        _destination_nic = destination_replica.host.nic["ingress"]
        if self == _destination_nic:
            if self.host.cluster.sim.debug:
                self.host.cluster.sim.logger.log("      ****** Transmission time = 0", 3)
            return 0
        else:
            min_host_bw = self.bandwidth if self.bandwidth < _destination_nic.bandwidth else _destination_nic.bandwidth
            min_replica_bw = src_replica.process.egress_bw \
                if src_replica.process.egress_bw < destination_replica.process.ingress_bw \
                else destination_replica.process.ingress_bw
            min_bw = min_host_bw if min_host_bw < min_replica_bw else min_replica_bw

            transmission_time = (payload_size / min_bw) * 1000000000
            path = nx.shortest_path(self.host.cluster.topology, self.host, _destination_nic.host)
            edges = list(zip(path, path[1:]))
            path_len = len(path)
            latency = 0
            transmission_str = ""

            for node_id in np.arange(path_len - 1):
                if isinstance(path[node_id], Router):
                    latency += path[node_id].latency
                    transmission_str += str(path[node_id].latency) + " + "

                link_data = self.host.cluster.topology.get_edge_data(path[node_id], path[node_id + 1])[0]
                latency += link_data['latency']
                transmission_str += str(link_data['latency']) + " + "

            transmission_str += str(transmission_time)
            transmission_time += latency

            if self.host.cluster.sim.debug:
                self.host.cluster.sim.logger.log("      ****** Transmission time = " + str(
                    transmission_str) + " = " + str(transmission_time), 3)

            return transmission_time  # if not 0 <= transmission_time < 1 else 1  # in nanoseconds

    def dismiss_bw(self, bandwidth_request):
        """
        This method is used to dismiss the bandwidth request from the NIC. It is used when the transmission is finished.

        :param bandwidth_request:
        :return:
        """

        self.bandwidth_requests_total -= bandwidth_request
        if self.bandwidth_requests_total < 0:
            raise Exception("The NIC " + str(self) +
                            " is trying to release more bandwidth requestes than overally requested from this NIC")

    def request_bw(self, bandwidth_request):
        """
        This method is used to request bandwidth from the NIC. It is used when a transmission is started.

        :param bandwidth_request:
        :return:
        """
        self.bandwidth_requests_total += bandwidth_request

    def get_available(self):
        """
        This simply returns the difference between the NIC's total bandwidth and requested bandwidth. If available bandwidth
        is less than 0, it returns 0.

        :return:
        """

        available = self.bandwidth - self.bandwidth_requests_total
        return self.bandwidth if self.bandwidth_requests_total > self.bandwidth else available
