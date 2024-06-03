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

from typing import List, Dict

# if TYPE_CHECKING:
from perfsim import MicroserviceEndpointFunctionPrototype


class MicroservicePrototype:
    def __init__(self, name: str, endpoint_function_prototypes: List[MicroserviceEndpointFunctionPrototype] = None):
        if endpoint_function_prototypes is None:
            endpoint_function_prototypes = []
        self.name = name

        self._endpoint_function_prototypes_dict = {}
        for endpoint_function_prototype in endpoint_function_prototypes:
            self.add_endpoint_function_prototype(prototype=endpoint_function_prototype)

    @property
    def endpoint_function_prototypes_dict(self):
        return self._endpoint_function_prototypes_dict

    @endpoint_function_prototypes_dict.setter
    def endpoint_function_prototypes_dict(self, value):
        raise Exception("Cannot modify endpoint_function_prototypes_dict directly. "
                        "Use add_endpoint_function_prototype() or remove_endpoint_function_prototype() instead.")

    def add_endpoint_function_prototype(self, prototype: MicroserviceEndpointFunctionPrototype):
        if prototype.name in self.endpoint_function_prototypes_dict:
            raise Exception("Endpoint function prototype with name {} already exists.".format(prototype.name))
        self._endpoint_function_prototypes_dict[prototype.name] = prototype

    def remove_endpoint_function_prototype(self, prototype: MicroserviceEndpointFunctionPrototype):
        if prototype.name not in self.endpoint_function_prototypes_dict:
            raise Exception("Endpoint function prototype with name {} does not exist.".format(prototype.name))
        del self._endpoint_function_prototypes_dict[prototype.name]

    @staticmethod
    def from_config(conf: Dict = None) -> dict[str, MicroservicePrototype]:
        microservice_prototypes_dict = {}

        for _microservice_id, _microservice_name in enumerate(conf):
            _microservice_prototype = MicroservicePrototype(name=_microservice_name)

            for function_id, function_name in enumerate(conf[_microservice_name]):
                _prototype_data = conf[_microservice_name][function_name]
                _microservice_prototype.endpoint_function_prototypes_dict[function_name] = \
                    MicroserviceEndpointFunctionPrototype(
                        name=function_name,
                        id=function_id,
                        threads_instructions=_prototype_data["instructions"],
                        threads_avg_cpi=_prototype_data["avg_cpi"],
                        threads_avg_cpu_usages=_prototype_data["avg_cpu_usage"],
                        threads_avg_mem_accesses=_prototype_data["memory_accesses"],
                        threads_single_core_isolated_cache_misses=_prototype_data["single_core_isolated_cache_misses"],
                        threads_single_core_isolated_cache_refs=_prototype_data["single_core_isolated_cache_refs"],
                        threads_avg_cache_miss_penalty=_prototype_data["avg_cache_miss_penalty"],
                        threads_avg_blkio_rw=_prototype_data["avg_blkio_rw"],
                        request_timeout=_prototype_data["request_timeout"],
                        microservice_prototype=_microservice_prototype)

            microservice_prototypes_dict[_microservice_name] = _microservice_prototype

        return microservice_prototypes_dict
