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


import numpy as np


class CostCalculator:
    """
    This class is used to calculate the cost of the resources.
    """

    ALWAYS_ALLOC_CPU_PRICE_PER_VCPU_SEC = 0.000018
    ALWAYS_ALLOC_CPU_FREE_TIER_VPU_SEC_PER_MONTH = 240000
    ALWAYS_ALLOC_MEM_PRICE_PER_GB_SEC = 0.000002
    ALWAYS_ALLOC_MEM_FREE_TIER_GB_SEC_PER_MONTH = 450000

    ONLY_ALLOC_DURING_REQ_CPU_PRICE_PER_VCPU_SEC = 0.000024
    ONLY_ALLOC_DURING_REQ_CPU_PRICE_PER_VCPU_SEC_IDLE = 0.0000025
    ONLY_ALLOC_DURING_REQ_FREE_TIER_VPU_SEC_PER_MONTH = 180000
    ONLY_ALLOC_DURING_REQ_MEM_PRICE_PER_GB_SEC = 0.0000025
    ONLY_ALLOC_DURING_REQ_MEM_PRICE_PER_GB_SEC_IDLE = 0.0000025
    ONLY_ALLOC_DURING_REQ_MEM_FREE_TIER_GB_SEC_PER_MONTH = 360000
    ONLY_ALLOC_DURING_REQ_PRICE = 0.0000004
    ONLY_ALLOC_DURING_REQ_REQ_FREE_TIER_COUNT = 2000000

    concurrent_requests_per_container = 200
    requests = 3000000
    request_execution_time = 2

    @staticmethod
    def cost_for_always_allocated_instance(duration_in_sec: float, cores: int, memory: int, storage: int) -> float:
        """
        Calculate the cost of an instance that is always allocated.

        :param duration_in_sec:
        :param cores:
        :param memory:
        :param storage:
        :return:
        """

        # In simulator: One month time (2628000 seconds) * MIN(Min instances;Max intances at peak) * CPU cores
        cpu_allocation_time = duration_in_sec * 1 * cores

        # In simulator: CPU allocation time + (ABS(Max instances at peak - Min instances) * CPU cores * duration * 0,5)
        actual_cpu_allocation_time = cpu_allocation_time + (0 * cores * duration_in_sec * 0.5)

        # In simulator: Exactly as described below
        non_free_cpu_time = \
            np.max([0, actual_cpu_allocation_time - CostCalculator.ALWAYS_ALLOC_CPU_FREE_TIER_VPU_SEC_PER_MONTH])

        # In simulator: One month time (2628000 seconds) * MIN(Min instances;Max intances at peak) * Mem
        mem_allocation_time = duration_in_sec * 1 * memory

        # In simulator: Mem allocation time + (ABS(Max instances at peak - Min instances) * memory * duration * 0,5)
        actual_mem_allocation_time = mem_allocation_time + (0 * memory * duration_in_sec * 0.5)

        non_free_mem_time = \
            np.max([0, actual_mem_allocation_time - CostCalculator.ALWAYS_ALLOC_MEM_FREE_TIER_GB_SEC_PER_MONTH])

        result = non_free_cpu_time * CostCalculator.ALWAYS_ALLOC_CPU_PRICE_PER_VCPU_SEC + \
                 non_free_mem_time * CostCalculator.ALWAYS_ALLOC_MEM_PRICE_PER_GB_SEC

        return result

    @staticmethod
    def cost_for_only_allocated_during_request_instance(duration_in_sec: float,
                                                        cores: int,
                                                        memory: int,
                                                        storage: int,
                                                        concurrent_requests: int,
                                                        requests: int,
                                                        request_exec_time_ns: int) -> float:
        """
        Calculate the cost of an instance that is only allocated during a request.

        :param duration_in_sec:
        :param cores:
        :param memory:
        :param storage:
        :param concurrent_requests:
        :param requests:
        :param request_exec_time_ns:
        :return:
        """

        # The minimum cost of 1 instance
        cost_of_min_number_of_instances = \
            (duration_in_sec * CostCalculator.ONLY_ALLOC_DURING_REQ_CPU_PRICE_PER_VCPU_SEC_IDLE * cores + \
             duration_in_sec * CostCalculator.ONLY_ALLOC_DURING_REQ_MEM_PRICE_PER_GB_SEC_IDLE * memory) * 1

        number_of_req_non_free = np.max([0, requests - CostCalculator.ONLY_ALLOC_DURING_REQ_REQ_FREE_TIER_COUNT])

        req_cost = number_of_req_non_free * CostCalculator.ONLY_ALLOC_DURING_REQ_PRICE

        exec_time = request_exec_time_ns / 1000000000

        cpu_non_free_busy_time = \
            np.max([0,
                    (requests * (exec_time / concurrent_requests) * cores) -
                    CostCalculator.ONLY_ALLOC_DURING_REQ_FREE_TIER_VPU_SEC_PER_MONTH])

        busy_cpu_cost = cpu_non_free_busy_time * CostCalculator.ONLY_ALLOC_DURING_REQ_CPU_PRICE_PER_VCPU_SEC

        non_free_mem_time = np.max([0,
                                    (requests * (exec_time / concurrent_requests) * memory) -
                                    CostCalculator.ONLY_ALLOC_DURING_REQ_MEM_FREE_TIER_GB_SEC_PER_MONTH])

        busy_mem_cost = non_free_mem_time * CostCalculator.ONLY_ALLOC_DURING_REQ_MEM_PRICE_PER_GB_SEC

        result = (busy_mem_cost + busy_cpu_cost + req_cost) + cost_of_min_number_of_instances

        return result

    def __new__(cls):
        """
        Prevent instantiation of this class.
        """

        raise TypeError('Static classes cannot be instantiated')
