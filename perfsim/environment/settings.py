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
import pandas as pd


def get_space(size, low, high):
    """
    Get a space of size with low and high values.

    :param size:
    :param low:
    :param high:
    :return:
    """

    low_list = np.tile(low, size)
    high_list = low_list + (high - low)

    return low_list, high_list


def merge_spaces(spaces):
    """
    Merge multiple spaces into one.

    :param spaces:
    :return:
    """

    merged_space = {"low": [], "high": []}
    for space in spaces:
        merged_space["low"] = np.concatenate([merged_space["low"], spaces[space][0]]).astype(int)
        merged_space["high"] = np.concatenate([merged_space["high"], spaces[space][1]]).astype(int)

    return merged_space


class Settings:
    """
    The Settings class is a class that contains the settings of the simulation.
    """

    indices = ['ms_count',
               'sc_edge_bytes',
               'cfs_period_ns',
               'ms_replica_cpu_requests_shares',
               'ms_replica_cpu_limits',
               'host_cpu_core_count',
               'sc_arrival_rate',
               'ms_replica_thread_count',
               'ms_replica_count',
               'host_network_bandwidth',
               'host_cpu_clock_rate',
               'ms_replica_thread_instructions',
               'ms_replica_thread_avg_cpi',
               'ms_replica_reserved_network_bandwidth',
               'ms_replica_average_cpu_usage',
               'ms_replica_thread_average_cpu_utilization',
               # lets assume a thread got 100ms cpu time, this parameter indicated how much cpu will a thread utilize within the given period of cpu time.
               'ms_replica_thread_weight',
               'sched_min_granularity_ns',
               'sched_latency_ns',
               'load_balancing_threshold',
               'nice_0_load']

    columns = ['min', 'max', 'chunks']

    data = np.array(
        [[1, 10, 10],  # MS_COUNT
         [1000, 1 * 1000 * 1000, 10],
         # SC_EDGE_BYTES ~> 1000 bytes = 1 kilobytes / 1 megabytes = 1 * 1000 * 1000 bytes
         [100, 100, 1],  # CFS_PERIOD_NS
         [0.5 * 1024, 8 * 1024, 16],  # MS_REPLICA_CPU_SIZE
         # [50, 800, 16],  # MS_REPLICA_cpu_limits_NS
         [0.5 * 1024, 8 * 1024, 16],  # MS_REPLICA_cpu_limits
         [8, 8, 1],  # CPU_ON_EACH_HOST
         [10, 10000, 10],  # ARRIVAL_RATE
         [1, 10, 10],  # MS_THREADS
         [1, 5, 5],  # MS_REPLICA_SIZE
         [100 * 125000, 10 * 1000 * 125000, 2],  # HOST_LINK_BANDWIDTH ~> 100Mbps = 12,500,000 bytes per second
         [3.4 * 1000 * 1000 * 1000, 3.4 * 1000 * 1000 * 1000, 1],  # HOST_CPU_CLOCK_RATE ~> in Nano Hertz
         [1000000 * 1, 10000000000 * 1, 10],
         # MS_THREAD_INSTRUCTIONS ~> maximum 10,000,000,000 instructions per microservice
         [1, 1, 1],  # ms_replica_thread_avg_cpi
         [0, 0, 1],  # MS_REPLICA_RESERVED_NET_BANDWIDTH ~> 0=best effort
         [10, 100, 10],  # MS CPU USAGE / LOAD
         [1, 1, 1],  # ms_replica_thread_average_cpu_utilization (when getting CPU time)
         [1, 1, 1],  # threads weight
         [2, 2, 1],  # sched_min_granularity_ns
         [6, 6, 1],  # sched_latency_ns
         [0.05, 0.05, 1],  # load_balancing_threshold
         [1024, 1024, 1]  # NICE_0_LOAD
         ]).astype(int).tolist()

    args = pd.DataFrame(data, indices, columns)

    chunks = {}
    for index, row in args.iterrows():
        chunks[index] = np.linspace(row["min"], row["max"], row["chunks"], dtype="int64")

    _ms_partial_sum = int(((args.loc['ms_count']['max'] - 1) * args.loc['ms_count']['max']) / 2)

    ##### Action Space
    action_spaces = {"ms_affinity": get_space(_ms_partial_sum, 0, 2),
                     "ms_replica_cpu_requests_shares": get_space(args.loc['ms_count']['max'],
                                                                 0,
                                                                 args.loc['ms_replica_cpu_requests_shares']['chunks']),
                     "ms_replica_cpu_limits": get_space(args.loc['ms_count']['max'],
                                                        0,
                                                        args.loc['ms_replica_cpu_limits']['chunks']),
                     "ms_replica_count": get_space(args.loc['ms_count']['max'],
                                                   args.loc['ms_replica_count']['min'],
                                                   args.loc['ms_replica_count']['max'])}

    #### Observation Space
    # assuming all hosts have the same number of cores (homogeneous)
    obs_spaces = {"host_cpu_core_count": get_space(1, 1, args.loc['host_cpu_core_count']['chunks']),
                  "host_cpu_clock_rate": get_space(1, 1, args.loc["host_cpu_clock_rate"]["chunks"]),
                  "cfs_period_ns": get_space(1, 1, args.loc["cfs_period_ns"]["chunks"]),
                  "host_network_bandwidth": get_space(1, 1, args.loc['host_network_bandwidth']['chunks']),
                  "ms_replica_count": get_space(args.loc['ms_count']['max'], 0, args.loc['ms_replica_count']['max']),
                  "ms_replica_cpu_requests_shares": get_space(args.loc['ms_count']['max'],
                                                              0,
                                                              args.loc['ms_replica_cpu_requests_shares']['chunks']),
                  "ms_replica_cpu_limits": get_space(args.loc['ms_count']['max'],
                                                     0,
                                                     args.loc['ms_replica_cpu_limits']['chunks']),
                  "ms_replica_net_bandwidth": get_space(args.loc['ms_count']['max'],
                                                        0,
                                                        args.loc['ms_replica_reserved_network_bandwidth']['chunks']),
                  "ms_replica_average_cpu_usage": get_space(args.loc['ms_count']['max'],
                                                            0,
                                                            args.loc["ms_replica_average_cpu_usage"]["chunks"]),
                  "ms_replica_thread_instructions": get_space(args.loc['ms_count']['max'],
                                                              0,
                                                              args.loc[
                                                                  "ms_replica_thread_instructions"][
                                                                  "chunks"]),
                  "ms_replica_thread_avg_cpi": get_space(args.loc['ms_count']['max'],
                                                         0,
                                                         args.loc[
                                                             "ms_replica_thread_avg_cpi"][
                                                             "chunks"]),
                  "ms_replica_thread_count": get_space(args.loc['ms_count']['max'],
                                                       0,
                                                       args.loc['ms_replica_thread_count']['max']),
                  "ms_affinity_rules": get_space(_ms_partial_sum, 0, 2),
                  "sc_edge": get_space(args.loc['ms_count']['max'] - 1, 0, args.loc["sc_edge_bytes"]["chunks"]),
                  "arrival_rate": get_space(1, 0, args.loc["sc_arrival_rate"]["chunks"]),
                  "ms_replica_thread_average_cpu_utilization": get_space(1, 0, args.loc[
                      "ms_replica_thread_average_cpu_utilization"]["chunks"]),
                  }

    action_space = merge_spaces(action_spaces)
    observation_space = merge_spaces(obs_spaces)

    ### CPU Execution Time of an Application (per core) =
    # Instructions count x average cycle per instruction x clock cycle

    # MAX_HOST_CPU_CLOCK_CYCLE = 1 / args.loc['host_cpu_clock_rate']['max']
    # MIN_HOST_CPU_CLOCK_CYCLE = 1 / args.loc['host_cpu_clock_rate']['min']
    #
    # MAX_MS_THREAD_CPU_TIME = args.loc['ms_replica_thread_instructions']['max'] * \
    #                          args.loc['ms_replica_thread_avg_cpi']['max'] * \
    #                          MAX_HOST_CPU_CLOCK_CYCLE
    #
    # MIN_MS_THREAD_CPU_TIME = args.loc['ms_replica_thread_instructions']['min'] * \
    #                          args.loc['ms_replica_thread_avg_cpi']['min'] * \
    #                          MIN_HOST_CPU_CLOCK_CYCLE

    @staticmethod
    def get_random_chunk(index, min_value=None):
        _len = len(Settings.chunks[index])
        if _len > 0:
            if min_value is None:
                return np.random.choice(Settings.chunks[index])
            elif _len == 1:
                if Settings.chunks[index][0] >= min_value:
                    return Settings.chunks[index][0]
            else:
                first_index_greater_than_min_value = (min_value - Settings.chunks[index][0]) \
                                                     / \
                                                     (Settings.chunks[index][1] - Settings.chunks[index][0])
                if first_index_greater_than_min_value >= 0:
                    first_index_greater_than_min_value = int(np.ceil(first_index_greater_than_min_value))
                    portion_greater_than_min_value = Settings.chunks[index][first_index_greater_than_min_value:]
                    # print(Settings.chunks[index])
                    # print("*********")
                    # print(str(portion_greater_than_min_value) + " - min_value=" + str(min_value) + "first_index=" + str(first_index_greater_than_min_value))
                    # print("_____")
                    return np.random.choice(portion_greater_than_min_value)

        raise Exception("Error: no chunk has been found")
