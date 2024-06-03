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
from typing import List, Union, Dict


class AffinityPrototype:
    def __init__(self,
                 name: str,
                 affinity_microservices: List[str],
                 antiaffinity_microservices: List[str],
                 affinity_hosts: List[str],
                 antiaffinity_hosts: List[str]):
        self.name = name
        self.affinity_microservices = affinity_microservices
        self.affinity_hosts = affinity_hosts
        self.antiaffinity_microservices = antiaffinity_microservices
        self.antiaffinity_hosts = antiaffinity_hosts

    @staticmethod
    def copy_to_dict(affinity_prototypes: Union[List[AffinityPrototype], Dict[str, AffinityPrototype]]) \
            -> dict[str, AffinityPrototype]:
        if isinstance(affinity_prototypes, dict):
            return deepcopy(affinity_prototypes)
        else:
            affinity_prototypes_dict = {}

            for _prototype in affinity_prototypes:
                affinity_prototypes_dict[_prototype.name] = deepcopy(_prototype)

            return affinity_prototypes_dict

    @staticmethod
    def from_config(conf: dict) -> Dict[str, AffinityPrototype]:
        affinity_prototypes_dict = {}

        for _affinity_id, _affinity_name in enumerate(conf):
            _ruleset_data = conf[_affinity_name]
            _microservice_affinities = _ruleset_data["affinity"]["microservice"]
            _host_affinities = _ruleset_data["affinity"]["host"]
            _microservice_antiaffinities = _ruleset_data["anti-affinity"]["microservice"]
            _host_antiaffinities = _ruleset_data["anti-affinity"]["host"]
            affinity_prototypes_dict[_affinity_name] = \
                AffinityPrototype(name=_affinity_name,
                                  affinity_microservices=_microservice_affinities,
                                  antiaffinity_microservices=_microservice_antiaffinities,
                                  affinity_hosts=_host_affinities,
                                  antiaffinity_hosts=_host_antiaffinities)

        return affinity_prototypes_dict
