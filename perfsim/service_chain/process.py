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

import copy
from typing import TYPE_CHECKING, Dict, Set

if TYPE_CHECKING:
    from perfsim import MicroserviceEndpointFunction, ReplicaThread, MicroserviceReplica


class Process:
    """
    Process class is used to represent a process in the system.
    """

    threads: Set[ReplicaThread]

    _cpu_requests_share: int

    _cpu_limits: int

    def __init__(self,
                 pname: str,
                 cpu_requests_share: int,
                 cpu_limits: int,
                 memory_capacity: int,
                 ingress_bw: int,
                 egress_bw: int,
                 ingress_latency: float,
                 egress_latency: float,
                 blkio_capacity: int,
                 endpoint_functions: Dict[str, MicroserviceEndpointFunction],
                 ms_replica: MicroserviceReplica):
        self.pname = pname
        self.__original_cpu_requests_share = cpu_requests_share
        self.total_used_share = 0
        self._cpu_requests_share = cpu_requests_share
        self._cpu_limits = cpu_limits
        self.endpoint_functions = copy.copy(endpoint_functions)
        self.memory_capacity = memory_capacity
        self.original_ingress_bw = ingress_bw
        self.ingress_bw = ingress_bw
        self.original_egress_bw = egress_bw
        self.egress_bw = egress_bw
        self.ingress_latency = ingress_latency
        self.egress_latency = egress_latency
        self.blkio_capacity = blkio_capacity
        self.active_incoming_transmissions = set()
        self.active_outgoing_transmissions = set()
        # self.avg_cpi = avg_cpi
        # self.original_threads_count = threads_count
        self.active_threads_count = 0
        self.threads = set()
        self.ms_replica = ms_replica

    @property
    def active_threads_count(self):
        return self.__active_threads_count

    @active_threads_count.setter
    def active_threads_count(self, v):
        self.__active_threads_count = v

    @property
    def original_cpu_requests_share(self):
        return self.__original_cpu_requests_share

    @original_cpu_requests_share.setter
    def original_cpu_requests_share(self, v):
        raise Exception(
            "Cannot set original cpu_requests_share! It's read only and should only be set in the constructor.")

    @property
    def cpu_requests_share(self):
        return self._cpu_requests_share

    @cpu_requests_share.setter
    def cpu_requests_share(self, v):
        self._cpu_requests_share = v

    @property
    def cpu_limits(self):
        return self._cpu_limits

    @cpu_limits.setter
    def cpu_limits(self, v):
        if v < self._cpu_requests_share:
            raise Exception("CPU limits cannot be less than CPU requests share!")
        else:
            self._cpu_limits = v

    def get_cpu_request_per_thread(self):
        if self.active_threads_count == 0:
            return None

        if self.ms_replica.microservice.is_unlimited_burstable() or self.ms_replica.microservice.is_guaranteed():
            share_per_thread = self.cpu_requests_share / self.active_threads_count
        elif self.ms_replica.microservice.is_limited_burstable():
            share_per_thread = self.cpu_limits / self.active_threads_count
        elif self.ms_replica.microservice.is_best_effort():
            share_per_thread = self.ms_replica.host.cpu.max_cpu_requests / self.active_threads_count
        else:
            raise Exception("Unknown microservice type!")

        return min(share_per_thread, self.ms_replica.host.cpu.max_cpu_requests)
