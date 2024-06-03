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

import importlib
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Dict, Any, Set, List, Union

import pandas as pd

from perfsim import MicroserviceReplica, Host


class PlacementAlgorithm(ABC):
    name: str  #: Name of the placement algorithm instance (including options)
    _algorithm_name: str  #: Name of the placement algorithm
    options: Dict[str, Any]  #: Options for the placement algorithm

    def __init__(self, name: str, options: Dict[str, Any]):
        self.name = name
        self.options = options

    @abstractmethod
    def place(self, placement_matrix: pd.DataFrame, replicas: Set[MicroserviceReplica], hosts_dict: Dict[str, Host]):
        """
        Place the nodes in the simulation.

        :return: None
        """
        pass

    @property
    def algorithm_name(self):
        return self._algorithm_name

    @algorithm_name.setter
    def algorithm_name(self, algorithm_name: str):
        raise NotImplementedError("You can't set the algorithm name")

    @staticmethod
    def copy_to_dict(placement_algorithms: Union[List[PlacementAlgorithm], Dict[str, PlacementAlgorithm]]) \
            -> Dict[str, PlacementAlgorithm]:
        if isinstance(placement_algorithms, dict):
            return deepcopy(placement_algorithms)
        else:
            placement_algorithms_dict = {}

            for _placement_algorithm in placement_algorithms:
                placement_algorithms_dict[_placement_algorithm.name] = deepcopy(_placement_algorithm)

            return placement_algorithms_dict

    @staticmethod
    def from_config(conf: dict) -> dict[str, PlacementAlgorithm]:
        placement_algorithms_dict = {}

        for _algorithm_instance_id, _algorithm_instance_name in enumerate(conf):
            _scenario_data = conf[_algorithm_instance_name]
            _algorithm_module_name = _scenario_data["classpath"]
            _algorithm_class_name = _scenario_data["algorithm_class"]
            _placement_options = _scenario_data["options"]

            if _algorithm_module_name in globals():
                _algorithm_class = globals()[_algorithm_module_name]
            else:
                module = importlib.import_module(_algorithm_module_name)
                _algorithm_class = getattr(module, _algorithm_class_name)

            # _algorithm_class = getattr(globals()[_algorithm_module_name], _algorithm_class_name)
            # placement_algorithms_dict[_scenario_name] = PlacementScenario(name=_scenario_name,
            #                                                              algorithm=_placement_algorithm,
            #                                                              options=_placement_options)
            placement_algorithms_dict[_algorithm_instance_name] = _algorithm_class(name=_algorithm_instance_name,
                                                                                   options=_placement_options)
        return placement_algorithms_dict
