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

from typing import TYPE_CHECKING, Dict, List, Union

import numpy as np

from perfsim import LoadBalancer, MicroserviceReplica, MicroservicePrototype, \
    MicroserviceEndpointFunction, ResourceAllocationScenario, Host

if TYPE_CHECKING:
    pass


class Microservice(MicroservicePrototype):
    """
    This class represents a microservice in a service chain. It has a name, a list of endpoints, a list of replicas, a
    load balancer, and a resource allocation scenario.
    """

    #: The name of the microservice
    name: str

    #: The list of endpoints of the microservice
    endpoint_functions: Dict[str, MicroserviceEndpointFunction]

    # TODO: Change the list to a dictionary with replica name as key
    #: The list of replicas of the microservice
    __replicas: List[MicroserviceReplica]

    #: The load balancer of the microservice that is responsible for the load balancing of the replicas
    load_balancer: LoadBalancer

    #: The resource allocation scenario of the microservice
    resource_allocation_scenario: ResourceAllocationScenario

    #: List of hosts containing at least a replica of this microservice
    __hosts: List[Host]

    #: The number of replicas of the microservice (the original number of replicas)
    __replica_count: int

    #: The CPU cpu_requests_share of the microservice
    _cpu_requests: int

    #: The cpu_limits of the microservice
    _cpu_limits: int

    #: The ingress bandwidth of the microservice
    ingress_bw: int

    #: The egress bandwidth of the microservice
    egress_bw: int

    #: The ingress latency of the microservice
    ingress_latency: Union[int, float]

    #: The egress latency of the microservice
    egress_latency: Union[int, float]

    #: The storage capacity of the microservice
    blkio_capacity: int

    #: The memory request of the microservice
    memory_requests: int

    def __init__(self,
                 name: str,
                 endpoint_functions: Dict[str, MicroserviceEndpointFunction] = None,
                 replica_count: int = 0,
                 cpu_requests: int = -1,
                 cpu_limits: int = -1,
                 memory_requests: int = 0,
                 ingress_bw: int = float('inf'),
                 egress_bw: int = float('inf'),
                 ingress_latency: float = 0,
                 egress_latency: float = 0,
                 blkio_capacity: int = 0,
                 resource_allocation_scenario: ResourceAllocationScenario = None):

        if endpoint_functions is None:
            endpoint_functions = {}

        super().__init__(name=name)
        self.name = name
        self.endpoint_functions = endpoint_functions
        self.__replica_count = replica_count
        self.cpu_requests = cpu_requests
        self.cpu_limits = cpu_limits
        self.memory_requests = memory_requests
        self.ingress_bw = ingress_bw
        self.egress_bw = egress_bw
        self.ingress_latency = ingress_latency
        self.egress_latency = egress_latency
        self.blkio_capacity = blkio_capacity
        self.resource_allocation_scenario = resource_allocation_scenario
        self.__ms_affinity_rules = set()
        self.__ms_antiaffinity_rules = set()
        self.__host_affinity_rules = set()
        self.__host_antiaffinity_rules = set()
        self.__replicas = []
        self.__hosts = []  #: list of hosts containing at least a replica of this microservice
        self.load_balancer = LoadBalancer(items=self.__replicas, algorithm="round_robin")
        self.current_replica_id = 0
        self._init_replicas(replica_count=self.replica_count)

    @classmethod
    def from_prototype(cls,
                       name: str,
                       prototype: MicroservicePrototype,
                       replica_count: int = 0,
                       cpu_requests: int = -1,
                       cpu_limits: int = -1,
                       memory_requests: int = -1,
                       ingress_bw: int = float('inf'),
                       egress_bw: int = float('inf'),
                       ingress_latency: float = 0,
                       egress_latency: float = 0,
                       blkio_capacity: int = -1):

        _cls = cls(name=name,
                   endpoint_functions=None,
                   replica_count=replica_count,
                   cpu_requests=cpu_requests,
                   cpu_limits=cpu_limits,
                   memory_requests=memory_requests,
                   ingress_bw=ingress_bw,
                   egress_bw=egress_bw,
                   ingress_latency=ingress_latency,
                   egress_latency=egress_latency,
                   blkio_capacity=blkio_capacity)

        endpoint_functions = {}
        for _function_id, _function_name in enumerate(prototype.endpoint_function_prototypes_dict):
            _microservice_prototype = prototype.endpoint_function_prototypes_dict[_function_name]
            _endpoint_function = MicroserviceEndpointFunction.from_prototype(name=_function_name,
                                                                             id=_function_id,
                                                                             prototype=_microservice_prototype)
            endpoint_functions[_function_name] = _endpoint_function
            _endpoint_function.microservice = _cls

        _cls.endpoint_functions = endpoint_functions

        return _cls

    def is_best_effort(self) -> bool:
        return self.cpu_limits == self.cpu_requests == -1

    def is_guaranteed(self) -> bool:
        return self.cpu_limits == self.cpu_requests != -1

    def is_burstable(self) -> bool:
        return self.cpu_limits != self.cpu_requests and self.cpu_requests != -1

    def is_unlimited_burstable(self) -> bool:
        return self.cpu_limits != self.cpu_requests and self.cpu_requests != -1 and self.cpu_limits == -1

    def is_limited_burstable(self) -> bool:
        return self.cpu_limits != self.cpu_requests and self.cpu_limits != -1

    def _init_replicas(self, replica_count) -> None:
        self.__replicas = []
        for replica_id in np.arange(0, replica_count):
            self.__replicas.append(MicroserviceReplica(name=str(self.name) + "_" + str(replica_id), microservice=self))

    def next_replica(self, increase_replica_id: bool = True) -> MicroserviceReplica:
        replica_id = self.current_replica_id % len(self.__replicas)

        if increase_replica_id:
            self.current_replica_id += 1

        # _id = randint(0, len(self.__replicas) - 1)
        return self.__replicas[replica_id]

    def add_microservice_affinity_with(self, ms: Microservice) -> None:
        if ms is not None:
            if isinstance(ms, Microservice):
                self.__ms_affinity_rules = self.__ms_affinity_rules.union({ms})
            else:
                raise Exception("Given microservice affinity rule to add is not valid!"
                                " The affinity object is not an instance of Microservice class!")

    def add_host_affinity_with(self, host: Host) -> None:
        if host is not None:
            if isinstance(host, Host):
                self.__host_affinity_rules = self.__host_affinity_rules.union({host})
            else:
                raise Exception("Given host affinity rule to add is not valid!"
                                " The affinity object is not an instance of Host class!")

    def delete_microservice_affinity_with(self, ms: Microservice) -> None:
        if ms is not None:
            if isinstance(ms, Microservice):
                self.__ms_affinity_rules -= {ms}
            else:
                raise Exception("Given microservice affinity rule to delete is not valid!"
                                " The affinity object is not an instance of Microservice class!")

    def delete_host_affinity_with(self, host: Host) -> None:
        if host is not None:
            if isinstance(host, Host):
                self.__host_affinity_rules -= {host}
            else:
                raise Exception("Given host affinity rule to delete is not valid!"
                                " The affinity object is not an instance of Host class!")

    def add_microservice_anti_affinity_with(self, ms: Microservice) -> None:
        if ms is not None:
            if isinstance(ms, Microservice):
                self.__ms_antiaffinity_rules = self.__ms_antiaffinity_rules.union({ms})
            else:
                raise Exception("Given microservice anti-affinity rule to add is not valid!"
                                " The anti-affinity object is not an instance of Microservice class!")

    def add_host_anti_affinity_with(self, host: Host) -> None:
        if host is not None:
            if isinstance(host, Host):
                self.__host_antiaffinity_rules = self.__host_antiaffinity_rules.union({host})
            else:
                raise Exception("Given host anti-affinity rule to add is not valid!"
                                " The anti-affinity object is not an instance of Host class!")

    def delete_microservice_anti_affinity_with(self, ms: Microservice) -> None:
        if ms is not None:
            if isinstance(ms, Microservice):
                self.__ms_antiaffinity_rules -= {ms}
            else:
                raise Exception("Given microservice anti-affinity rule to delete is not valid!"
                                " The anti-affinity object is not an instance of Microservice class!")

    def delete_host_anti_affinity_with(self, host: Host) -> None:
        if host is not None:
            if isinstance(host, Host):
                self.__host_antiaffinity_rules -= {host}
            else:
                raise Exception("Given host anti-affinity rule to delete is not valid!"
                                " The anti-affinity object is not an instance of Host class!")

    @property
    def ms_affinity_rules(self):
        return self.__ms_affinity_rules

    @property
    def ms_antiaffinity_rules(self):
        return self.__ms_antiaffinity_rules

    @property
    def host_affinity_rules(self):
        return self.__host_affinity_rules

    @property
    def host_antiaffinity_rules(self):
        return self.__host_antiaffinity_rules

    @property
    def replicas(self):
        return self.__replicas

    @property
    def replica_count(self):
        return self.__replica_count

    @property
    def hosts(self):
        return self.__hosts

    @ms_affinity_rules.setter
    def ms_affinity_rules(self, v):
        raise Exception(
            "You can't directly change microservice affinity rules. "
            "Use the add_microservice_affinity_with(ms) or delete_microservice_affinity_with(ms) methods instead.")

    @ms_antiaffinity_rules.setter
    def ms_antiaffinity_rules(self, v):
        raise Exception(
            "You can't directly change microservice anti-affinity rules. "
            "Use the add_microservice_anti_affinity_with(ms) or delete_microservice_anti_affinity_with(ms) "
            "methods instead.")

    @host_affinity_rules.setter
    def host_affinity_rules(self, v):
        raise Exception(
            "You can't directly change host affinity rules. "
            "Use the add_host_affinity_with(ms) or delete_host_affinity_with(ms) methods instead.")

    @host_antiaffinity_rules.setter
    def host_antiaffinity_rules(self, v):
        raise Exception(
            "You can't directly change host anti-affinity rules. "
            "Use the add_host_anti_affinity_with(ms) or delete_host_anti_affinity_with(ms) "
            "methods instead.")

    @replicas.setter
    def replicas(self, v):
        raise Exception("You can't change replicas of a microservice. Sorry!")

    @hosts.setter
    def hosts(self, v):
        raise Exception("You can't change hosts of a microservice! It's the job of the scheduler.")

    @replica_count.setter
    def replica_count(self, v):
        self._init_replicas(replica_count=v)
        self.__replica_count = v

    def __str__(self):
        return self.name

    @property
    def cpu_requests(self):
        return self._cpu_requests

    @cpu_requests.setter
    def cpu_requests(self, v):
        if hasattr(self, "_cpu_limits") and self._cpu_limits != -1 and v != -1 and v > self._cpu_limits:
            raise Exception("CPU requests can't be greater than CPU limits!")
        elif v != -1 and v <= 0:
            raise Exception("CPU requests must be greater than 0!")

        old_data = self._cpu_requests if hasattr(self, "_cpu_requests") else None
        self._cpu_requests = v

        if old_data is not None and old_data != v:
            for replica in self.replicas:
                replica.reinit()

    @property
    def cpu_limits(self):
        return self._cpu_limits

    @cpu_limits.setter
    def cpu_limits(self, v):
        if hasattr(self, "_cpu_requests") and self._cpu_requests != -1 and v != -1 and v < self._cpu_requests:
            raise Exception("CPU limits can't be less than CPU requests!")
        elif v != -1 and v <= 0:
            raise Exception("CPU limits must be greater than 0!")

        old_data = self._cpu_limits if hasattr(self, "_cpu_limits") else None
        self._cpu_limits = v

        if old_data is not None and old_data != v:
            for replica in self.replicas:
                replica.reinit()

    # @staticmethod
    # def create_random_instances(ms_count: int = None,
    #                             replica_count: int = None,
    #                             cpu_requests: int = None,
    #                             cpu_limits: int = None,
    #                             replica_reserved_network_bandwidth: int = None,
    #                             replica_thread_instructions: List[int] = [],
    #                             replica_thread_avg_cpi: List[int] = [],
    #                             replica_average_cpu_usage: List[float] = [],
    #                             replica_thread_count: int = None,
    #                             ms_request_size_in_chain: int = None,
    #                             ) -> List[Microservice]:
    #     microservices = []
    #     _ms_count = Settings.get_random_chunk("ms_count") \
    #         if ms_count is None else ms_count
    #
    #     for i in np.arange(0, _ms_count):
    #         _replica_count = Settings.get_random_chunk("ms_replica_count") \
    #             if replica_count is None else replica_count
    #         _cpu_shares = Settings.get_random_chunk(
    #             "ms_replica_cpu_shares") if cpu_requests is None else cpu_requests
    #
    #         _cpu_limits = Settings.get_random_chunk(
    #             "ms_replica_cpu_limits",
    #             _cpu_shares) if cpu_limits is None else cpu_limits
    #         _replica_reserved_network_bandwidth = Settings.get_random_chunk(
    #             "ms_replica_reserved_network_bandwidth") if replica_reserved_network_bandwidth is None else replica_reserved_network_bandwidth
    #
    #         if replica_thread_instructions is None or \
    #                 replica_thread_avg_cpi is None or \
    #                 replica_average_cpu_usage is None:
    #             if replica_thread_count is None:
    #                 replica_thread_count = Settings.get_random_chunk("ms_replica_thread_count")
    #             elif len(replica_thread_instructions) != len(replica_thread_avg_cpi) \
    #                     != len(replica_average_cpu_usage) != replica_thread_count:
    #                 raise Exception("Mismatch in number of requested threads and size of instructions/cpis/cpu usages "
    #                                 "lists.")
    #         else:
    #             for _thread in range(replica_thread_count):
    #                 replica_thread_instructions.append(Settings.get_random_chunk("ms_replica_thread_instructions"))
    #                 replica_thread_avg_cpi.append(Settings.get_random_chunk("ms_replica_thread_avg_cpi"))
    #                 replica_average_cpu_usage.append(Settings.get_random_chunk("ms_replica_average_cpu_usage"))
    #
    #         _ms_request_size_in_chain = Settings.get_random_chunk(
    #             "sc_edge_bytes") if ms_request_size_in_chain is None else ms_request_size_in_chain
    #         microservices.append(Microservice(name="microservice" + str(i),
    #                                           id=_replica_count,
    #                                           _cpu_shares,
    #                                           cpu_limits=_cpu_limits,
    #                                           egress_bw=_replica_reserved_network_bandwidth,
    #                                           ingress_bw=_replica_reserved_network_bandwidth,
    #                                           replica_thread_count,
    #                                           replica_thread_instructions,
    #                                           replica_thread_avg_cpi,
    #                                           replica_average_cpu_usage,
    #                                           _ms_request_size_in_chain
    #                                           ))
    #
    #     return microservices
