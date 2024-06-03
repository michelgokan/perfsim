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


"""
A Host object simulates a single host in a cluster. It has a single CPU and a
single NIC. Number of cores in its CPU can be specifies using the *cores_count*
property and its maximum network bandwidth can be specified with the *max_bandwidth*
property.
"""
from typing import Dict

from perfsim import Settings, CostDict


class HostPrototype:
    """A `Host` may contain several `Microservices`.
    Here are the possible initialization parameters:

        `name`
            Name of the host. In example host1.

        `cores_count`
            Number of cores that this host's CPU contains. It will create a CPU
             with the given number of cores (can be accessed via self.Cpu). Currently it's
             been assumed that each *Host* only has 1 *CPU*.

        `cpu_clock_rate`
            The maximum clock rate of the CPU for this host (in Hertz).

        `max_bandwidth`
            Maximum bandwidth that this host's NIC can support. During initiallization,
            a `Nic` object with the given bandwidth is being created. (can be accessed
            via self.Nic)
    """

    #: The cost of running this host per minute
    cost_dict: CostDict

    def __init__(self,
                 name: str,
                 cpu_core_count: int,
                 cpu_clock_rate: int,
                 memory_capacity: int,
                 ram_speed: int,
                 storage_capacity: int,
                 storage_speed: int,
                 network_bandwidth: int,
                 # number_of_gpus,
                 sched_latency_ns: int = Settings.args.loc['sched_latency_ns']['min'],
                 sched_min_granularity_ns: int = Settings.args.loc['sched_min_granularity_ns']['min'],
                 cfs_period_ns: int = Settings.args.loc['cfs_period_ns']['min'],
                 cost_dict: CostDict = None):
        self.name = name
        self.cpu_core_count = cpu_core_count
        self.cpu_clock_rate = cpu_clock_rate
        self.memory_capacity = memory_capacity
        self.ram_speed = ram_speed
        self.storage_capacity = storage_capacity
        self.storage_speed = storage_speed
        self.network_bandwidth = network_bandwidth
        self.sched_latency_ns = sched_latency_ns
        self.sched_min_granularity_ns = sched_min_granularity_ns
        self.cfs_period_ns = cfs_period_ns
        self.cost_dict = cost_dict if cost_dict is not None else CostDict(cost_start_up=0,
                                                                          cost_per_core_per_minute=0,
                                                                          cost_per_gb_per_minute=0,
                                                                          cost_best_effort_per_minute=0,
                                                                          cost_extra_per_minute=0)
        # for core in range(0, cores_count):
        #     self.cores.append(
        #         Resource("core", True, True, "cores", 1, 1)
        #         Cpu()
        #     )

        # self.memory = Resource("memory", False, True, "bytes", memory_size, memory_size)
        # self.disk = Resource("disk", False, True, "bytes", disk_size, disk_size)
        # self.network = Resource("network",10,False,True,"bytes",max_bandwidth)

    def __str__(self):
        return self.name

    # def run(self):
    #
    #
    # def schedule_resources(self):
    #     for replica in self.replicas:
    #         replica.init_threads()
    #         self.__threads.extend(replica.active_threads)

    # self.cpu.cfs.

    @staticmethod
    def from_config(conf: Dict = None) -> dict[str, 'HostPrototype']:
        host_prototypes_dict = {}

        for _host_proto_id, _host_proto_name in enumerate(conf):
            host_prototypes_dict[_host_proto_name] = \
                HostPrototype(name=_host_proto_name,
                              cpu_core_count=int(conf[_host_proto_name]['cores_count']),
                              cpu_clock_rate=int(conf[_host_proto_name]['cpu_clock_rate']),
                              ram_speed=int(conf[_host_proto_name]['ram_speed']),
                              memory_capacity=int(conf[_host_proto_name]['memory_capacity']),
                              storage_capacity=int(conf[_host_proto_name]['storage_capacity']),
                              storage_speed=int(conf[_host_proto_name]['storage_speed']),
                              network_bandwidth=int(conf[_host_proto_name]['network_bandwidth']))

        return host_prototypes_dict
