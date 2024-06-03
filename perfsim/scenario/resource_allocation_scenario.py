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

from copy import deepcopy
from typing import Union, List, Dict


class ResourceAllocationScenario:
    """
    This class represents a resource allocation scenario.
    """

    def __init__(self,
                 name: str,
                 cpu_requests: int = -1,
                 cpu_limits: int = -1,
                 memory_requests: int = 0,
                 ingress_bw: Union[int, str] = "",
                 egress_bw: Union[int, str] = "",
                 ingress_latency: float = 0,
                 egress_latency: float = 0,
                 blkio_capacity: int = 0):
        ingress_bw = float('inf') if ingress_bw == "" else ingress_bw
        egress_bw = float('inf') if egress_bw == "" else egress_bw

        negative_resource_name = None
        if memory_requests < 0:
            negative_resource_name = "mem"
        elif ingress_bw < 0:
            negative_resource_name = "ingress_bw"
        elif egress_bw < 0:
            negative_resource_name = "egress_bw"

        if negative_resource_name is not None:
            raise Exception(f"At least one of the resources ({negative_resource_name}) has negative capacity!")

        self.name = name
        self.cpu_requests = cpu_requests
        self.cpu_limits = cpu_limits
        self.memory_requests = memory_requests
        self.ingress_bw = ingress_bw
        self.egress_bw = egress_bw
        self.ingress_latency = ingress_latency
        self.egress_latency = egress_latency
        self.blkio_capacity = blkio_capacity

    @staticmethod
    def copy_to_dict(res_alloc_scenarios: Union[List[ResourceAllocationScenario],
    Dict[str, ResourceAllocationScenario]]) \
            -> Dict[str, ResourceAllocationScenario]:
        """
        Copy the resource allocation scenarios to a dictionary.

        :param res_alloc_scenarios: The resource allocation scenarios to copy.
        :return:  The copied resource allocation scenarios.
        """

        if isinstance(res_alloc_scenarios, dict):
            return deepcopy(res_alloc_scenarios)
        else:
            resource_allocation_scenarios_dict = {}

            for scenario in res_alloc_scenarios:
                resource_allocation_scenarios_dict[scenario.name] = deepcopy(scenario)

            return resource_allocation_scenarios_dict

    @staticmethod
    def from_config(conf: dict) -> Dict[str, ResourceAllocationScenario]:
        """
        Create resource allocation scenarios from a configuration.

        :param conf: The configuration in the form of a dictionary.
        :return: The resource allocation scenarios.
        """

        resource_allocation_scenarios_dict = {}

        for _scenario_id, _scenario_name in enumerate(conf):
            _resource_allocation_scenario = ResourceAllocationScenario(
                name=_scenario_name,
                cpu_requests=conf[_scenario_name]["cpu_requests"],
                cpu_limits=conf[_scenario_name]["cpu_limits"],
                memory_requests=conf[_scenario_name]["memory_capacity"],
                ingress_bw=conf[_scenario_name]["ingress_bw"],
                egress_bw=conf[_scenario_name]["egress_bw"],
                ingress_latency=conf[_scenario_name]["ingress_latency"],
                egress_latency=conf[_scenario_name]["egress_latency"],
                blkio_capacity=conf[_scenario_name]["blkio_capacity"])
            resource_allocation_scenarios_dict[_scenario_name] = _resource_allocation_scenario

        return resource_allocation_scenarios_dict

    def __str__(self):
        """
        Return the string representation of the resource allocation scenario.

        :return:
        """

        return self.name
