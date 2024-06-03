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
from typing import Union, Dict, List, Any, TYPE_CHECKING

from perfsim import SimulationScenario, ServiceChain, PlacementAlgorithm, ResourceAllocationScenario, \
    AffinityPrototype, Microservice, TrafficPrototype, LoadGenerator, Cluster, Logger, TopologyPrototype, Topology, \
    ResultsStorageDriver

if TYPE_CHECKING:
    from perfsim import SimulationScenarioManager


class Simulation:
    """
    This class represents a simulation. It contains all the necessary information to run a simulation.
    """

    #: microservices_dict is a dictionary of microservices
    microservices_dict: Dict[str, Microservice]

    #: service_chains_dict is a dictionary of service chains
    service_chains_dict: Dict[str, ServiceChain]

    #: placement_algorithm is the algorithm used to place the microservices
    affinity_prototypes_dict: Dict[str, AffinityPrototype]

    #: resource_allocation_scenarios_dict is a dictionary of resource allocation scenarios
    resource_allocation_scenarios_dict: Dict[str, ResourceAllocationScenario]

    #: topology is the topology of the simulation
    topology: Topology

    #: traffic_prototypes_dict is a dictionary of traffic prototypes
    traffic_prototypes_dict: Dict[str, TrafficPrototype]

    #: scenario is the simulation scenario
    scenario: SimulationScenario

    #: cluster is the cluster of the simulation
    cluster: Cluster

    #: load_generator is the load generator of the simulation
    load_generator: LoadGenerator

    #: storage_driver is the storage driver of the simulation
    storage_driver: ResultsStorageDriver

    #: The name of the simulation
    name: str

    #: Status of debug mode (automatically configured based on _debug_level)
    _debug: bool

    #: Level of debug verbosity (1-5)
    _debug_level: bool

    #: Collects various logs during simulation
    logger: Logger

    #: Stores the location of the log file (if set to None, logs are not saved)
    _debug_file_location: str

    #: If set yes, we collect CPU events (task load balancing) for each core in all hosts. Use for debug purposes only!
    _log_cpu_events: bool

    #: If set yes, we collect all events as a timeline. Use for debug purposes only!
    _log_timeline: bool

    #: The simulation clock (in ns). Other classes use this parameter to know current simulation time.
    _time: int

    DEFAULT_DEBUG_LEVEL = 0
    DEFAULT_DEBUG_FILE_LOCATION = False
    DEFAULT_LOG_CPU_EVENTS = False
    DEFAULT_LOG_TIMELINE = False

    def __init__(self,
                 name: str,
                 simulation_scenario: SimulationScenario,
                 service_chains_dict: Dict[str, ServiceChain],
                 topology_prototype: TopologyPrototype,
                 placement_algorithm: PlacementAlgorithm,
                 resource_allocation_scenarios_dict: Dict[str, ResourceAllocationScenario],
                 affinity_prototypes_dict: Dict[str, AffinityPrototype],
                 traffic_prototypes_dict: Dict[str, TrafficPrototype],
                 storage_driver: ResultsStorageDriver,
                 validate: bool = False,
                 copy: bool = True):
        self.name = name
        self.time = 0
        self.scenario = self.set_object(simulation_scenario, copy)
        self.set_debug_properties(
            level=self.__get_debug_param(name="debug_level", default=self.DEFAULT_DEBUG_LEVEL),
            file_path=self.__get_debug_param(name="debug_file_location", default=self.DEFAULT_DEBUG_FILE_LOCATION),
            log_cpu_events=self.__get_debug_param(name="log_cpu_events", default=self.DEFAULT_LOG_CPU_EVENTS),
            log_timeline=self.__get_debug_param(name="log_timeline", default=self.DEFAULT_LOG_TIMELINE))
        self.logger = Logger(simulation=self)
        # self.simulation_scenario_manager = simulation_scenario_manager
        self.service_chains_dict = self.set_object(service_chains_dict, copy)
        self.microservices_dict = ServiceChain.microservices_to_dict_from_dict(service_chains=self.service_chains_dict)
        if validate: self.validate_simulation_scenario(sim_scenario=simulation_scenario)
        self.topology = Topology.from_prototype(prototype=topology_prototype, simulation=self, copy=copy)
        # self.topology.sim = self
        # in topology to man daram copy mikonam ke baes mishe simulatione toosham copy beshe, deghat kon ke maa hamin
        # alan too simulation hastim, vase hamin baes mishe 2 ta simulation ijad beshe....in bayad dorost she
        self.placement_algorithm = self.set_object(placement_algorithm, copy)
        self.resource_allocation_scenarios_dict = self.set_object(resource_allocation_scenarios_dict, copy)
        self.affinity_prototypes_dict = self.set_object(affinity_prototypes_dict, copy)
        self.traffic_prototypes_dict = self.set_object(traffic_prototypes_dict, copy)
        self.storage_driver = storage_driver

        self.setting_scaling_scenario()
        self.setting_affinity_scenarios()

        self.cluster = Cluster(name=self.name,
                               simulation=self,
                               topology=self.topology,
                               service_chains_dict=self.service_chains_dict)
        self.load_generator = LoadGenerator(name=self.scenario["traffic_scenario"]["name"], simulation=self)

    @staticmethod
    def set_object(obj: Any, copy: bool):
        """
        Set an object with or without copy

        :param obj:
        :param copy:
        :return:
        """
        if copy:
            return deepcopy(obj)
        else:
            return obj

    def setting_scaling_scenario(self):
        """
        Setting the scaling scenario

        :return: None
        """
        for scaling_scenario in self.scenario["scaling_scenarios"]:
            for microservice_name in list(scaling_scenario["microservice"].keys()):
                ras_name = scaling_scenario["microservice"][microservice_name]["resource_allocation_scenario"]
                replica_count = scaling_scenario["microservice"][microservice_name]["replica_count"]

                ms = self.microservices_dict[microservice_name]
                ras = self.resource_allocation_scenarios_dict[ras_name]

                ms.cpu_requests = ras.cpu_requests
                ms.cpu_limits = ras.cpu_limits
                ms.memory_requests = ras.memory_requests
                ms.ingress_bw = ras.ingress_bw
                ms.egress_bw = ras.egress_bw
                ms.ingress_latency = ras.ingress_latency
                ms.egress_latency = ras.egress_latency
                ms.blkio_capacity = ras.blkio_capacity
                ms.resource_allocation_scenario = ras
                ms.replica_count = replica_count

    def setting_affinity_scenarios(self):
        """
        Setting the affinity scenarios

        :return:
        """

        for affinity_ruleset in self.scenario["affinity_scenarios"]:
            microservice_name = list(affinity_ruleset["microservice"].keys())[0]
            ms = self.microservices_dict[microservice_name]
            affinity_ruleset_name = affinity_ruleset["microservice"][microservice_name]["affinity_ruleset"]

            if affinity_ruleset_name is not None:
                ruleset = self.affinity_prototypes_dict[affinity_ruleset_name]

                for affinity_ms_name in ruleset.affinity_microservices:
                    ms.add_microservice_affinity_with(self.microservices_dict[affinity_ms_name])

                for antiaffinity_ms_name in ruleset.antiaffinity_microservices:
                    ms.add_microservice_anti_affinity_with(self.microservices_dict[antiaffinity_ms_name])

                for affinity_host_name in ruleset.affinity_hosts:
                    ms.add_host_affinity_with(self.topology.hosts_dict[affinity_host_name])

                for antiaffinity_host_name in ruleset.antiaffinity_hosts:
                    ms.add_host_anti_affinity_with(self.topology.hosts_dict[antiaffinity_host_name])

    def validate_simulation_scenario(self, sim_scenario: dict):
        """
        Validate the simulation scenario to make sure all the microservices are in the simulation scenario
        It raises an exception if a microservice is not found in the simulation scenario

        :param sim_scenario:  The simulation scenario
        :return: None
        """

        for microservice in sim_scenario["microservices"]:
            if microservice.name not in self.microservices_dict:
                raise Exception("Microservice {} not found in microservices".format(microservice.name))

    @staticmethod
    def copy_sim_scenarios_to_dict(sim_scenarios: Union[List[SimulationScenario], Dict[str, SimulationScenario]]) \
            -> Dict[str, SimulationScenario]:
        """
        Copy simulation scenarios to a dictionary

        :param sim_scenarios:
        :return:
        """

        if isinstance(sim_scenarios, dict):
            return deepcopy(sim_scenarios)
        else:
            simulation_scenarios_dict = {}

            for scenario in sim_scenarios:
                simulation_scenarios_dict[scenario['name']] = deepcopy(scenario)

            return simulation_scenarios_dict

    def __get_debug_param(self, name: str, value: Any = None, default: Any = None):
        """
        Get a debug parameter

        :param name:
        :param value:
        :param default:
        :return:
        """

        scenario_debug_config = self.scenario["debug"] if "debug" in self.scenario else {}

        if value is None:
            if name in scenario_debug_config:
                return scenario_debug_config[name]
            elif default is not None:
                return default
            else:
                raise Exception("Debug parameter {} not found in scenario debug config".format(name))
        else:
            return value

    def set_debug_properties(self,
                             level: Union[bool, int] = None,
                             file_path: str = None,
                             log_cpu_events: bool = None,
                             log_timeline: bool = None):
        """
        Set debug properties

        :param level:
        :param file_path:
        :param log_cpu_events:
        :param log_timeline:
        :return:
        """

        self.debug_level = self.__get_debug_param("debug_level", level)
        self.debug_file_location = self.__get_debug_param("debug_file_location", file_path)
        self._log_cpu_events = self.__get_debug_param("log_cpu_events", log_cpu_events)
        self._log_timeline = self.__get_debug_param("log_timeline", log_timeline)

    @property
    def log_timeline(self):
        """
        Log timeline

        :return:
        """
        return self._log_timeline

    @property
    def debug(self):
        """
        Status of debug mode (automatically configured based on _debug_level)

        :return:
        """
        return self._debug

    @property
    def debug_level(self):
        """
        Level of debug verbosity (1-5)

        :return: Return debug level
        """
        return self._debug_level

    @debug_level.setter
    def debug_level(self, debug_level: Union[int, bool]):
        """
        Set debug level (1-5)
        :param debug_level:  Debug level (1-5)
        :return:  None
        """

        self._debug = False if debug_level == 0 or debug_level is False else True
        self._debug_level = 0 if self._debug is False or debug_level < 0 else debug_level

    @property
    def debug_file_location(self):
        """
        Return log file location
        :return: Log file path - None if empty (then log will print out in console)
        :rtype: str
        """

        return self._debug_file_location

    @debug_file_location.setter
    def debug_file_location(self, debug_file_location: str):
        self._debug_file_location = debug_file_location

    @property
    def log_cpu_events(self):
        """
        Status of logging CPU events (used for drawing task load balancing heatmaps)
        :return: bool
        """

        return self._log_cpu_events

    @property
    def time(self) -> int:
        """
        Simulation time
        :return: Simulation time
        :rtype: float
        """

        return self._time

    @time.setter
    def time(self, v: int):
        """
        Set simulation time

        :param v:
        :return:
        """

        self._time = v

    @staticmethod
    def from_scenarios_manager(sm: 'SimulationScenarioManager') -> dict[str, 'Simulation']:
        """
        Create simulations from scenarios manager

        :param sm:
        :return:
        """

        simulations_dict = {}

        for scenario in sm.simulation_scenarios_dict.values():
            simulations_dict[scenario["name"]] = \
                Simulation(name=scenario["name"],
                           simulation_scenario=scenario,
                           service_chains_dict=sm.service_chains_dict,
                           topology_prototype=sm.topologies_prototype_dict[scenario["topology"]],
                           placement_algorithm=sm.placement_algorithms_dict[scenario["placement_algorithm"]],
                           resource_allocation_scenarios_dict=sm.res_alloc_scenarios_dict,
                           affinity_prototypes_dict=sm.affinity_prototypes_dict,
                           traffic_prototypes_dict=sm.traffic_prototypes_dict,
                           storage_driver=sm.results_storage_driver)

        return simulations_dict
