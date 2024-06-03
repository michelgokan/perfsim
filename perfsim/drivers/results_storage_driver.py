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

import importlib
from abc import ABC


class ResultsStorageDriver(ABC):
    """
    The ResultsStorageDriver class is the abstract class for the different storage drivers that can be used to store
    the results of the simulation.
    """

    #: The name of the storage driver.
    name: str

    #: The results with graphs.
    results_with_graphs: dict

    def __init__(self, name: str):
        self.name = name
        pass

    def save_service_chains_original_graph(self, service_chain_managers_dict, **atr):
        """
        Save the original service chains graph.

        :param service_chain_managers_dict:
        :param atr:
        :return:
        """
        pass

    def save_service_chains_alternative_graph(self, service_chain_managers_dict, **atr):
        """
        Save the alternative service chains graph.

        :param service_chain_managers_dict:
        :param atr:
        :return:
        """
        pass

    def save_cluster_topology_graph(self, cluster, **atr):
        """
        Save the topology graph of the cluster.

        :param cluster:
        :param atr:
        :return:
        """
        pass

    def save_service_chain_result_graph(self, result, **atr):
        """
        Save the service chain result graph.

        :param result:
        :param atr:
        :return:
        """
        pass

    def save_timeline_graph(self, result, **atr):
        """
        Save the timeline graph.

        :param result:
        :param atr:
        :return:
        """
        pass

    def save_simulation_scenario_results(self, simulation):
        """
        Save the results of the simulation scenario.

        :param simulation:
        :return:
        """
        pass

    def save_hosts_cores_heatmap(self, hosts_dict, **atr):
        """
        Save the hosts cores heatmap.

        :param hosts_dict:
        :param atr:
        :return:
        """
        pass

    def save_all(self, simulation):
        """
        Save all the results of the simulation scenario.

        :param simulation:
        :return:
        """
        pass

    @staticmethod
    def from_config(conf: dict, default_class, name, **other_attrs) -> 'ResultsStorageDriver':
        """
        Create a storage driver from the configuration.

        :param conf:
        :param default_class:
        :param name:
        :param other_attrs:
        :return:
        """
        if conf is None:
            storage_driver = default_class(name=name, **other_attrs)
        else:
            params = conf["params"] if "params" in conf else {}
            if conf["driver_class"] in globals():
                klass = globals()[conf["driver_class"]]
            else:
                module = importlib.import_module(conf["classpath"])
                klass = getattr(module, conf["driver_class"])
            storage_driver = klass(**params)
        return storage_driver
