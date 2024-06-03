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

if TYPE_CHECKING:
    from perfsim import MicroservicePrototype


class MicroserviceEndpointFunctionPrototype:
    def __init__(self,
                 name: str,
                 id: int,
                 threads_instructions: List[int],
                 threads_avg_cpi: List[float],
                 threads_avg_cpu_usages: List[float],
                 threads_avg_mem_accesses: List[int],
                 threads_single_core_isolated_cache_misses: List[int],
                 threads_single_core_isolated_cache_refs: List[int],
                 threads_avg_cache_miss_penalty: List[float],
                 threads_avg_blkio_rw: List[int],
                 request_timeout: float,
                 microservice_prototype: MicroservicePrototype = None):
        if len(threads_instructions) != len(threads_avg_cpi) != len(
                threads_avg_cpu_usages):
            raise Exception("Mismatch in number of threads and length of provided instructions/cpis/cpu_usage lists " +
                            "for microservice endpoint function " + name)

        self.name = name
        self.id = id
        self.threads_count = len(threads_instructions)
        self.threads_instructions = threads_instructions
        self.threads_avg_cpi = threads_avg_cpi
        self.threads_avg_cpu_usages = threads_avg_cpu_usages
        self.threads_avg_mem_accesses = threads_avg_mem_accesses
        self.threads_single_core_isolated_cache_misses = threads_single_core_isolated_cache_misses
        self.threads_single_core_isolated_cache_refs = threads_single_core_isolated_cache_refs
        self.threads_avg_cache_miss_penalty = threads_avg_cache_miss_penalty
        self.threads_avg_blkio_rw = threads_avg_blkio_rw
        self.request_timeout = request_timeout if request_timeout != -1 else float('inf')
        self.microservice_prototype = microservice_prototype

    def add_threads(self,
                    threads_instructions,
                    threads_avg_cpi,
                    threads_avg_cpu_usage,
                    threads_avg_mem_accesses,
                    threads_single_core_isolated_cache_misses,
                    threads_single_core_isolated_cache_refs,
                    threads_avg_cache_miss_penalty,
                    threads_avg_blkio_rw):
        self.threads_instructions.extend(threads_instructions)
        self.threads_avg_cpi.extend(threads_avg_cpi)
        self.threads_avg_cpu_usages.extend(threads_avg_cpu_usage)
        self.threads_avg_mem_accesses.extend(threads_avg_mem_accesses)
        self.threads_single_core_isolated_cache_misses.extend(threads_single_core_isolated_cache_misses)
        self.threads_single_core_isolated_cache_refs.extend(threads_single_core_isolated_cache_refs)
        self.threads_avg_cache_miss_penalty.extend(threads_avg_cache_miss_penalty)
        self.threads_avg_blkio_rw.extend(threads_avg_blkio_rw)
        self.threads_count = len(self.threads_instructions)

    def __str__(self):
        return self.name
