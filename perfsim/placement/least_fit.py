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

from typing import Dict, Set
from typing import TypedDict

import pandas as pd

from perfsim import PlacementAlgorithm, ResourceNotAvailableError, MicroserviceReplica, Host


class LeastFitOptions(TypedDict):
    w_cpu: float
    w_mem: float
    w_ingress: float
    w_egress: float
    w_blkio: float


class LeastFit(PlacementAlgorithm):
    def place(self, placement_matrix: pd.DataFrame, replicas: Set[MicroserviceReplica], hosts_dict: Dict[str, Host]):
        self.reschedule(placement_matrix=placement_matrix, replicas=replicas, hosts_dict=hosts_dict)

    def __init__(self, name: str, options: LeastFitOptions):
        super().__init__(name=name, options=options)
        self._algorithm_name = self.__class__.__name__

    def _calculate_host_score_for_placing_replica(self, host: Host, replica: MicroserviceReplica) -> float:
        weight_opts = self.options
        # sum_of_weights = opts["w_cpu"] + opts["w_mem"] + opts["w_ingress"] + opts["w_egress"] + opts["w_blkio"]
        # todo: check for non weights
        scores = {"cpu_score": self.least_fit_score(available=host.cpu.get_available(),
                                                    capacity=host.cpu.capacity,
                                                    requested=replica.microservice.cpu_requests,
                                                    weight=weight_opts["w_cpu"]),
                  "mem_score": self.least_fit_score(available=host.ram.get_available(),
                                                    capacity=host.ram.capacity,
                                                    requested=replica.microservice.memory_requests,
                                                    weight=weight_opts["w_mem"]),
                  "ingress_score": self.least_fit_score(available=host.nic["ingress"].get_available(),
                                                        capacity=host.nic["ingress"].bandwidth,
                                                        requested=replica.microservice.ingress_bw,
                                                        weight=weight_opts["w_ingress"]),
                  "egress_score": self.least_fit_score(available=host.nic["egress"].get_available(),
                                                       capacity=host.nic["egress"].bandwidth,
                                                       requested=replica.microservice.egress_bw,
                                                       weight=weight_opts["w_egress"]),
                  "blkio_score": self.least_fit_score(available=host.blkio.get_available(),
                                                      capacity=host.blkio.capacity,
                                                      requested=replica.microservice.blkio_capacity,
                                                      weight=weight_opts["w_blkio"])}

        _final_score = sum(scores.values()) / sum(weight_opts.values())
        return _final_score

    @staticmethod
    def least_fit_score(available: float, capacity: float, requested: float, weight: float):
        if requested > capacity:
            requested = capacity
        return (100 - ((available - requested) * (100 / capacity))) * weight

    def reschedule(self,
                   placement_matrix: pd.DataFrame,
                   replicas: Set[MicroserviceReplica],
                   hosts_dict: Dict[str, Host]) -> None:
        if hosts_dict is None:
            raise Exception("Current version of this package doesn't support automatic host generation for the least " +
                            "fit placement algorithm. Try the first fit algorithm, or define hosts in the first place!")

        for r in replicas:
            if len(r.microservice.ms_affinity_rules) != 0 or len(r.microservice.host_affinity_rules) != 0:
                affinity_hosts = set()

                for ms in r.microservice.ms_affinity_rules:
                    affinity_hosts = affinity_hosts.union(set(ms.hosts_dict))

                for host in r.microservice.host_affinity_rules:
                    affinity_hosts = affinity_hosts.union({host})
            else:
                affinity_hosts = hosts_dict.values()

            antiaffinity_hosts_names = set()
            if len(r.microservice.ms_antiaffinity_rules) != 0 or len(r.microservice.host_antiaffinity_rules) != 0:
                if len(r.microservice.ms_antiaffinity_rules) != 0:
                    for ms in r.microservice.ms_antiaffinity_rules:
                        antiaffinity_hosts_names = antiaffinity_hosts_names.union(
                            {_host.name for _host in ms.hosts_dict})

                if len(r.microservice.host_antiaffinity_rules) != 0:
                    for host in r.microservice.host_antiaffinity_rules:
                        antiaffinity_hosts_names = antiaffinity_hosts_names.union({host.name})

            lowest_score = float('inf')
            least_used_host = None

            for host in affinity_hosts:
                if host.name not in antiaffinity_hosts_names:
                    if host.is_replica_placeable_on_host_from_resource_perspective(replica=r):
                        _host_score = self._calculate_host_score_for_placing_replica(host=host, replica=r)
                        if _host_score < lowest_score:
                            lowest_score = _host_score
                            least_used_host = host
                        elif _host_score == lowest_score and len(host.replicas) < len(least_used_host.replicas):
                            least_used_host = host

            r.host = least_used_host
            if r.host is None:
                raise ResourceNotAvailableError("Available hosts are not enough to place replica " + str(r) + "!")
            placement_matrix.loc[r.microservice.name, r.host.name] += 1
