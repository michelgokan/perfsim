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

import json
from typing import Dict, List, TypedDict, Union, TYPE_CHECKING, Any

from perfsim import MicroservicePrototype, HostPrototype, RouterPrototype, TrafficPrototype, Host, Router, \
    TopologyLinkPrototype, Microservice, ServiceChain, ResourceAllocationScenario, \
    PlacementScenario, AffinityPrototype, SimulationScenario, AffinityScenario, \
    PlacementAlgorithm, Simulation, TopologyPrototype, SimulationScenarioManagerResultDict, ScalingScenario, \
    ResultsStorageDriver, FileStorageDriver

if TYPE_CHECKING:
    from perfsim import ResultsStorageDriver


class TopologyEquipmentSet(TypedDict):
    hosts: Dict[str, Host]
    routers: Dict[str, Router]


class SimulationScenarioManager:
    """
    This class represents a simulation scenario manager. It is responsible for managing simulation scenarios.
    """

    microservice_prototypes_dict: dict[str, MicroservicePrototype]
    host_prototypes_dict: dict[str, HostPrototype]
    router_prototypes_dict: dict[str, RouterPrototype]
    traffic_prototypes_dict: dict[str, TrafficPrototype]
    link_prototypes_dict: dict[str, TopologyLinkPrototype]
    topology_equipments_dict: dict[str, TopologyEquipmentSet]
    service_chains_dict: dict[str, ServiceChain]
    topologies_prototype_dict: dict[str, TopologyPrototype]
    microservices_dict: dict[str, Microservice]
    simulation_scenarios_dict: dict[str, SimulationScenario]
    simulations_dict: dict[str, Simulation]
    affinity_prototypes_dict: dict[str, AffinityPrototype]
    res_alloc_scenarios_dict: dict[str, ResourceAllocationScenario]
    placement_scenarios_dict: dict[str, PlacementScenario]
    placement_algorithms_dict: dict[str, PlacementAlgorithm]
    results_storage_driver: 'ResultsStorageDriver'

    @classmethod
    def from_config_file(cls, config_file_path: str = None):
        if config_file_path is None:
            raise Exception("Either config_file_path should be provided to initiate a ScenarioManager!")
        try:
            _config = json.load(open(config_file_path, "r"))
        except ValueError:
            raise Exception("Decoding JSON has failed!")

        return cls.from_config(_config)

    @staticmethod
    def get_obj(subj: Any, key: str, attr: str, attr_key: Union[str, None], conf: Dict,
                sm: Union[None, 'SimulationScenarioManager'], **other):
        """
        This method first checks if the provided key is exists in the provided configuration dictionary. If it is, it
        returns the result of `from_config` method of the provided class (subj). If not, it checks if an existing
        SimulationScenarioManager is provided (e.g., if the scenario manager is already initialized). If it is, it
        returns the requested attribute (attr_key) of the provided SimulationScenarioManager (sm). If not, it raises
        a ValueError exception.

        The benefit of this method is that it allows to use the same configuration file and/or an existing
        SimulationScenarioManager to initialize a new SimulationScenarioManager.
        """

        key_list = key.split(".")
        conf_dict = conf

        if len(key_list) == 0:
            raise ValueError(f"Key cannot be empty!")

        for key_item in key_list:
            if key_item in conf_dict:
                conf_dict = conf_dict[key_item]
            elif sm is not None:
                sm_attr = getattr(sm, attr)
                attr_key_list = attr_key.split(".")

                for attr_key_item in attr_key_list:
                    if attr_key_item in sm_attr:
                        sm_attr = sm_attr[attr_key_item]
                    else:
                        raise Exception(f"{attr_key_item} not found in {attr}!")

                return sm_attr
            else:
                raise ValueError(f"{key_item} is not defined in the configuration file!")

        return subj.from_config(conf=conf_dict, **other)

    @classmethod
    def from_config(cls, conf: Dict = None, existing_scenario_manager: 'SimulationScenarioManager' = None):
        if conf is None:
            raise Exception("Either config or sm object should be provided to initiate a ScenarioManager!")

        topology_equipments_dict: dict[str, TopologyEquipmentSet] = {}
        microservice_prototypes_dict = cls.get_obj(subj=MicroservicePrototype, key="prototypes.microservices",
                                                   attr="microservice_prototypes_dict", attr_key=None, conf=conf,
                                                   sm=existing_scenario_manager)
        host_prototypes_dict = cls.get_obj(subj=HostPrototype, key="prototypes.hosts",
                                           attr="host_prototypes_dict", attr_key=None, conf=conf,
                                           sm=existing_scenario_manager)
        router_prototypes_dict = cls.get_obj(subj=RouterPrototype, key="prototypes.routers",
                                             attr="router_prototypes_dict", attr_key=None, conf=conf,
                                             sm=existing_scenario_manager)
        link_prototypes_dict = cls.get_obj(subj=TopologyLinkPrototype, key="prototypes.links",
                                           attr="link_prototypes_dict", attr_key=None, conf=conf,
                                           sm=existing_scenario_manager)
        traffic_prototypes_dict = cls.get_obj(subj=TrafficPrototype, key="prototypes.traffics",
                                              attr="traffic_prototypes_dict", attr_key=None, conf=conf,
                                              sm=existing_scenario_manager)
        for _topology_id, _topology_name in enumerate(conf["topologies"]):
            topology_equipments_dict[_topology_name] = {"hosts": {}, "routers": {}}
            topology_equipments_dict[_topology_name]["hosts"] = \
                cls.get_obj(subj=Host, key="equipments.hosts", attr="topology_equipments_dict",
                            attr_key="equipments.hosts", conf=conf, sm=existing_scenario_manager,
                            host_prototypes_dict=host_prototypes_dict)
            topology_equipments_dict[_topology_name]["routers"] = \
                cls.get_obj(subj=Router, key="equipments.routers", attr="topology_equipments_dict",
                            attr_key="equipments.routers", conf=conf, sm=existing_scenario_manager,
                            router_prototypes_dict=router_prototypes_dict)
        topology_prototypes_dict = \
            cls.get_obj(subj=TopologyPrototype, key="topologies", attr="topology_prototypes_dict", attr_key=None,
                        conf=conf, sm=existing_scenario_manager, topology_equipments_dict=topology_equipments_dict,
                        link_prototypes_dict=link_prototypes_dict)
        service_chains_dict = cls.get_obj(subj=ServiceChain, key="service_chains", attr="service_chains_dict",
                                          attr_key=None, conf=conf, sm=existing_scenario_manager,
                                          microservice_prototypes_dict=microservice_prototypes_dict)
        resource_allocation_scenarios_dict = \
            cls.get_obj(subj=ResourceAllocationScenario, key="resource_allocation_scenarios",
                        attr="resource_allocation_scenarios_dict", attr_key=None, conf=conf,
                        sm=existing_scenario_manager)
        results_storage_driver = \
            cls.get_obj(subj=ResultsStorageDriver, key="storage_driver", attr="results_storage_driver",
                        attr_key=None, conf=conf, sm=existing_scenario_manager, default_class=FileStorageDriver,
                        name="file_storage_driver1", file_path="./results/")
        placement_algorithms_dict = \
            cls.get_obj(subj=PlacementAlgorithm, key="placement_algorithms", attr="placement_algorithms_dict",
                        attr_key=None, conf=conf, sm=existing_scenario_manager)
        affinity_prototypes_dict = \
            cls.get_obj(subj=AffinityPrototype, key="affinity_rulesets", attr="affinity_prototypes_dict",
                        attr_key=None, conf=conf, sm=existing_scenario_manager)
        simulation_scenarios_dict = \
            cls.get_obj(subj=SimulationScenario, key="simulation_scenarios", attr="simulation_scenarios_dict",
                        attr_key=None, conf=conf, sm=existing_scenario_manager)

        return cls(simulation_scenarios=simulation_scenarios_dict,
                   service_chains=service_chains_dict,
                   topology_prototypes=topology_prototypes_dict,
                   placement_algorithms=placement_algorithms_dict,
                   res_alloc_scenarios=resource_allocation_scenarios_dict,
                   affinity_prototypes=affinity_prototypes_dict,
                   traffic_prototypes=traffic_prototypes_dict,
                   results_storage_driver=results_storage_driver)

    def __init__(self,
                 simulation_scenarios: Union[List[SimulationScenario], Dict[str, SimulationScenario]],
                 service_chains: Union[List[ServiceChain], Dict[str, ServiceChain]],
                 topology_prototypes: Union[List[TopologyPrototype], Dict[str, TopologyPrototype]],
                 placement_algorithms: Union[List[PlacementAlgorithm], Dict[str, PlacementAlgorithm]],
                 res_alloc_scenarios: Union[List[ResourceAllocationScenario], Dict[str, ResourceAllocationScenario]],
                 affinity_prototypes: Union[List[AffinityPrototype], Dict[str, AffinityPrototype]],
                 traffic_prototypes: Union[List[TrafficPrototype], Dict[str, TrafficPrototype]],
                 results_storage_driver: ResultsStorageDriver):
        self.res_alloc_scenarios_dict = ResourceAllocationScenario.copy_to_dict(res_alloc_scenarios=res_alloc_scenarios)
        self.affinity_prototypes_dict = AffinityPrototype.copy_to_dict(affinity_prototypes=affinity_prototypes)
        self.service_chains_dict, self.microservices_dict = ServiceChain.copy_to_dict(service_chains=service_chains)
        self.topologies_prototype_dict = TopologyPrototype.copy_to_dict(topology_prototypes=topology_prototypes)
        self.placement_algorithms_dict = PlacementAlgorithm.copy_to_dict(placement_algorithms=placement_algorithms)
        self.traffic_prototypes_dict = TrafficPrototype.copy_to_dict(traffic_prototypes=traffic_prototypes)
        self.simulation_scenarios_dict = Simulation.copy_sim_scenarios_to_dict(sim_scenarios=simulation_scenarios)
        self.results_storage_driver = results_storage_driver

        self.validate_simulation_scenarios()
        self.simulations_dict = Simulation.from_scenarios_manager(sm=self)

    def validate_simulation_scenarios(self):
        for sim_scenario in self.simulation_scenarios_dict.values():
            for service_chain in sim_scenario['traffic_scenario']['service_chains']:
                traffic_prototype = sim_scenario['traffic_scenario']['service_chains'][service_chain]['traffic_type']
                self.validate_service_chain(service_chain=service_chain)
                self.validate_traffic_prototype(traffic_prototype=traffic_prototype)

            self.validate_scaling_scenarios(scaling_scenarios=sim_scenario['scaling_scenarios'])
            self.validate_affinity_scenarios(affinity_scenarios=sim_scenario['affinity_scenarios'])
            self.validate_placement_algorithms(placement_algorithm=sim_scenario['placement_algorithm'])
            self.validate_topology(topology=sim_scenario['topology'])

    def validate_traffic_prototype(self, traffic_prototype: str):
        if traffic_prototype not in self.traffic_prototypes_dict.keys():
            raise ValueError(f"Traffic type {traffic_prototype} is not defined in the simulation")

    def validate_service_chain(self, service_chain: str):
        if service_chain not in self.service_chains_dict.keys():
            raise ValueError(f"Service chain {service_chain} is not defined in the simulation")

    def validate_scaling_scenarios(self, scaling_scenarios: List[ScalingScenario]):
        for scaling_scenario in scaling_scenarios:
            if next(iter(scaling_scenario['microservice'])) not in self.microservices_dict.keys():
                raise ValueError(f"Microservice {scaling_scenario['microservice']['name']} not found in the "
                                 f"microservices list: {list(self.microservices_dict.keys())}")

    def validate_affinity_scenarios(self, affinity_scenarios: List[AffinityScenario]):
        for affinity_scenario in affinity_scenarios:
            if next(iter(affinity_scenario['microservice'])) not in self.affinity_prototypes_dict.keys():
                raise ValueError(f"Microservice {affinity_scenario['microservice']['name']} not found in the "
                                 f"affinity prototypes list: {list(self.affinity_prototypes_dict.keys())}")

    def validate_placement_algorithms(self, placement_algorithm: str):
        if placement_algorithm not in self.placement_algorithms_dict.keys():
            raise ValueError(f"Placement algorithm {placement_algorithm} not found in the "
                             f"placement algorithms list: {list(self.placement_algorithms_dict.keys())}")

    def validate_topology(self, topology: str):
        if topology not in self.topologies_prototype_dict.keys():
            raise ValueError(f"Topology {topology} not found in the "
                             f"topologies prototypes list: {list(self.topologies_prototype_dict.keys())}")

    def get_all_latencies(self) -> SimulationScenarioManagerResultDict:
        result: SimulationScenarioManagerResultDict = {"simulation_scenarios": {}}
        for scenario in self.simulation_scenarios_dict:
            result["simulation_scenarios"][scenario] = \
                self.simulations_dict[scenario].load_generator.get_latencies_grouped_by_sfc()
        return result

    def save_all(self):
        results = {}
        for sim_name, sim in self.simulations_dict.items():
            results[sim_name] = sim.storage_driver.save_simulation_scenario_results(simulation=sim)
        return results
    # def reinit(self, file_path: str = None, config: Dict = None, setup_cluster_and_load_generators: bool = True):
    #     self.__init__.py(file_path, config, setup_cluster_and_load_generators, init=True)
