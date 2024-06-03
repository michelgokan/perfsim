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

from typing import TYPE_CHECKING, List

from perfsim import MicroserviceEndpointFunctionPrototype

if TYPE_CHECKING:
    from perfsim import Microservice


class MicroserviceEndpointFunction(MicroserviceEndpointFunctionPrototype):
    __microservice: Microservice

    def __init__(self,
                 name: str,
                 id: int,
                 threads_instructions: List[int],
                 threads_avg_cpi: List[float],
                 threads_avg_cpu_usages: List[float],
                 # ms_request_size_in_chain: int,
                 threads_avg_mem_accesses: List[int],
                 threads_single_core_isolated_cache_misses: List[int],
                 threads_single_core_isolated_cache_refs: List[int],
                 threads_avg_cache_miss_penalty: List[float],
                 threads_avg_blkio_rw: List[int],
                 request_timeout: float = float('inf'),
                 microservice: Microservice = None):
        super().__init__(name=name,
                         id=id,
                         threads_instructions=threads_instructions,
                         threads_avg_cpi=threads_avg_cpi,
                         threads_avg_cpu_usages=threads_avg_cpu_usages,
                         threads_avg_mem_accesses=threads_avg_mem_accesses,
                         threads_single_core_isolated_cache_misses=threads_single_core_isolated_cache_misses,
                         threads_single_core_isolated_cache_refs=threads_single_core_isolated_cache_refs,
                         threads_avg_cache_miss_penalty=threads_avg_cache_miss_penalty,
                         threads_avg_blkio_rw=threads_avg_blkio_rw,
                         request_timeout=request_timeout)

        self.__microservice = microservice
        self.update_name_with_microservice_prefix()

    def update_name_with_microservice_prefix(self):
        if self.__microservice is not None:
            self.name = self.__microservice.name + "_" + self.name

    @property
    def microservice(self):
        return self.__microservice

    @microservice.setter
    def microservice(self, v: Microservice):
        if v is None:
            raise Exception("Setting microservice to None is forbidden!")
        self.__microservice = v
        self.update_name_with_microservice_prefix()

    @classmethod
    def from_prototype(cls,
                       name,
                       id,
                       prototype: MicroserviceEndpointFunctionPrototype,
                       microservice: Microservice = None):
        return cls(name=name,
                   id=id,
                   threads_instructions=prototype.threads_instructions,
                   threads_avg_cpi=prototype.threads_avg_cpi,
                   threads_avg_cpu_usages=prototype.threads_avg_cpu_usages,
                   threads_avg_mem_accesses=prototype.threads_avg_mem_accesses,
                   threads_single_core_isolated_cache_misses=prototype.threads_single_core_isolated_cache_misses,
                   threads_single_core_isolated_cache_refs=prototype.threads_single_core_isolated_cache_refs,
                   threads_avg_cache_miss_penalty=prototype.threads_avg_cache_miss_penalty,
                   threads_avg_blkio_rw=prototype.threads_avg_blkio_rw,
                   request_timeout=prototype.request_timeout,
                   microservice=microservice)
