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

#
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from prettytable import PrettyTable
from tabulate import tabulate

if TYPE_CHECKING:
    from perfsim import Simulation, ServiceChainManager


class Logger:
    """
    This class represents a logger that logs the simulation events.
    """

    lb_timer = []
    tick_timer = []
    core_sorting_timer = []
    sim: Simulation

    def __init__(self, simulation: Simulation = None):
        # self.latencies = []
        # self.arrivals = []
        self.sim = simulation
        # self.average_compute_times = np.zeros(len(self.sim.load_generator.sim.cluster.microservices_dict))
        # self.average_transmission_times = np.zeros(self.sim.load_generator.sim.cluster.count_total_service_edges())
        if self.sim.debug_file_location is not None and self.sim.debug_file_location is not False:
            os.remove(self.sim.debug_file_location)

    def _print_log(self, log_str: str, end: str = None):
        if self.sim.debug_file_location is None or self.sim.debug_file_location is False:
            if end is not None:
                print(log_str, end=end)
            else:
                print(log_str)
        else:
            original_stdout = sys.stdout  # Save a reference to the original standard output

            with open(self.sim.debug_file_location, 'a') as f:
                sys.stdout = f  # Change the standard output to the file we created.
                if end is not None:
                    print(log_str, end=end)
                else:
                    print(log_str)
                sys.stdout = original_stdout  # Reset the standard output to its original value

    def print_traffic_details(self):
        table = PrettyTable(
            ["Traffic Generator Name/SCM ID", "Duration", "Arrival Delta T", "Start at", "Batch size",
             "Total requests"])

        self._print_log("\nTraffic Prototypes\n")
        for traffic_prototype in self.sim.traffic_prototypes_dict.values():
            row = [str(traffic_prototype.name),
                   str(traffic_prototype.duration),
                   str(traffic_prototype.arrival_interval_ns),
                   str(traffic_prototype.start_at),
                   str(traffic_prototype.parallel_user),
                   str(traffic_prototype.requests_count)]
            table.add_row(row)

        self._print_log(log_str=str(table))

    def print_hosts_info(self):
        hosts_table = PrettyTable(["Host Name", "Clock Rate", "Cores"])

        self._print_log("\nHosts\n")
        for h in self.sim.cluster.cluster_scheduler.hosts_dict.values():
            hosts_table.add_row([str(h.name), str(h.cpu.clock_rate), str(len(h.cpu.cores))])
        self._print_log(str(hosts_table))

    def print_microservices_info(self):
        self._print_log("\nMicroservices\n")
        table = PrettyTable(["MS Name", "CPU Requests", "CPU Limits", "Replica Name", "Host", "Endpoint Function ID",
                             "Thread ID", "Instructions", "CPI", "Misses", "Refs", "Penalty"])

        for scm in self.sim.cluster.scm_dict.values():
            row = []
            for ms in scm.service_chain.microservices_dict.values():
                row.append(ms.name)
                row.append(ms.cpu_requests)
                row.append(ms.cpu_limits)

                for replica in ms.replicas:
                    row.append(replica.name)
                    row.append(replica.host.name) if replica.host is not None else row.append("None")
                    for f in ms.endpoint_functions:
                        _f_data = ms.endpoint_functions[f]
                        row.append(_f_data.name)

                        for t in np.arange(ms.endpoint_functions[f].threads_count):
                            row.append(str(t))
                            row.append(_f_data.threads_instructions[t])
                            row.append(str(_f_data.threads_avg_cpi[t]))
                            row.append(str(_f_data.threads_single_core_isolated_cache_misses[t]))
                            row.append(str(_f_data.threads_single_core_isolated_cache_refs[t]))
                            row.append(str(_f_data.threads_avg_cache_miss_penalty[t]))
                            table.add_row(row)
                            row = ['', '', '', '', '', '']

                        row = ['', '', '', '', '']

                    row = ['', '', '']

                row = []

        self._print_log(str(table))

    def print_cluster_info(self):
        self._print_log(log_str=self.sim.cluster.cluster_scheduler.placement_matrix.to_string())
        self.print_hosts_info()
        self.print_microservices_info()

    def print_subchains(self, scm: ServiceChainManager):
        self._print_log(log_str="----------------------")
        self._print_log(log_str="Subchains of scm #" + str(scm.name))

        for subchain_id, subchain in enumerate(scm.subchains):
            self._print_log(log_str="Subchain #" + str(subchain_id) + ": ", end='')
            for node in subchain:
                self._print_log(log_str="(" + str(node[0]) + "," + str(node[1]) + ") ", end="")
            self._print_log(log_str="")

        self._print_log(log_str="----------------------")
        self._print_log(log_str="")

    def print_all(self):
        self.print_cluster_info()
        self.print_traffic_details()
        for scm_name, scm in enumerate(self.sim.cluster.scm_dict.values()):
            self.print_subchains(scm=scm)

    def log(self, msg: str, level: int = 1):
        if self.sim.debug and self.sim.debug_level >= level:
            self._print_log(log_str=str(self.sim.time) + ": " + msg)

    def print_latencies(self, summary=False, detailed=True):
        if detailed:
            self._print_log(log_str=tabulate(self.sim.load_generator.latencies, headers="keys", tablefmt="psql"))

        if summary:
            self._print_log(log_str=tabulate(self.get_latencies_summary(), headers="keys", tablefmt="psql"))

    def get_latencies_summary(self):
        summary = pd.DataFrame(columns=["avg. latency", "max latency", "min latency"])
        summary.loc[0] = {"avg. latency": int(self.sim.load_generator.latencies["latency"].mean()),
                          "max latency": int(self.sim.load_generator.latencies["latency"].max()),
                          "min latency": int(self.sim.load_generator.latencies["latency"].min())}
        return summary

    # def calculate_average_computation_times(self) -> None:
    #     if self.total_batch_requests_count != 0:
    #         for request in self.requests:
    #             for ms_id in np.arange(self.cluster.service_chain.chain_count):
    #                 self.average_compute_times[ms_id] += request.compute_times[ms_id]
    #
    #                 if ms_id < self.cluster.service_chain.chain_count - 1:
    #                     self.average_transmission_times[ms_id] += request.transmission_times[ms_id]
    #
    #         self.average_compute_times = self.average_compute_times / len(self.requests)
    #         self.average_transmission_times = self.average_transmission_times / len(self.requests)
