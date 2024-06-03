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

from typing import TYPE_CHECKING, List, Union, Set, Dict

import numpy as np

from perfsim import Nic, CPU, Storage, Settings, HostPrototype, RamSet, Router, ReplicaThread, CoreLogObserver, \
    CPULogObserver, Equipment, CostDict, CostEventsDict

if TYPE_CHECKING:
    from perfsim import MicroserviceReplica, Cluster


class Host(HostPrototype, Equipment):
    """
    A Host object simulates a single host in a cluster. It has a single CPU and a
    single NIC. The Number of cores in its CPU can be specified using the *cores_count*
    property, and its maximum network bandwidth can be specified with the *max_bandwidth*
    property.
    """

    #: The cluster this host belongs to
    __cluster: Cluster

    #: The CPU of this host
    cpu: CPU

    #: The cost events of this host
    cost_events: CostEventsDict

    def __init__(self,
                 name: str,
                 cpu_core_count: int,
                 cpu_clock_rate: int,
                 memory_capacity: int,
                 ram_speed: int,
                 storage_capacity: int,
                 storage_speed: int,
                 network_bandwidth: int,
                 router: Router = None,
                 cluster: Cluster = None,
                 sched_latency_ns: int = Settings.args.loc['sched_latency_ns']['min'],
                 sched_min_granularity_ns: int = Settings.args.loc['sched_min_granularity_ns']['min'],
                 cfs_period_ns: int = Settings.args.loc['cfs_period_ns']['min'],
                 cost_dict: CostDict = None):
        super().__init__(name=name,
                         cpu_core_count=cpu_core_count,
                         cpu_clock_rate=cpu_clock_rate,
                         memory_capacity=memory_capacity,
                         ram_speed=ram_speed,
                         storage_capacity=storage_capacity,
                         storage_speed=storage_speed,
                         network_bandwidth=network_bandwidth,
                         sched_latency_ns=sched_latency_ns,
                         sched_min_granularity_ns=sched_min_granularity_ns,
                         cfs_period_ns=cfs_period_ns,
                         cost_dict=cost_dict)
        self.cluster = cluster
        self.cost_events: CostEventsDict = {
            "power_on_periods": [],
            "best_effort_periods": [],
            "storage_reserved_periods": [],
            "core_reserved_periods": []
        }
        self.cpu = CPU(name=name + "_cpu0",
                       cores_count=self.cpu_core_count,
                       clock_rate=self.cpu_clock_rate,
                       host=self)
        self.nic = {
            "egress": Nic(name + "_nic0_egress", self.network_bandwidth, self),
            "ingress": Nic(name + "_nic0_ingress", self.network_bandwidth, self),
        }
        self.ram = RamSet(ram_set_id=name + "_ram0",
                          capacity=self.memory_capacity,
                          speed=self.ram_speed,
                          host=self)
        self.blkio = Storage(storage_id=name + "_storage0",
                             capacity=self.storage_capacity,
                             speed=self.storage_speed,
                             host=self)
        self._id_in_cluster = -1
        self.microservices = []
        self.replicas = set()
        self.__threads = set()
        self.timeline_event = []
        self.timeline_time = []
        self.name = name
        self.__router = router
        self.load_balancing_needed = False

    def reinit(self):
        """
        Reinitialize the host object

        :return:
        """
        self.__init__(name=self.name,
                      cpu_core_count=self.cpu_core_count,
                      cpu_clock_rate=self.cpu_clock_rate,
                      memory_capacity=self.memory_capacity,
                      ram_speed=self.ram_speed,
                      storage_capacity=self.storage_capacity,
                      storage_speed=self.storage_speed,
                      network_bandwidth=self.network_bandwidth,
                      router=self.router,
                      cluster=self.cluster,
                      sched_latency_ns=self.sched_latency_ns,
                      sched_min_granularity_ns=self.sched_min_granularity_ns,
                      cfs_period_ns=self.cfs_period_ns,
                      cost_dict=self.cost_dict)

    @property
    def cluster(self) -> Cluster:
        """
        Returns the cluster this host belongs to
        :return:
        """

        return self.__cluster

    @cluster.setter
    def cluster(self, cluster: Cluster):
        """
        Sets the cluster this host belongs to and attaches the necessary observers to the host's CPU and cores

        :param cluster:
        :return:
        """
        self.__cluster = cluster
        if cluster is not None:
            for core in self.cpu.cores:
                core.attach_observer(observer=CoreLogObserver(core=core))
            self.cpu.attach_observer(CPULogObserver(cpu=self.cpu))

    @property
    def router(self) -> Router:
        """
        Returns the router this host is connected to (if any)

        :return:
        """

        return self.__router

    @router.setter
    def router(self, v: Union[Router, None]):
        """
        Sets the router this host is connected to (if any)

        :param v:
        :return:
        """

        if not isinstance(v, Router) and v is not None:
            raise Exception(f"Can't connect host {self} to object of type {type(v).__name__}")
        self.__router = v

    @classmethod
    def from_host_prototype(cls,
                            name: str,
                            host_prototype: HostPrototype,
                            cluster: Cluster = None,
                            router: Router = None):
        """
        Create a host from a host prototype object and assign it to a cluster and a router

        :param name:
        :param host_prototype:
        :param cluster:
        :param router:
        :return:
        """

        return cls(name=name,
                   cpu_core_count=host_prototype.cpu_core_count,
                   cpu_clock_rate=host_prototype.cpu_clock_rate,
                   memory_capacity=host_prototype.memory_capacity,
                   ram_speed=host_prototype.ram_speed,
                   storage_capacity=host_prototype.storage_capacity,
                   storage_speed=host_prototype.storage_speed,
                   network_bandwidth=host_prototype.network_bandwidth,
                   router=router,
                   cluster=cluster,
                   sched_latency_ns=host_prototype.sched_latency_ns,
                   sched_min_granularity_ns=host_prototype.sched_min_granularity_ns,
                   cfs_period_ns=host_prototype.cfs_period_ns)

    def is_replica_placeable_on_host_from_resource_perspective(self, replica: MicroserviceReplica) -> bool:
        """
        Check if a replica can be placed on this host from a resource perspective (CPU, RAM, BLKIO, NIC)

        :param replica:
        :return:
        """

        c_a = self.cpu.is_there_enough_resources_to_reserve(amount=replica.microservice.cpu_requests) or \
              replica.microservice.cpu_requests == replica.microservice.cpu_limits == -1
        r_a = self.ram.is_there_enough_resources_to_reserve(amount=replica.microservice.memory_requests)
        b_a = self.blkio.is_there_enough_resources_to_reserve(amount=replica.microservice.blkio_capacity)

        if c_a and r_a and b_a:  # and e_a and i_a:
            return True
        else:
            return False

    def place_replica(self, replica: MicroserviceReplica) -> None:
        """
        Place a replica on this host and reserve the necessary resources (CPU, RAM, BLKIO, NIC)

        :param replica:
        :return:
        """

        if replica.microservice.is_guaranteed() or replica.microservice.is_unlimited_burstable():
            self.cpu.reserve(amount=replica.microservice.cpu_requests)
        elif replica.microservice.is_limited_burstable():
            self.cpu.reserve(amount=replica.microservice.cpu_limits)
        elif replica.microservice.is_burstable():
            self.cpu.reserve(amount=replica.microservice.cpu_limits)
        else:
            replica.process.cpu_requests_share = len(self.cpu.cores) * self.cpu.max_cpu_requests
        self.ram.reserve(amount=replica.microservice.memory_requests)
        self.blkio.reserve(amount=replica.microservice.blkio_capacity)
        self.nic["egress"].request_bw(bandwidth_request=replica.microservice.egress_bw)
        self.nic["ingress"].request_bw(bandwidth_request=replica.microservice.ingress_bw)
        self.replicas.add(replica)
        if len(self.replicas) == 1:
            self.cost_events["power_on_periods"].append((self.cluster.sim.time, float("inf")))

    def evict_replica(self, replica: MicroserviceReplica) -> None:
        """
        Evict a replica from this host and release the reserved resources (CPU, RAM, BLKIO, NIC)

        :param replica:
        :return:
        """

        self.replicas.remove(replica)
        if replica.microservice.cpu_requests != -1 and replica.microservice.cpu_limits != -1:
            self.cpu.release(amount=replica.microservice.cpu_requests)
        self.ram.release(amount=replica.microservice.memory_requests)
        self.blkio.release(amount=replica.microservice.blkio_capacity)
        self.nic["egress"].dismiss_bw(bandwidth_request=replica.microservice.egress_bw)
        self.nic["ingress"].dismiss_bw(bandwidth_request=replica.microservice.ingress_bw)
        if len(self.replicas) == 0:
            last_power_on_period = self.cost_events["power_on_periods"][-1]
            if last_power_on_period[1] != float("inf"):
                raise Exception("Last power on period is not infinite! Probably something went wrong (i.e., a bug).")
            else:
                last_power_on_period = (last_power_on_period[0], self.cluster.sim.time)

    def is_active(self) -> bool:
        """
        Check if the host is active (i.e., has at least one thread running)

        :return:
        """

        return len(self.threads) > 0

    @staticmethod
    def generate_random_instances(cluster: Cluster,
                                  host_count: int,
                                  core_count: int = np.random.choice(Settings.chunks["host_cpu_core_count"]),
                                  cpu_clock_rate: int = np.random.choice(Settings.chunks["host_cpu_clock_rate"]),
                                  memory_capacity: int = 16 * 1024 * 1024 * 1024,
                                  ram_speed: int = 2675787694,  # sysbench
                                  storage_capacity: int = 1000,
                                  storage_speed: int = 1.0695 * 10 ** 7,  # sysbench
                                  network_bandwidth: int = np.random.choice(Settings.chunks["host_network_bandwidth"]),
                                  name_index_starts_from: int = 0) -> List[Host]:
        """
        Generate random instances of hosts

        :param cluster:
        :param host_count:
        :param core_count:
        :param cpu_clock_rate:
        :param memory_capacity:
        :param ram_speed:
        :param storage_capacity:
        :param storage_speed:
        :param network_bandwidth:
        :param name_index_starts_from:
        :return:
        """

        host_count = np.random.choice(Settings.chunks["host_count"]) \
            if host_count is None else host_count

        hosts = []
        for i in np.arange(0, host_count):
            hosts.append(
                Host(name="host" + str(i + name_index_starts_from),
                     cpu_core_count=core_count,
                     cpu_clock_rate=cpu_clock_rate,
                     memory_capacity=memory_capacity,
                     ram_speed=ram_speed,
                     storage_capacity=storage_capacity,
                     storage_speed=storage_speed,
                     network_bandwidth=network_bandwidth,
                     cluster=cluster)
            )

        return hosts

    @property
    def threads(self) -> Set[ReplicaThread]:
        """
        Get the threads running on the host (if any)

        :return:
        """
        return self.__threads

    @threads.setter
    def threads(self, v: Set[ReplicaThread]):
        """
        Set the threads running on the host (if any)

        :param v:
        :return:
        """

        self.__threads = v

    @staticmethod
    def from_config(conf: Dict = None, host_prototypes_dict: dict[str, 'HostPrototype'] = None) -> dict[str, 'Host']:
        """
        Create hosts from a configuration dictionary and a dictionary of host prototypes

        :param conf:
        :param host_prototypes_dict:
        :return:
        """
        hosts_dict = {}

        for _host_id, _host_name in enumerate(conf):
            _host_type = conf[_host_name]
            _h = Host.from_host_prototype(name=_host_name, host_prototype=host_prototypes_dict[_host_type])
            hosts_dict[_host_name] = _h

        return hosts_dict

    @staticmethod
    def to_dict(hosts_list: list[Host]) -> dict[str, Host]:
        """
        Convert a list of hosts to a dictionary of hosts

        :param hosts_list:
        :return:
        """

        hosts_dict = {}

        for node in hosts_list:
            hosts_dict[node.name] = node

        return hosts_dict
