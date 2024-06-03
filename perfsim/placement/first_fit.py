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

from typing import Dict, Any, Set

import pandas as pd

from perfsim import PlacementAlgorithm, MicroserviceReplica, Host, ResourceNotAvailableError


class FirstFit(PlacementAlgorithm):
    def place(self, placement_matrix: pd.DataFrame, replicas: Set[MicroserviceReplica], hosts_dict: Dict[str, Host]):
        self.first_fit(placement_matrix, replicas, hosts_dict)

    @staticmethod
    def first_fit(placement_matrix: pd.DataFrame,
                  replicas: Set[MicroserviceReplica],
                  hosts_dict: Dict[str, Host] = None) -> None:
        for replica in replicas:
            if len(replica.microservice.affinity_rules) != 0:
                affinity_hosts = replica.microservice.affinity_rules
            else:
                affinity_hosts = hosts_dict

            antiaffinity_hosts_names = list((x.name for x in replica.microservice.antiaffinity_rules))

            for host in affinity_hosts:
                if host.name not in antiaffinity_hosts_names:
                    try:
                        replica.host = host
                        break
                    except ResourceNotAvailableError:
                        continue

            if replica.host is None:
                # if hosts_dict is None:
                #     new_host = Host.generate_random_instances(
                #         cluster=cluster,
                #         host_count=1,
                #         core_count=cluster.host_prototype.cpu_core_count,
                #         cpu_clock_rate=cluster.host_prototype.cpu_clock_rate,
                #         memory_capacity=cluster.host_prototype.memory_requests,
                #         ram_speed=cluster.host_prototype.ram_speed,
                #         storage_capacity=cluster.host_prototype.storage_capacity,
                #         storage_speed=cluster.host_prototype.storage_speed,
                #         network_bandwidth=cluster.host_prototype.network_bandwidth,
                #         name_index_starts_from=len(hosts_dict))[0]
                #     self.hosts_dict.append(new_host)
                #     replica.host = new_host
                #     placement_matrix.insert(len(hosts_dict) - 1,
                #                             replica.host.name,
                #                             np.zeros(shape=(len(self.cluster.microservices), 1)))
                # else:
                raise ResourceNotAvailableError("Available hosts are not enough!")

            placement_matrix.loc[replica.microservice.name, replica.host.name] += 1

    def __init__(self, name: str, options: Dict[str, Any]):
        super().__init__(name=name, options=options)
        self._algorithm_name = self.__class__.__name__
