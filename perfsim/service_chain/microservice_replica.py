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

from typing import TYPE_CHECKING, Tuple, Dict

import numpy as np

from perfsim import ReplicaThread, Process, MicroserviceEndpointFunction

if TYPE_CHECKING:
    from perfsim import Host, Microservice, Request


class MicroserviceReplica:
    microservice: Microservice

    def __init__(self, name: str, microservice: Microservice):
        self.cpu_limits_ns = None
        self.name = name
        self.__host = None
        self.microservice = microservice
        self.process = Process(pname=name,
                               cpu_requests_share=microservice.cpu_requests,
                               cpu_limits=microservice.cpu_limits,
                               memory_capacity=microservice.memory_requests,
                               ingress_bw=microservice.ingress_bw,
                               egress_bw=microservice.egress_bw,
                               ingress_latency=microservice.ingress_latency,
                               egress_latency=microservice.egress_latency,
                               blkio_capacity=microservice.blkio_capacity,
                               endpoint_functions=microservice.endpoint_functions,
                               ms_replica=self)  # self, self.cgroup)
        self.last_thread_id = 0

    # def set_reserved_cpu_limits_ns(self) -> None:
    #     if self.host is not None:
    #         self.cpu_limits_ns = (self.host.cfs_period_ns *
    #                                  self.microservice.cpu_limits) / self.host.cpu.max_cpu_requests

    def reinit(self):
        self.__init__(self.name, self.microservice)

    @property
    def host(self) -> Host:
        return self.__host

    @host.setter
    def host(self,
             host: Host):
        if host != self.host:
            if self.host is not None:
                self.host.evict_replica(self)

            if host is not None:
                host.place_replica(self)

            self.__host = host
            self.microservice.hosts.append(host)
            # self.set_reserved_cpu_limits_ns()

    @property
    def microservice(self) -> Microservice:
        return self.__microservice

    @microservice.setter
    def microservice(self, microservice: Microservice):
        self.__microservice = microservice
        # self.set_reserved_cpu_limits_ns()

    def __str__(self):
        return self.name

    def remove_host_without_eviction(self) -> None:
        if self.host is not None:
            self.host.evict_replica(self)
        self.__host = None

    def reserve_egress_bw(self, bw: float):
        self.process.egress_bw -= bw if bw > self.process.egress_bw else 0

    def release_egress_bw(self, bw: float):
        self.process.egress_bw += bw

        if self.process.egress_bw > self.process.original_egress_bw:
            self.process.egress_bw = self.process.original_egress_bw

    def reserve_ingress_bw(self, bw: float):
        self.process.ingress_bw -= bw if bw > self.process.ingress_bw else 0

    def release_ingress_bw(self, bw: float):
        self.process.ingress_bw += bw

        if self.process.ingress_bw > self.process.original_ingress_bw:
            self.process.ingress_bw = self.process.original_ingress_bw

    def generate_threads(self,
                         from_subchain_id: int,
                         node_in_subchain: Tuple[int, MicroserviceEndpointFunction],
                         replica_identifier_in_subchain: int,
                         load_balance: bool = False,
                         parent_request: Request = None) -> Dict[str, ReplicaThread]:
        threads_dict: Dict[str, ReplicaThread] = {}

        for _ in np.arange(node_in_subchain[1].threads_count):  #: node_in_subchain[1] == the endpoint function
            _thread = ReplicaThread(process=self.process,
                                    replica=self,
                                    replica_identifier_in_subchain=replica_identifier_in_subchain,
                                    node_in_alt_graph=node_in_subchain,
                                    thread_id_in_node=_,
                                    subchain_id=from_subchain_id,
                                    average_load=node_in_subchain[1].threads_avg_cpu_usages[_],
                                    parent_request=parent_request)
            threads_dict[str(_thread.id)] = _thread

            # TODO: To optimize execution we should have active_hosts concept so that it only iterates on active hosts
            # parent_request.cluster.cluster_scheduler.active_hosts.add(self.host)

        self.host.cpu.cores[0].runqueue.enqueue_tasks(threads=list(threads_dict.values()), load_balance=load_balance)

        return threads_dict
