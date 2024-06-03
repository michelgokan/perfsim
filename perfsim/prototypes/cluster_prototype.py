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


from copy import deepcopy
from functools import singledispatch
from typing import Dict, List, Union

from perfsim import ServiceChain, Topology, TrafficPrototype, AffinityPrototype, \
    ResourceAllocationScenario, SimulationScenario, ServiceChainManager, PlacementAlgorithm


class ClusterPrototype:
    scms_dict: Dict[str, ServiceChainManager]
    scenario_name: str
    service_chains_dict: Dict[str, ServiceChain]
    topology: Topology
    # placement_scenario: PlacementScenario
    placement_scenario: PlacementAlgorithm
    traffic_prototypes_dict: Dict[str, TrafficPrototype]
    resource_allocation_scenarios_dict: Dict[str, ResourceAllocationScenario]
    affinity_prototypes_dict: Dict[str, AffinityPrototype]
    simulation_scenario: SimulationScenario

    @singledispatch
    def __init__(self,
                 scenario_name: str,
                 service_chains: Union[Dict[str, ServiceChain], List[ServiceChain]],
                 topology: Topology,
                 # placement_scenario: PlacementScenario,
                 placement_algorithm: PlacementAlgorithm,
                 resource_allocation_scenarios: Union[
                     Dict[str, ResourceAllocationScenario], List[ResourceAllocationScenario]],
                 affinity_prototypes: Union[
                     Dict[str, AffinityPrototype], List[AffinityPrototype]],
                 simulation_scenario: SimulationScenario):
        self.scms_dict = {}
        self.scenario_name = scenario_name

        self.service_chains_dict = {}
        self.microservices_dict = {}
        if service_chains is list:
            for service_chain in service_chains:
                self.service_chains_dict[service_chain.name] = deepcopy(service_chain)
                self.microservices_dict = \
                    self.microservices_dict | self.service_chains_dict[service_chain.name].microservices_dict
        elif service_chains is dict:
            self.service_chains_dict = deepcopy(service_chains)
            for service_chain_name, service_chain in enumerate(service_chains.values()):
                self.microservices_dict = \
                    self.microservices_dict | self.service_chains_dict[service_chain.name].microservices_dict

        self.topology = deepcopy(topology)
        self.placement_algorithm = deepcopy(placement_algorithm)

        self.resource_allocation_scenarios_dict = {}
        if resource_allocation_scenarios is list:
            for resource_allocation_scenario in resource_allocation_scenarios:
                self.resource_allocation_scenarios_dict[resource_allocation_scenario.name] = \
                    deepcopy(resource_allocation_scenario)
        elif resource_allocation_scenarios is dict:
            self.resource_allocation_scenarios_dict = deepcopy(resource_allocation_scenarios)

        self.affinity_prototypes_dict = {}
        if affinity_prototypes is list:
            for _prototype in affinity_prototypes:
                self.affinity_prototypes_dict[_prototype.name] = deepcopy(_prototype)
        else:
            self.affinity_prototypes_dict = deepcopy(affinity_prototypes)

        self.simulation_scenario = simulation_scenario

    @__init__.register
    def _(self,
          scenario_name: str,
          service_chains: Dict[str, ServiceChain],
          topology: Topology,
          # placement_scenario: PlacementScenario,
          placement_algorithm: PlacementAlgorithm,
          resource_allocation_scenarios: Dict[str, ResourceAllocationScenario],
          affinity_prototypes: Dict[str, AffinityPrototype],
          cluster_scenario: SimulationScenario):
        self.scms_dict = {}
        self.scenario_name = scenario_name
        self.service_chains_dict = deepcopy(service_chains)
        self.topology = deepcopy(topology)
        self.placement_algorithm = deepcopy(placement_algorithm)
        self.resource_allocation_scenarios_dict = deepcopy(resource_allocation_scenarios)
        self.affinity_prototypes_dict = deepcopy(affinity_prototypes)
        self.simulation_scenario = cluster_scenario
