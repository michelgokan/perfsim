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

from perfsim import FirstFit, MicroserviceReplica, Host


class FirstFitDecreasing(FirstFit):
    def place(self, placement_matrix: pd.DataFrame, replicas: Set[MicroserviceReplica], hosts_dict: Dict[str, Host]):
        self.first_fit_decreasing(placement_matrix, replicas, hosts_dict)

    def first_fit_decreasing(self, placement_matrix: pd.DataFrame, replicas: Set[MicroserviceReplica],
                             hosts_dict: Dict[str, Host] = None) -> None:
        replicas.sort(key=lambda x: x.microservice.cpu_requests, reverse=True)
        self.first_fit(placement_matrix, replicas, hosts_dict)

    def __init__(self, name: str, options: Dict[str, Any]):
        super().__init__(name=name, options=options)
        self._algorithm_name = self.__class__.__name__
