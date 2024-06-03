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

from typing import TYPE_CHECKING, Dict, Set

import numpy as np
import pandas as pd

from perfsim import Host, MicroserviceReplica

if TYPE_CHECKING:
    from perfsim import Cluster, ReplicaThread


class ClusterScheduler:
    """
    This class is responsible for scheduling the cluster.
    """

    #: The set of zombie threads in the cluster that needs to be killed
    zombie_threads: Set[ReplicaThread]

    #: The set of active hosts in the cluster that are actually having a thread running on them.
    active_hosts: Set[Host]

    #: The set of hosts in the cluster that require CPU load balancing.
    hosts_need_load_balancing: Set[Host]

    #: The set of active threads in the cluster that are actually running on a host.
    active_threads: Set[ReplicaThread]

    #: The cluster to which this scheduler belongs
    cluster: Cluster

    #: The placement dataframe consisting of microservice name as index and host name as column
    __placement_matrix: pd.DataFrame

    #:
    hosts_dict: Dict[str, Host]
    replicas: Set[MicroserviceReplica]

    # placement_algorithm: PlacementAlgorithm

    def __init__(self, cluster: Cluster):
        # TODO: concept of active_hosts should be defined here
        self.active_hosts = set()
        self.hosts_need_load_balancing = set()
        self.zombie_threads = set()
        self.active_threads = set()
        self.cluster = cluster

        self.reschedule(hosts_dict=self.cluster.topology.hosts_dict)

    def __initialize_cluster(self, hosts_dict: Dict[str, Host] = None):
        """
        Initialize the cluster.

        :param hosts_dict: The dictionary of hosts.
        :return:   None
        """

        self.hosts_dict = hosts_dict

        self.replicas = set()
        host_names = list(self.hosts_dict.keys())
        microservices_names = list(self.cluster.microservices_dict.keys())
        zero_array = np.zeros(shape=(len(self.cluster.microservices_dict), len(self.hosts_dict)))
        self.__placement_matrix = pd.DataFrame(data=zero_array, index=microservices_names, columns=host_names)

    @property
    def placement_matrix(self) -> pd.DataFrame:
        """
        Get the placement matrix.

        :return:
        """

        return self.__placement_matrix

    @placement_matrix.setter
    def placement_matrix(self, v):
        """
        Set the placement matrix.

        :param v:
        :return:
        """

        raise Exception(
            "You can't directly change the placement matrix. Use the reschedule method or change microservices "
            "affinity/anti-affinities instead.")

    def reschedule(self, hosts_dict: Dict[str, Host] = None, use_current_hosts: bool = False):
        """
        Reschedule the cluster.

        :param hosts_dict:  The dictionary of hosts.
        :param use_current_hosts:  Whether to use the current hosts or not.
        :return:  None
        """

        if use_current_hosts:
            hosts_dict = self.hosts_dict

        self.__initialize_cluster(hosts_dict=hosts_dict)

        for microservice_index, microservice in enumerate(self.cluster.microservices_dict.values()):
            self.replicas.update(microservice.replicas)
            for replica_index, replica in enumerate(microservice.replicas):
                replica.remove_host_without_eviction()

        self.cluster.sim.placement_algorithm.place(placement_matrix=self.placement_matrix,
                                                   replicas=self.replicas,
                                                   hosts_dict=hosts_dict)
