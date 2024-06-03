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
from typing import TYPE_CHECKING, Tuple, Union

from perfsim import Observable, ReplicaThreadLogObserver, ReplicaThreadTimelineObserver

if TYPE_CHECKING:
    from perfsim import MicroserviceReplica, Process, Core, Request, MicroserviceEndpointFunction


class ReplicaThread(Observable):
    """
    This class represents a thread of execution of a microservice replica.
    """
    #: The event that is going to be notified before killing a thread.
    before_killing_thread: str

    #: The event that is going to be notified before executing a thread.
    before_executing_thread: str

    #: The event that is going to be notified after executing a thread.
    after_executing_thread: str

    #: Indicates whether the thread is on a core's runqueue or not.
    _on_rq: bool

    #: The process that the thread belongs to.
    _process: Process

    #: The vruntime represents the virtual runtime of the thread (as in the Linux scheduler).
    _vruntime: float

    #: Thread's load.
    _load: int

    #: Replica that the thread belongs to.
    replica: MicroserviceReplica

    #: Replica's identifier in the subchain.
    replica_identifier_in_subchain: int

    #: Thread's cpu_requests_share.
    _cpu_requests_share: int

    #: Thread's cpu_limits.
    _cpu_limits: int

    #: The current core that the thread is running on.
    _core: Core

    #: The index id of the thread in the node of the alternative graph.
    _thread_id_in_node: int

    #: The node in the alternative graph that this thread belongs to.
    _node_in_alt_graph: Tuple[int, MicroserviceEndpointFunction]

    __in_best_effort_active_threads: bool
    __in_burstable_active_threads: bool
    __in_guaranteed_active_threads: bool

    def __init__(self,
                 process: Process,
                 replica: MicroserviceReplica,
                 replica_identifier_in_subchain: int,
                 node_in_alt_graph: Tuple[int, MicroserviceEndpointFunction],
                 thread_id_in_node: int,
                 subchain_id: int,
                 average_load: float = 1,
                 core: Core = None,
                 parent_request: Request = None):
        self._process = process
        # self._process_backup = process

        self.id = str(replica.host.cluster.sim.time) + "_" + parent_request.id + "_" + \
                  str(parent_request.iteration_id) + "_" + str(subchain_id) + "_" + process.pname + "_" + \
                  str(len(self.process.threads))
        # self.__hash = int.from_bytes(self.id.encode(), byteorder='big')

        # TODO: Is this really needed?!
        self.process.threads.add(self)

        self._load = 0
        self.average_load = average_load
        self._cpu_requests_share = 0
        self._cpu_limits = 0
        self.period = 0
        self.request = 0
        self._core = core
        self.vruntime = 0
        self._on_rq = True
        self.executed_instructions = 0
        # self.cache_penalty = 0
        self.__in_best_effort_active_threads = False
        self.__in_burstable_active_threads = False
        self.__in_guaranteed_active_threads = False
        self.__in_burstable_unlimited_active_threads = False
        self.__in_burstable_limited_active_threads = False

        # self.total_runtime = 0
        self.is_idle = 0
        self.replica = replica
        self.replica_identifier_in_subchain = replica_identifier_in_subchain
        self.set_node_in_alt_graph(node=node_in_alt_graph, thread_id_in_node=thread_id_in_node)
        self.duration_to_finish = -1
        self.parent_request = parent_request
        self.subchain_id = subchain_id
        self.process.active_threads_count += 1
        self.parent_request.current_active_threads[self.subchain_id] += 1

        super().__init__()
        if self.replica.host.cluster.sim.debug_level > 0:
            self.attach_observer(ReplicaThreadLogObserver(replica_thread=self))
        if self.replica.host.cluster.sim.log_timeline:
            self.attach_observer(ReplicaThreadTimelineObserver(replica_thread=self))

    @property
    def node_in_alt_graph(self) -> Tuple[int, MicroserviceEndpointFunction]:
        return self._node_in_alt_graph

    @node_in_alt_graph.setter
    def node_in_alt_graph(self, node: Tuple[int, MicroserviceEndpointFunction]):
        raise Exception("Cannot set node_in_alt_graph directly. Use set_node_in_alt_graph() instead.")

    @property
    def thread_id_in_node(self) -> int:
        return self._thread_id_in_node

    @thread_id_in_node.setter
    def thread_id_in_node(self, thread_id_in_node: int):
        raise Exception("Cannot set thread_id_in_node directly. Use set_node_in_alt_graph() instead.")

    def set_node_in_alt_graph(self, node: Tuple[int, MicroserviceEndpointFunction], thread_id_in_node: int):
        self._thread_id_in_node = thread_id_in_node
        self._node_in_alt_graph = node
        self._set_values_from_endpoint_function()

    def register_events(self):
        self.register_event("before_killing_thread")
        self.register_event("before_executing_thread")
        self.register_event("after_executing_thread")

    def kill(self) -> None:
        self.notify_observers(self.before_killing_thread)

        self.process.active_threads_count -= 1
        self.core.cpu.host.threads.remove(self)
        self.core.cpu.host.cluster.cluster_scheduler.active_threads.remove(self)

        if not self.core.cpu.host.is_active():
            self.core.cpu.host.cluster.cluster_scheduler.active_hosts.remove(self.core.cpu.host)
            self.core.cpu.host.load_balancing_needed = False
            try:
                self.core.cpu.host.cluster.cluster_scheduler.hosts_need_load_balancing.remove(self.core.cpu.host)
            except KeyError:
                pass
        else:
            self.core.cpu.host.load_balancing_needed = True
            self.core.cpu.host.cluster.cluster_scheduler.hosts_need_load_balancing.add(self.core.cpu.host)

        self.process.threads.remove(self)
        self.core.runqueue.dequeue_task_by_thread(thread=self)
        self.on_rq = False

        # We are already calculating cpu_requests_share in cpu.recalculate_share
        # for _thread in self.process.threads:
        #     if _thread.on_rq:
        #         _thread.cpu_requests_share = _thread.cpu_requests_share / self.process.active_threads_count
        #         a=1

        # self._process_backup = self.process
        self.process = None

    def __recalculate_cache_penalty(self, millicores: Union[float, int]):
        miss_rate = (self.replica_single_core_isolated_cache_misses / self.replica_single_core_isolated_cache_refs)
        contention_penalty = 0.033420389 * math.log(len(self.core.runqueue.active_threads)) + 0.003341528
        # altered_millicores = millicores if millicores >= 100 else 100
        # millicores = (share * self.core.cpu.max_cpu_requests) / 1000
        # |___> it supposed to (1000 * share) / max_cpu_requests
        cpu_size_penalty = -0.02509033 * math.log(millicores) + 0.17859156
        miss_rate += miss_rate * cpu_size_penalty
        miss_rate += miss_rate * contention_penalty

        return ((self.replica_memory_accesses / self.original_instructions) *
                miss_rate * self.replica_avg_cache_miss_penalty)

    def __get_share_proportion(self) -> float:
        millicores = self.get_relative_guaranteed_cpu_requests_share()
        cache_penalty = self.__recalculate_cache_penalty(millicores=millicores)
        # _share_considering_cache_miss = ((self.cpi + self.cache_penalty) * (_cpu_requests_share ** 2)) / \
        #                                     (self.cpi * self.core.cpu.max_cpu_requests)
        millicores_to_share = (1024 * millicores) / 1000
        share_considering_cache_miss = (self.cpi * millicores_to_share) / (self.cpi + cache_penalty)
        return share_considering_cache_miss / self.core.cpu.max_cpu_requests

    def is_runnable(self):
        return self.on_rq and self.instructions > 0 and self.core is not None

    def exec(self, duration: int, simultaneous_flag: bool = False) -> int:
        if not self.is_runnable():
            raise Exception("You can't execute a zombie thread and/or a thread without any instructions left!")

        # if not simultaneous_flag:
        #     self.total_runtime += duration
        # self.core.runqueue.time += duration

        relative_share_proportion = self.__get_share_proportion()
        instructions_to_consume = (duration * relative_share_proportion /
                                   (self.cpi * (1 / self.replica.host.cpu.clock_rate_in_nanohertz)))
        remaining_instructions = self.instructions - instructions_to_consume
        if -0.001 < remaining_instructions < 0.001:
            instructions_to_consume += remaining_instructions
        self.notify_observers(event_name=self.before_executing_thread,
                              simultaneous_flag=simultaneous_flag,
                              duration=duration,
                              instructions_to_consume=instructions_to_consume)
        self.instructions -= instructions_to_consume
        self.executed_instructions += instructions_to_consume
        self.vruntime += duration * relative_share_proportion
        self.notify_observers(event_name=self.after_executing_thread,
                              simultaneous_flag=simultaneous_flag,
                              duration=duration,
                              instructions_to_consume=instructions_to_consume,
                              relative_share_proportion=relative_share_proportion)
        return 1 if self.instructions == 0 else 0

    def get_best_effort_cpu_requests_share(self) -> int:
        if self.process.ms_replica.microservice.is_best_effort():
            return self.core.cpu.max_cpu_requests
        elif self.process.ms_replica.microservice.is_burstable():
            if self.cpu_limits != -1:
                return self.cpu_limits - self.cpu_requests_share
            else:
                return self.core.cpu.max_cpu_requests - self.cpu_requests_share
        elif self.process.ms_replica.microservice.is_guaranteed():
            return 0
        else:
            raise Exception("Unknown microservice type")

    def get_relative_guaranteed_cpu_requests_share(self) -> int:
        if self.cpu_limits != -1:
            my_actual_guaranteed_cpu_requests_share = self.cpu_requests_share
            if my_actual_guaranteed_cpu_requests_share > self.core.cpu.max_cpu_requests:
                return self.core.cpu.max_cpu_requests
            else:
                return my_actual_guaranteed_cpu_requests_share
        else:  # if thread is best effort
            if self.cpu_requests_share == -1:
                raise Exception("I'm not sure this is an error, but thread supposed to get a cpu request before")
            else:
                return self.cpu_requests_share
            # v = (self.core.cpu.max_cpu_requests * my_actual_guaranteed_cpu_requests_share)
            # return v / self.core.runqueue.total_guaranteed_cpu_requests
            # best_effort_cpu_requests_share_proportion =
            # my_actual_guaranteed_cpu_requests_share / self.core.runqueue.total_guaranteed_cpu_requests
            # rq_free_share = self.core.cpu.max_cpu_requests - self.core.runqueue.total_guaranteed_cpu_requests
            # relative_share =
            # my_actual_guaranteed_cpu_requests_share + (best_effort_cpu_requests_share_proportion * rq_free_share)
            # return relative_share

    def get_exec_time_on_rq(self) -> float:
        relative_share_proportion = self.__get_share_proportion()
        self.duration_to_finish = (self.instructions * self.cpi) / \
                                  (self.replica.host.cpu.clock_rate_in_nanohertz * relative_share_proportion)
        return self.duration_to_finish

    @property
    def instructions(self):
        return self.__instructions

    @instructions.setter
    def instructions(self, v):
        self.__instructions = v

        if self.__instructions <= 0:
            self.core.cpu.host.cluster.cluster_scheduler.zombie_threads.add(self)

    @property
    def process(self):
        return self._process

    @process.setter
    def process(self, v: Process):
        self._process = v
        # if self._process is not None:
        #     self._process_backup = v

    # @property
    # def process_backup(self):
    #     return self._process_backup

    def __lt__(self, other):
        if isinstance(other, ReplicaThread):
            if self.load < other.load:
                return True
            else:
                return self.vruntime < other.vruntime

    def __gt__(self, other):
        if isinstance(other, ReplicaThread):
            if self.load > other.load:
                return True
            else:
                return self.vruntime > other.vruntime

    def __le__(self, other):
        if isinstance(other, ReplicaThread):
            if self.load <= other.load:
                return True
            else:
                return self.vruntime <= other.vruntime

    def __ge__(self, other):
        if isinstance(other, ReplicaThread):
            if self.load >= other.load:
                return True
            else:
                return self.vruntime >= other.vruntime

    # def __hash__(self):
    #     return self.__hash
    #
    # def __eq__(self, other):
    #     return self.__hash__() == other.__hash__()

    def __str__(self):
        return str(self.id)

    def _set_values_from_endpoint_function(self) -> ReplicaThread:
        func = self.node_in_alt_graph[1]
        thread_id = self.thread_id_in_node

        if func.microservice.cpu_requests != -1:
            self.cpu_requests_share = \
                min(self.replica.host.cpu.max_cpu_requests, func.microservice.cpu_requests / func.threads_count)
        else:
            self.cpu_requests_share = self.replica.host.cpu.max_cpu_requests / func.threads_count

        if func.microservice.cpu_limits != -1:
            self.cpu_limits = func.microservice.cpu_limits / func.threads_count
        else:
            self.cpu_limits = -1

        self.instructions = func.threads_instructions[thread_id]
        self.cpi = func.threads_avg_cpi[thread_id]
        self.replica_memory_accesses = func.threads_avg_mem_accesses[thread_id]
        self.original_instructions = func.threads_instructions[thread_id]
        self.replica_single_core_isolated_cache_misses = func.threads_single_core_isolated_cache_misses[thread_id]
        self.replica_single_core_isolated_cache_refs = func.threads_single_core_isolated_cache_refs[thread_id]
        self.replica_avg_cache_miss_penalty = func.threads_avg_cache_miss_penalty[thread_id]

        return self

    @property
    def on_rq(self):
        return self._on_rq

    @on_rq.setter
    def on_rq(self, v):
        self._on_rq = v

    @property
    def load(self):
        return self._load

    @property
    def vruntime(self):
        return self._vruntime

    @property
    def core(self):
        return self._core

    @core.setter
    def core(self, v: Core):
        if hasattr(self, 'core') and self._core is not None:
            self._core.cpu.remove_from_threads_sorted(self)
        self._core = v
        if self._core is not None:
            self._core.cpu.add_to_threads_sorted(self)

    @vruntime.setter
    def vruntime(self, v: float):
        if v > 0 and self.core is not None:
            self.core.cpu.remove_from_threads_sorted(self)
        self._vruntime = v
        if self.core is not None:
            self.core.cpu.add_to_threads_sorted(self)

    @load.setter
    def load(self, v):
        if self.core is None:
            self._load = v
        elif self._load != v:
            self.core.cpu.remove_from_threads_sorted(thread=self, inverted_thread_load=self._load * -1)
            self.core.runqueue.load -= self._load
            self._load = v
            self.core.cpu.add_to_threads_sorted(thread=self, inverted_thread_load=self._load * -1)
            self.core.runqueue.load += self._load

    @property
    def cpu_requests_share(self):
        return self._cpu_requests_share

    @cpu_requests_share.setter
    def cpu_requests_share(self, v: int):
        if v > 1000:
            error_message = "CPU requests share cannot be greater than {} in a single " \
                            "thread placed in a core. {} Given!".format(self.core.cpu.max_cpu_requests, v)
            raise Exception(error_message)
        else:
            difference = self._cpu_requests_share - v
            self._cpu_requests_share = v
            # TODO: I originally started with millicores = 1024, but I think it should be 1000. So, I converted
            #  all the millicores to 1000.
            millicores_to_share = (self._cpu_requests_share * 1024) / self.replica.host.cpu.max_cpu_requests
            self.load = self.average_load * millicores_to_share

            if self.core is not None and difference != 0:
                for thread_set in self.core.runqueue.thread_set_dict[self.id]:
                    # if thread_set.sum_cpu_requests != 0:
                    thread_set.sum_cpu_requests -= difference

    @property
    def cpu_limits(self):
        return self._cpu_limits

    @cpu_limits.setter
    def cpu_limits(self, v):
        if v > 1000:
            error_message = "CPU limits share cannot be greater than {} in a single " \
                            "thread placed in a core. {} Given!".format(self.core.cpu.max_cpu_requests, v)
            raise Exception(error_message)
        else:
            if self.core is not None:
                self.core.runqueue.decategorize_thread_from_sets(self)

            self._cpu_limits = v

            if self.core is not None:
                self.core.runqueue.categorize_thread_into_sets(self)
