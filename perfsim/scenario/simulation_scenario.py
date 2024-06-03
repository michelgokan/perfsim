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

from typing import List, TypedDict, Dict

from perfsim import TrafficScenario, ScalingScenario, AffinityScenario, DebugDict


class SimulationScenario(TypedDict):
    """
    This class represents a simulation scenario.
    """

    #: name is the name of the simulation scenario
    name: str

    #: traffic_scenario is the traffic scenario of the simulation scenario
    traffic_scenario: TrafficScenario

    #: scaling_scenarios is the scaling scenario of the simulation scenario
    scaling_scenarios: List[ScalingScenario]

    #: affinity_scenarios is the affinity scenario of the simulation scenario
    affinity_scenarios: List[AffinityScenario]

    #: placement_algorithm is the placement algorithm of the simulation scenario
    placement_algorithm: str

    #: topology is the topology of the simulation scenario
    topology: str

    #: network_timeout is the network timeout of the simulation scenario
    network_timeout: int

    #: The debug configuration of the simulation scenario.
    debug: DebugDict

    @staticmethod
    def from_config(conf: Dict) -> dict[str, 'SimulationScenario']:
        """
        Create a dictionary of simulation scenarios from a configuration dictionary.

        :param conf:
        :return:
        """

        simulation_scenarios_dict = {}

        for _scenario_id, _scenario_name in enumerate(conf):
            simulation_scenarios_dict[_scenario_name]: SimulationScenario = conf[_scenario_name]

        return simulation_scenarios_dict
