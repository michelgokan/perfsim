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

import math
import os
import time as tt
from copy import deepcopy
from typing import TYPE_CHECKING, List, Dict, Union, Set

import numpy as np
import pandas as pd
import plotly.express as px
from sortedcontainers import SortedDict, SortedSet

from perfsim import Logger, Core, RunQueue, Observable, CPULogObserver, Utils, Plotter, ReplicaThread

if TYPE_CHECKING:
    from perfsim import Host

"""
A *CPU* object represents a single NUMA node with a given *clock_rate* and *name*
in the system. Each NUMA node contains a number of cores represented by the 
*cores_count*. 

Here are the possible initialization parameters:

        `name`
            Name of the CPU. i.e. *CPU1*

        `cores_count`
            Number of cores that this CPU contains.

        `cpu_clock_rate`
            The maximum clock rate of this CPU for this host (in Hertz).

There are also other parameters that one can access after initialization:        
        `cores`
            Return a list of cores in a *Cpu*
            
"""


class CPU(Observable):
    """
    The CPU class represents a single NUMA node in the system. It contains a number
    of cores and has a clock rate. It is responsible for load balancing among the
    cores and the threads that are assigned to them.
    """

    #: The list of cores in this CPU
    cores: List[Core]

    #: sched_domain_hierarchy similar to the Linux kernel
    sched_domain_hierarchy = ["core pairs", "node"]

    #: The clock rate of the CPU in Hertz
    _clock_rate: int

    #: The clock rate of the CPU in nanohertz
    _clock_rate_in_nanohertz: float

    #: The host that this CPU belongs to
    host: Host

    #: Sorted dictionary of all threads (by load) belongs to this CPU (not reliable, only for emergency load balancing)
    threads_sorted: SortedDict[int, SortedDict[float, set[ReplicaThread]]]

    #: Sorted dictionary of all pairs (by load) belongs to this CPU (not reliable, only for load balancing)
    pairs_sorted: SortedDict[int, Set[int]]

    #: Stores the id of cores in pairs that are idle (the key is pair_id in CPU and values are idle cores)
    idle_core_pair_ids: Dict[int, SortedSet[int]]

    #: Stores the id of idle pairs (sorted by the pair id)
    idle_pair_ids: SortedSet[int]

    #: Stores the id of idle cores (sorted by the core id)
    idle_core_ids: SortedSet[int]

    #: Stores the load of each pair (sorted by the load)
    pairs_load: List[int]

    def __init__(self, name: str, cores_count: int, clock_rate: int, host: Host):
        self.name = name
        self.clock_rate = clock_rate  # in hertz
        self.cores = []
        self.host = host
        self.max_cpu_requests = 1000
        self.events = {0: {key: 0 for (key, value) in enumerate(np.arange(0, cores_count))}}
        self.thread_events = {0: {key: 0 for (key, value) in enumerate(np.arange(0, cores_count))}}
        self.threads_sorted = SortedDict()
        self.pairs_sorted = SortedDict()
        self.idle_core_pair_ids = {}
        self.idle_pair_ids = SortedSet()
        self.idle_core_ids = SortedSet()
        self.pairs_load = []

        for core_id in np.arange(0, cores_count):
            self.cores.append(Core(cpu=self, core_id=self.name + "_core" + str(core_id), core_id_in_cpu=core_id))
            self.idle_pair_ids.add(self.cores[core_id].pair_id)
            self.idle_core_ids.add(core_id)

            if self.cores[core_id].pair_id not in self.idle_core_pair_ids:
                self.idle_core_pair_ids[self.cores[core_id].pair_id] = SortedSet([core_id])
                self.pairs_load.append(0)
            else:
                self.idle_core_pair_ids[self.cores[core_id].pair_id].add(core_id)

        self.sched_domains = {}
        self.sched_domains = self.get_sched_domains()
        self.sched_groups = []

        super().__init__()
        if host.cluster is not None and host.cluster.sim.debug:
            self.attach_observer(CPULogObserver(cpu=self))

        # _core_rq_exec_order = SortedList(core_rqs[0])
        # _core_rq_exec_order = 0

    def reinit(self):
        """
        Reinitialize the CPU

        :return:
        """

        self.__init__(name=self.name, cores_count=len(self.cores), clock_rate=self.clock_rate, host=self.host)

    def register_events(self):
        pass

    def get_available(self) -> int:
        """
        Returns available cores in the *CPU*

        :return: Returns available cores in the *CPU*
        :rtype: int
        """

        available = 0

        for core in self.cores:
            available += core.get_available()

        return available

    @property
    def capacity(self):
        """
        Returns the total capacity of the *CPU* in terms of CPU requests (each core is 1000 milicores).

        :return:
        """

        capacity = 0

        for core in self.cores:
            capacity += core.capacity

        return capacity

    def is_there_enough_resources_to_reserve(self, amount: int) -> bool:
        """
        Check if there are enough resources to reserve *amount* of CPU in the *CPU*.

        :param amount:
        :return:
        """

        if self.get_available() >= amount:
            return True
        else:
            return False

    def reserve(self, amount: int) -> None:
        """
        Uniformly reserve a given *amount* of CPU within all the *cores* in the
        *CPU*.

        :param amount:
        """

        cpu_requests_per_core = round(amount / len(self.cores))

        for core in self.cores:
            core.reserve(amount=cpu_requests_per_core)

    def release(self, amount: int) -> None:
        """
        Uniformly release a given *amount* of CPU within all the *cores* in the
        *CPU*.

        :param amount:
        :return:
        """

        cpu_requests_per_core = round(amount / len(self.cores))

        for core in self.cores:
            core.release(amount=cpu_requests_per_core)

    def _get_clock_rate_in_nanohertz(self) -> float:
        """
        Returns the clock rate of the CPU in nanohertz

        :return:
        """

        return self.clock_rate / 10 ** 9

    def get_idle_core_in_sd(self, sd_name: str, sd: List, numa_node_id: int, current_core_in_sd: Core) -> int:
        """
        Get the idle core in the given sched domain

        :param sd_name:
        :param sd:
        :param numa_node_id:
        :param current_core_in_sd:
        :return:
        """

        if len(sd) != 0 and len(sd[numa_node_id]) != 0:
            if sd_name == CPU.sched_domain_hierarchy[0]:
                the_other_core_id_in_pair = self.get_the_other_core_in_pair(core_id=current_core_in_sd.id_in_cpu,
                                                                            return_same_if_not_exists=True)
                if the_other_core_id_in_pair in self.idle_core_pair_ids[current_core_in_sd.pair_id]:
                    return the_other_core_id_in_pair
                elif current_core_in_sd.id_in_cpu in self.idle_core_ids:
                    return current_core_in_sd.id_in_cpu
            elif sd_name == CPU.sched_domain_hierarchy[1]:
                if len(self.idle_pair_ids) != 0:
                    _next_idle_pair_id = next(iter(self.idle_pair_ids))
                    next_idle_core_id = self.idle_core_pair_ids[_next_idle_pair_id][0]
                    return next_idle_core_id
            return -1
        else:
            return 0

    def get_the_other_core_in_pair(self, core_id: int, return_same_if_not_exists: bool = False) -> Union[None, int]:
        """
        Get the other core in the pair

        :param core_id:
        :param return_same_if_not_exists:
        :return:
        """

        if core_id % 2 == 0:
            # TODO: If in the future, we want to support more than one NUMA node, we need to change this
            if len(self.sched_domains['core pairs'][0][int(core_id / 2)]) == 1:
                # There is only one core in the pair
                return core_id if return_same_if_not_exists else None
            else:
                return core_id + 1
        else:
            return core_id - 1

    def get_core_pairs(self) -> List[List[int]]:
        """
        Get the core pairs

        :return:
        """

        numa_node_id = 0
        pairs_range = range(int(len(self.cores) + 1 / 2))
        pairs = []

        for core_id in range(len(self.cores)):
            if core_id % 2 == 0:
                pairs.append([core_id])
            else:
                pairs[math.ceil(core_id / 2) - 1].append(core_id)

        return pairs

    def get_sched_domains(self) -> Dict:
        """
        Get the sched domains

        :return:
        """

        numa_node_id = 0
        self.sched_domains[self.sched_domain_hierarchy[0]] = []
        self.sched_domains[self.sched_domain_hierarchy[0]].append(numa_node_id)  # assume we have 1 CPU socket per host
        self.sched_domains[self.sched_domain_hierarchy[0]][numa_node_id] = self.get_core_pairs()

        self.sched_domains[self.sched_domain_hierarchy[1]] = []
        self.sched_domains[self.sched_domain_hierarchy[1]].append(
            self.sched_domains[self.sched_domain_hierarchy[0]][numa_node_id])

        return self.sched_domains

    def get_busiest_core_in_pair_by_core_id(self, core_id) -> Union['Core', None]:
        """
        Get the busiest core in the pair

        :param core_id:
        :return:
        """

        the_other_core_id_in_cur_pair = self.get_the_other_core_in_pair(core_id=core_id)
        if the_other_core_id_in_cur_pair is None:
            return self.cores[core_id]

        busiest_core = None
        if self.cores[core_id].runqueue.load > self.cores[the_other_core_id_in_cur_pair].runqueue.load:
            busiest_core = self.cores[core_id]
        elif self.cores[core_id].runqueue.load < self.cores[the_other_core_id_in_cur_pair].runqueue.load:
            busiest_core = self.cores[the_other_core_id_in_cur_pair]
        elif len(self.cores[core_id].runqueue.active_threads) >= \
                len(self.cores[the_other_core_id_in_cur_pair].runqueue.active_threads):
            busiest_core = self.cores[core_id]
        else:
            busiest_core = self.cores[the_other_core_id_in_cur_pair]

        return busiest_core

    def get_busiest_core_in_pair(self, pair_id) -> Union['Core', None]:
        """
        Get the busiest core in the pair

        :param pair_id:
        :return:
        """

        return self.get_busiest_core_in_pair_by_core_id(core_id=pair_id * 2)

    def get_busiest_core_in_busiest_pair(self, current_pair_id, numa_node_id: int = 0) -> Union['Core', None]:
        """
        Get the busiest core in the busiest pair

        :param current_pair_id:
        :param numa_node_id:
        :return:
        """

        if len(self.pairs_sorted) > 0:
            _busiest_pair_inverted_load = next(iter(self.pairs_sorted))
            _busiest_pair_load = _busiest_pair_inverted_load * -1

            if self.pairs_load[current_pair_id] > _busiest_pair_load:
                raise Exception("How come the busiest pair (load = " + str(self.pairs_load[current_pair_id]) +
                                ") is lighter than the current pair (load = " + str(_busiest_pair_inverted_load) + ")?")
            elif self.pairs_load[current_pair_id] == _busiest_pair_load:
                return None

            _busiest_pairs_iter = iter(self.pairs_sorted[_busiest_pair_inverted_load])
            _next_busiest_pair = next(_busiest_pairs_iter)

            if _next_busiest_pair == current_pair_id and len(self.pairs_sorted[_busiest_pair_inverted_load]) > 1:
                _next_busiest_pair = next(_busiest_pairs_iter)

            busiest_core_in_pair = self.get_busiest_core_in_pair(_next_busiest_pair)
            return busiest_core_in_pair if busiest_core_in_pair is not None else self.cores[_next_busiest_pair * 2]

        return None

    def load_balance_threads_among_runqueues(self) -> List[List[RunQueue]]:
        """
        Load balance threads among runqueues

        :return:
        """

        time1 = tt.time()
        numa_node_id = 0

        break_flag = 0

        for core_id in range(len(self.cores)):
            for sd_name in self.sched_domains:
                idle_core = self.get_idle_core_in_sd(sd_name=sd_name,
                                                     sd=self.sched_domains[sd_name],
                                                     numa_node_id=numa_node_id,
                                                     current_core_in_sd=self.cores[core_id])

                if idle_core != -1:
                    if core_id != idle_core:
                        continue

                break_flag = 0
                while break_flag == 0:
                    busiest_core = None

                    if sd_name == CPU.sched_domain_hierarchy[0]:
                        busiest_core = self.get_busiest_core_in_pair_by_core_id(core_id=core_id)
                    elif sd_name == CPU.sched_domain_hierarchy[1]:
                        busiest_core = \
                            self.get_busiest_core_in_busiest_pair(current_pair_id=self.cores[core_id].pair_id,
                                                                  numa_node_id=numa_node_id)

                    if busiest_core is None:
                        break_flag = 1
                        break

                    if sd_name == CPU.sched_domain_hierarchy[0]:
                        if len(busiest_core.runqueue.active_threads) <= 1:
                            break_flag = 1
                            break

                        lightest_thread_load_in_busiest_core = next(iter(busiest_core.runqueue.lightest_threads_in_rq))
                        local_new_load = self.cores[core_id].runqueue.load + lightest_thread_load_in_busiest_core
                        busiest_new_load = busiest_core.runqueue.load - lightest_thread_load_in_busiest_core

                        if round(busiest_new_load, 5) >= round(local_new_load, 5) and \
                                len(busiest_core.runqueue.active_threads) > 1:
                            lightest_threads_set = \
                                busiest_core.runqueue.lightest_threads_in_rq[lightest_thread_load_in_busiest_core]
                            lightest_thread_vruntime_in_busiest_core = next(iter(lightest_threads_set))
                            lightest_thread_in_busiest_core = next(iter(
                                lightest_threads_set[lightest_thread_vruntime_in_busiest_core]))
                            busiest_core.runqueue.dequeue_task_by_thread(thread=lightest_thread_in_busiest_core)
                            self.cores[core_id].runqueue.enqueue_task(thread=lightest_thread_in_busiest_core)
                        else:
                            break
                    elif sd_name == CPU.sched_domain_hierarchy[1]:
                        the_other_core_id_in_busiest_pair = self.get_the_other_core_in_pair(
                            core_id=busiest_core.id_in_cpu)
                        if the_other_core_id_in_busiest_pair is not None:
                            number_of_cores_in_busiest_pair = 2
                            the_other_core_in_busiest_pair = self.cores[the_other_core_id_in_busiest_pair]
                            total_number_of_threads_in_busiest_pair = \
                                len(self.cores[busiest_core.id_in_cpu].runqueue.active_threads) + \
                                len(the_other_core_in_busiest_pair.runqueue.active_threads)
                        else:
                            number_of_cores_in_busiest_pair = 1
                            total_number_of_threads_in_busiest_pair = \
                                len(self.cores[busiest_core.id_in_cpu].runqueue.active_threads)

                        if total_number_of_threads_in_busiest_pair <= 1:
                            break_flag = 1
                            break

                        for counter in np.arange(number_of_cores_in_busiest_pair):
                            if counter != 0:
                                busiest_core_id = the_other_core_id_in_busiest_pair
                                if len(self.cores[busiest_core_id].runqueue.active_threads) == 0:
                                    break_flag = 1
                                    break  # --> break mikonim chon nemishe chizi kand az busiest pair
                            else:
                                busiest_core_id = busiest_core.id_in_cpu

                            lightest_thread_load_in_busiest_core = \
                                next(iter(self.cores[busiest_core_id].runqueue.lightest_threads_in_rq))
                            local_new_load = \
                                self.pairs_load[self.cores[core_id].pair_id] + lightest_thread_load_in_busiest_core
                            busiest_new_load = \
                                self.pairs_load[self.cores[busiest_core_id].pair_id] - \
                                lightest_thread_load_in_busiest_core

                            if round(busiest_new_load, 5) >= round(local_new_load, 5):
                                lightest_threads_set = self.cores[busiest_core_id].runqueue.lightest_threads_in_rq[
                                    lightest_thread_load_in_busiest_core]
                                lightest_thread_vruntime_in_busiest_core = next(iter(lightest_threads_set))
                                lightest_thread_in_busiest_core = next(iter(
                                    lightest_threads_set[lightest_thread_vruntime_in_busiest_core]))

                                self.cores[busiest_core_id].runqueue.dequeue_task_by_thread(
                                    thread=lightest_thread_in_busiest_core)
                                if lightest_thread_in_busiest_core.instructions <= 0:
                                    raise Exception("Are you kidding me?! How come this zombie made its way here?")
                                self.cores[core_id].runqueue.enqueue_task(thread=lightest_thread_in_busiest_core)
                                break
                            elif counter == 1:  # --> break mikonim chon nemishe chizi kand az busiest pair, bikhial sho
                                break_flag = 1
                                break

        _time2 = tt.time()
        Logger.lb_timer.append(_time2 - time1)
        self.host.cluster.cluster_scheduler.hosts_need_load_balancing.remove(self.host)
        self.host.load_balancing_needed = False

    def emergency_load_balance_idle_cores(self) -> None:
        """
        Emergency load balance idle cores

        :return:
        """

        time1 = tt.time()
        numa_node_id = 0

        cores_that_became_busy = set()
        for core_id in self.idle_core_ids:
            core = self.cores[core_id]
            heaviest_thread = None
            core_id_of_the_rq_containing_heaviest_load = -1

            break_flag = 0
            to_discard = set()
            for thread_load, thread_sorted_set in self.threads_sorted.items():
                for vruntime, thread_set in thread_sorted_set.items():
                    for _, thread in enumerate(thread_set):
                        if not thread.on_rq or thread.load <= 0 or thread.instructions <= 0:
                            to_discard.add((thread_load, thread))
                            continue
                        if (thread.core is not None and thread.core.id_in_cpu == core_id) or len(
                                thread.core.runqueue.rq) <= 1:
                            continue
                        heaviest_thread = thread
                        core_id_of_the_rq_containing_heaviest_load = thread.core.id_in_cpu
                        break_flag = 1
                        break
                    if break_flag == 1:
                        break

            for _, thread_load_tuple in enumerate(to_discard):
                self.remove_from_threads_sorted(thread=thread_load_tuple[1], inverted_thread_load=thread_load_tuple[0])

            if core_id_of_the_rq_containing_heaviest_load != -1:
                self.cores[core_id_of_the_rq_containing_heaviest_load].runqueue.dequeue_task_by_thread(
                    thread=heaviest_thread)
                self.cores[core_id].runqueue.enqueue_task(thread=heaviest_thread)

            # self.cores[core_id].runqueue.recalculate_cpu_requests_shares()

        time2 = tt.time()
        Logger.lb_timer.append(time2 - time1)

    def recalculate_cpu_requests_shares(self) -> None:
        """
        Recalculate CPU requests shares

        :return:
        """

        for core_id, core in enumerate(self.cores):
            core.runqueue.recalculate_cpu_requests_shares()

    def kill_zombie_threads(self) -> None:
        """
        Kill zombie threads

        :return:
        """

        transmission_time_recalculation_list = {}

        cores_killed_a_thread_in = set()
        for thread in self.host.cluster.cluster_scheduler.zombie_threads:
            if thread.instructions > 0:
                raise Exception("How is that even possible!?")

            cores_killed_a_thread_in.add(thread.core.id_in_cpu)
            thread.kill()
            if thread.parent_request is None:
                continue

            thread.parent_request.current_active_threads[thread.subchain_id] -= 1
            if thread.parent_request.current_active_threads[thread.subchain_id] == 0:
                calc_todo = thread.parent_request.init_transmission(node_in_alt_graph=thread.node_in_alt_graph)
                transmission_time_recalculation_list[thread.parent_request] = calc_todo
            elif thread.parent_request.current_active_threads[thread.subchain_id] < 0:
                raise Exception("What the hell is going on here? Number of active threads in subchain id #" +
                                str(thread.subchain_id) + " belonging to request " +
                                str(thread.parent_request.id) + " is less than zero !!!!")

        self.host.cluster.cluster_scheduler.zombie_threads = set()

        if len(transmission_time_recalculation_list) != 0:
            # TODO: do we really need to recalculate transmission bw on ALL LINKS? Isn't it enough to recalculate for a
            #  subset of links only?
            self.host.cluster.topology.recalculate_transmissions_bw_on_all_links()

    def plot(self, save_dir: str = None, show: bool = True):
        """
        Plot the CPU requests share and threads count on run queues

        :param save_dir:
        :param show:
        :return:
        """

        share_events = {}
        thread_events = {}
        step = 1000000000  #: 1s
        _share_events = SortedDict(deepcopy(self.events))
        _threads_events = SortedDict(deepcopy(self.thread_events))
        timerange = np.arange(start=0, stop=self.host.cluster.sim.time + step, step=step, dtype=int)
        core_range = range(len(self.cores))

        df_share = pd.DataFrame.from_dict(_share_events).transpose()
        df_threads = pd.DataFrame.from_dict(_threads_events).transpose()

        for _, time_range in enumerate(timerange):
            if time_range not in _share_events:
                get_last_share = df_share[df_share.index < time_range].iloc[-1]
                get_last_threads_count = df_threads[df_threads.index < time_range].iloc[-1]

                _share_events[time_range] = {}
                _threads_events[time_range] = {}

                for core in core_range:
                    _share_events[time_range][core] = get_last_share[core]
                    _threads_events[time_range][core] = get_last_threads_count[core]

        share_events_list = list(_share_events)
        share_events_list_items = list(_share_events.items())
        thread_events_list = list(_threads_events)
        thread_events_list_items = list(_threads_events.items())
        event_number = 0
        # step = 1000000  #: 1ms
        current_event_time = 0
        xaxis_nticks = 0
        yaxis_nticks = len(self.events[current_event_time].keys()) if current_event_time in self.events else 0

        for _, time_range in enumerate(timerange):
            xaxis_nticks += 1
            current_range_end = time_range + step

            while event_number + 1 < len(share_events_list) and share_events_list[event_number] < current_range_end:
                if time_range not in share_events.keys():
                    share_events[time_range] = {core_id: 0 for core_id in core_range}
                    thread_events[time_range] = {core_id: 0 for core_id in core_range}

                time_weight = (share_events_list[event_number + 1] - share_events_list[event_number]) / step

                for core in core_range:
                    share_events[time_range][core] += share_events_list_items[event_number][1][core] * time_weight
                    thread_events[time_range][core] += thread_events_list_items[event_number][1][core] * time_weight

                event_number += 1

        a = [[] for _ in range(len(self.cores))]
        b = [[] for _ in range(len(self.cores))]

        step_id = 0
        for timestamp, value1 in share_events.items():
            for core_id, value2 in value1.items():
                if len(a[core_id]) < step_id + 1:
                    a[core_id].append(int(value2))
                else:
                    a[core_id][step_id] = int(value2)
            step_id += 1

        step_id = 0
        for timestamp, value1 in thread_events.items():
            for core_id, value2 in value1.items():
                if len(b[core_id]) < step_id + 1:
                    b[core_id].append(value2)
                else:
                    b[core_id][step_id] = value2
            step_id += 1

        fig_share = px.imshow(a, labels=dict(x="Time (in secs)", y="Core ID", color="Average CPU Requests Share"),
                              aspect="auto")
        fig_threads = px.imshow(b, labels=dict(x="Time (in secs)", y="Core ID", color="Threads count"), aspect="auto")

        fig_share.update_layout(title='Average cpu_requests_share load on run queues for host ' + self.host.name,
                                xaxis_nticks=xaxis_nticks,
                                yaxis_nticks=yaxis_nticks,
                                xaxis=dict(tickmode='array', tickvals=list(range(xaxis_nticks))),
                                yaxis=dict(tickmode='array', tickvals=list(range(yaxis_nticks))))

        fig_threads.update_layout(title='Average threads count on run queues for host ' + self.host.name,
                                  xaxis_nticks=xaxis_nticks,
                                  yaxis_nticks=yaxis_nticks,
                                  xaxis=dict(tickmode='array', tickvals=list(range(xaxis_nticks))),
                                  yaxis=dict(tickmode='array', tickvals=list(range(yaxis_nticks))))

        if show:
            fig_share.show()
            fig_threads.show()
        if save_dir is not None:
            try:
                Utils.mkdir_p(save_dir)
                file_name1 = f"{str(self.host.name)}-threads-lb-cpu_requests_share.html"
                file_name2 = f"{str(self.host.name)}-threads-lb-threads.html"
                file_path1 = os.path.join(save_dir, file_name1)
                file_path2 = os.path.join(save_dir, file_name2)
                file_path3 = os.path.join(save_dir, f"{str(self.host.name)}-dashboard.html")
                fig_share.write_html(file_path1)
                fig_threads.write_html(file_path2)
                Plotter.figures_to_html(figs=[(file_name1, fig_share), (file_name2, fig_threads)], filename=file_path3)
            except FileExistsError:
                pass

        return [fig_share, fig_threads]

    def __update_events(self):
        _time = self.host.cluster.sim.time
        self.events[_time] = {}
        self.thread_events[_time] = {}

        for core_id in np.arange(0, len(self.cores)):
            nr = 0
            self.events[_time][core_id] = self.cores[core_id].runqueue.load
            self.thread_events[_time][core_id] = len(self.cores[core_id].runqueue.active_threads)

    def load_balance(self) -> None:
        """
        Load balance the CPU by balancing the threads among the runqueues
        :return:
        """

        self.kill_zombie_threads()
        if self.host.load_balancing_needed and self.host.is_active():
            self.load_balance_threads_among_runqueues()
            self.emergency_load_balance_idle_cores()
        self.recalculate_cpu_requests_shares()
        if self.host.cluster.sim.log_cpu_events:
            self.__update_events()

    def add_to_pairs_sorted(self, pair_id, inverted_pair_load):
        """
        Add to pairs sorted dictionary
        :param pair_id:
        :param inverted_pair_load:
        :return:
        """

        if inverted_pair_load in self.pairs_sorted:
            self.pairs_sorted[inverted_pair_load].add(pair_id)
        else:
            self.pairs_sorted[inverted_pair_load] = {pair_id}

    def add_to_threads_sorted(self, thread: ReplicaThread, inverted_thread_load: int = None):
        """
        Add to threads sorted dictionary
        :param thread:
        :param inverted_thread_load:
        :return:
        """

        if inverted_thread_load is None:
            inverted_thread_load = thread.load * -1
        if inverted_thread_load in self.threads_sorted:
            if thread.vruntime in self.threads_sorted[inverted_thread_load]:
                self.threads_sorted[inverted_thread_load][thread.vruntime].add(thread)
            else:
                self.threads_sorted[inverted_thread_load][thread.vruntime] = {thread}
        else:
            self.threads_sorted[inverted_thread_load] = SortedDict({thread.vruntime: {thread}})

        thread.core.runqueue.add_to_lightest_threads_in_rq(thread=thread)

    def remove_from_pairs_sorted(self, pair_id, inverted_pair_load):
        """
        Remove from pairs sorted dictionary

        :param pair_id:
        :param inverted_pair_load:
        :return:
        """

        if inverted_pair_load in self.pairs_sorted:
            self.pairs_sorted[inverted_pair_load].discard(pair_id)
            if len(self.pairs_sorted[inverted_pair_load]) == 0:
                del self.pairs_sorted[inverted_pair_load]

    def remove_from_threads_sorted(self, thread: ReplicaThread, inverted_thread_load: int = None):
        """
        Remove from threads sorted dictionary

        :param thread:
        :param inverted_thread_load:
        :return:
        """

        if inverted_thread_load is None:
            inverted_thread_load = thread.load * -1
        if inverted_thread_load in self.threads_sorted:
            if thread.vruntime in self.threads_sorted[inverted_thread_load]:
                self.threads_sorted[inverted_thread_load][thread.vruntime].discard(thread)
                if len(self.threads_sorted[inverted_thread_load][thread.vruntime]) == 0:
                    del self.threads_sorted[inverted_thread_load][thread.vruntime]
                    if len(self.threads_sorted[inverted_thread_load]) == 0:
                        del self.threads_sorted[inverted_thread_load]
                if thread.core is not None:
                    thread.core.runqueue.remove_from_lightest_threads_in_rq(thread=thread)
            else:
                raise ValueError(f"Thread {thread} is not in threads_sorted[" + str(thread.vruntime) + "] " +
                                 "(perhaps vruntime was changed without updating threads_sorted?)")
        else:
            raise ValueError(f"Thread {thread} is not in threads_sorted")

    def update_idle_pairs(self, core):
        """
        Update idle pairs in the CPU by checking the load of the cores in the pair

        :param core:
        :return:
        """

        other_core_id_in_pair = self.get_the_other_core_in_pair(core_id=core.id_in_cpu)
        if other_core_id_in_pair is not None:
            other_core_in_pair = self.cores[other_core_id_in_pair]
            total_active_threads_in_pair = \
                len(core.runqueue.active_threads) + \
                (len(other_core_in_pair.runqueue.active_threads) if other_core_in_pair is not None else 0)
        else:
            total_active_threads_in_pair = len(core.runqueue.active_threads)

        if total_active_threads_in_pair > 0:
            self.idle_core_pair_ids[core.pair_id].discard(core.id_in_cpu)
            if len(self.idle_core_pair_ids[core.pair_id]) != 2:
                self.idle_pair_ids.discard(core.pair_id)
        else:
            self.idle_core_pair_ids[core.pair_id].add(core.id_in_cpu)
            self.idle_pair_ids.add(core.pair_id)

        if len(core.runqueue.active_threads) == 0:
            self.idle_core_ids.add(core.id_in_cpu)
        else:
            self.idle_core_ids.discard(core.id_in_cpu)

    @property
    def clock_rate(self) -> int:
        """
        Get the clock rate of the CPU in Hertz
        :return:
        """

        return self._clock_rate

    @clock_rate.setter
    def clock_rate(self, value):
        """
        Set the clock rate of the CPU in Hertz and update the clock rate in nanohertz

        :param value:
        :return:
        """
        self._clock_rate = value
        self._clock_rate_in_nanohertz = self._get_clock_rate_in_nanohertz()

    @property
    def clock_rate_in_nanohertz(self) -> float:
        """
        Get the clock rate of the CPU in nanohertz

        :return:
        """

        return self._clock_rate_in_nanohertz

    @clock_rate_in_nanohertz.setter
    def clock_rate_in_nanohertz(self, value):
        """
        Set the clock rate of the CPU in nanohertz

        :param value:
        :return:
        """

        raise ValueError("clock_rate_in_nanohertz is read-only! Set clock_rate instead.")

    def __str__(self):
        """
        String representation of the CPU

        :return:
        """

        return self.name
