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

import heapq
from typing import TYPE_CHECKING, Union, Dict, List, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sortedcontainers import SortedDict

from perfsim import Request, ReplicaThread, Utils, LoadGeneratorLogObserver, Observable, ServiceChainResultDict, \
    SimulationScenarioResultDict
from perfsim.observers.results_observer import ResultsObserver

if TYPE_CHECKING:
    from perfsim import Simulation


class LoadGenerator(Observable):
    """
    This class is responsible for generating a load for each service chain manager in a `simulation`.
    """

    #: Name of the LoadGenerator instance.
    name: str

    #: The ``Simulation`` object where traffic belongs to.
    sim: Simulation

    #: All ``Request`` instances in the simulation
    requests: list[Request]

    #: All ``ReplicaThread`` instances in the simulation
    threads: list[ReplicaThread]

    #: All ``ReplicaThread`` instances in the simulation (in dict)
    threads_dict: Dict[str, ReplicaThread]

    #: The next batch request arrival time. 
    _next_batch_arrival_time: Union[int, float]

    #: Next ``ServiceChainManager``s in the loop that arrive at `_next_batch_arrival_time`
    _next_scm_names: list[str]

    _min_arrival_scm_names: list[str]

    _scm_current_arrival_iteration_ids: Dict[str, int]

    #: Requests that are ready for thread generation in the next "THREAD GEN" event. List of tuple(subchain_id, request)
    _requests_ready_for_thread_generation: list[tuple[int, Request]]

    #: A sorted dictionary of all future transmissions completion time ("exact" means the clock time, not duration)
    _next_trans_completion_times: SortedDict

    #: Sum of all expected requests count in the simulation
    __total_requests_count: int

    #: Stores whether its the last request by scm_name (as keys)
    _last_request: Dict[str, bool]

    #: Stores requests latencies
    latencies: pd.DataFrame

    #: Stores requests arrival times
    arrivals: pd.DataFrame

    #: The event that is being triggered before traffic starts.
    before_traffic_start: str

    #: The event that is being triggered
    before_generate_threads: str

    #: The event that is being triggered before request is generated.
    before_requests_start: str

    #: The event that is being triggered at the end of initiate_next_batch_of_requests in being triggered.
    after_requests_start: str

    #: The event that is being triggered before estimating threads execution time.
    before_exec_time_estimation: str

    #: The event that is being triggered before start running threads.
    before_executing_threads: str

    #: The event that is being triggered after executing all threads/requests of this load generator.
    after_completing_load_generation: str

    #: The event that is being triggered after next batch arrival time is being calculated.
    after_next_batch_arrival_time_calculation: str

    #: The event that is being triggered before generating a thread for a request (within a subchain).
    before_generate_request_threads: str

    #: The event that is being triggered after generating a thread for a request (within a subchain).
    after_generate_request_threads: str

    #: The event that is being triggered after transmission completion time is being estimated.
    after_transmission_estimation: str

    #: The event that is being triggered after next event time is being estimated.
    after_estimating_time_of_next_event: str

    #: The event that is being triggered before transmitting packets
    before_transmit_requests_in_network: str

    #: The event that is being triggered after transmitting requests and load balancing threads on all hosts
    after_transmit_requests_in_network_and_load_balancing_threads: str

    #: The event that is being triggered after transmitting requests and load balancing threads on all hosts
    before_request_created: str

    #: This property stores the merged arrival tables from the traffic prototypes defined in the simulation scenario.
    __merged_arrival_table: List[Tuple[int, Request]]

    def __init__(self,
                 name: str,
                 simulation: Simulation,
                 notify_observers_on_event: bool = True):
        """
        A *LoadGenerator* is an object responsible for not only generating a given list of traffic objects
        *traffic_prototypes* on a given *simulation.cluster*, but to control the state, events and time of
        the entire simulation.

        :param name: Name of the LoadGenerator instance.
        :param simulation: The `Simulation` object where traffic belongs to.
        """

        self.name = name
        self.sim = simulation
        self.previous_event = None
        self.next_event = "REQUEST"
        self.requests = []
        self.threads = []
        self.latencies = pd.DataFrame(columns=["scenario #",
                                               "SFC",
                                               "iteration_id",
                                               "req_id_in_iteration",
                                               "latency",
                                               "arrival_time",
                                               "completion_time",
                                               "status",
                                               "traffic_type"])
        self.__total_requests_count = self.__calculate_total_requests_count()
        self._next_scm_names = list(self.sim.cluster.scm_dict.keys())
        self._scm_current_arrival_iteration_ids = {scm_name: 0 for scm_name in self._next_scm_names}
        self._requests_ready_for_thread_generation = []
        self._next_trans_completion_times = SortedDict({float('inf'): None})
        self._next_thread_completion_exact_times = SortedDict({float('inf'): None})
        self._last_request = {scm_name: False for scm_name in self.sim.traffic_prototypes_dict.keys()}
        self._completed_threads = 0
        self._completed_requests = 0
        self._next_batch_arrival_time = 0
        self._min_arrival_time = float('inf')
        self._min_arrival_scm_names = []
        self._last_transmission_id = 0
        self.notify_observers_on_event = notify_observers_on_event
        self.__merged_arrival_table = []
        heapq.heapify(self.__merged_arrival_table)
        self.merge_arrival_tables()
        super().__init__()
        if self.sim.debug_level > 0:
            self.attach_observer(observer=LoadGeneratorLogObserver(load_generator=self))
        self.attach_observer(observer=ResultsObserver(load_generator=self))

    def __calculate_total_requests_count(self):
        requests_count = 0
        for sfc_name, traffic_type_object in self.sim.scenario["traffic_scenario"]["service_chains"].items():
            requests_count += self.sim.traffic_prototypes_dict[traffic_type_object["traffic_type"]].requests_count
        return requests_count

    @property
    def total_requests_count(self):
        return self.__total_requests_count

    @total_requests_count.setter
    def total_requests_count(self, value):
        raise AttributeError(
            "The attribute total_requests_count is read-only and can only be set during initialization "
            "based on give simulation scenario.")

    @property
    def merged_arrival_table(self):
        return self.__merged_arrival_table

    @merged_arrival_table.setter
    def merged_arrival_table(self, value):
        raise Exception("Cannot set merged_arrival_table!")

    def register_events(self):
        self.register_event("before_traffic_start")
        self.register_event("before_requests_start")
        self.register_event("after_requests_start")
        self.register_event("before_generate_threads")
        self.register_event("before_exec_time_estimation")
        self.register_event("before_executing_threads")
        self.register_event("after_completing_load_generation")
        self.register_event("after_next_batch_arrival_time_calculation")
        self.register_event("before_generate_request_threads")
        self.register_event("after_generate_request_threads")
        self.register_event("after_transmission_estimation")
        self.register_event("after_estimating_time_of_next_event")
        self.register_event("before_transmit_requests_in_network")
        self.register_event("after_transmit_requests_in_network_and_load_balancing_threads")
        self.register_event("before_request_created")

    def execute_traffic(self) -> [ReplicaThread]:
        """
        This is the main function responsible to start the traffic in the cluster

        :param: debug: Enable/disable debugging mode
        """

        self.notify_observers(event_name=self.before_traffic_start)

        while self.next_event != "DONE":
            if self.next_event == "REQUEST":
                self._initiate_next_batch_of_requests()
            elif self.next_event == "THREAD GEN":
                self._initiate_next_endpoint_function_in_chain()
            elif self.next_event == "EXEC TIME EST":
                self._exec_time_estimation()
            elif self.next_event == "RUN THREADS":
                self._run_threads_on_hosts()

        for host_name, host in self.sim.cluster.cluster_scheduler.hosts_dict.items():
            if self.sim.time not in host.cpu.events:
                host.cpu.events[self.sim.time] = {key: 0 for (key, value) in
                                                  enumerate(np.arange(0, len(host.cpu.cores)))}

        self.notify_observers(event_name=self.after_completing_load_generation)
        return self.threads

    def _generate_threads(self, request: Request, subchain_id: int, load_balance: bool = True) -> None:
        current_replicas = request.init_next_microservices(subchain_id)
        self.notify_observers(event_name=self.before_generate_request_threads, request=request, subchain_id=subchain_id)
        replica_pair = current_replicas[subchain_id]
        replica_identifier_in_subchain = replica_pair[0]
        replica = replica_pair[1]
        current_node = request.current_nodes[subchain_id]
        threads = replica.generate_threads(from_subchain_id=subchain_id,
                                           node_in_subchain=current_node,
                                           load_balance=load_balance,
                                           parent_request=request,
                                           replica_identifier_in_subchain=replica_identifier_in_subchain)
        self.threads.extend(list(threads.values()))
        self.notify_observers(event_name=self.after_generate_request_threads, request=request, subchain_id=subchain_id,
                              threads=threads, current_replicas=current_replicas)

    def _initiate_next_endpoint_function_in_chain(self) -> None:
        self.notify_observers(event_name=self.before_generate_threads)

        _id = 0
        _load_balance_on_id = len(self._requests_ready_for_thread_generation) - 1
        for request_subchainid_pair in self._requests_ready_for_thread_generation:
            self._generate_threads(subchain_id=request_subchainid_pair[0],
                                   request=request_subchainid_pair[1],
                                   load_balance=(_load_balance_on_id == _id))
            _id += 1

        self._requests_ready_for_thread_generation = []
        self.next_event = "EXEC TIME EST"
        self.previous_event = "THREAD GEN"

    def _exec_time_estimation(self) -> None:
        self.notify_observers(event_name=self.before_exec_time_estimation)

        self.sim.cluster.topology.recalculate_transmissions_bw_on_all_links()
        next_trans_completion_time = self._next_trans_completion_times.peekitem(0)[0]

        if next_trans_completion_time == float('inf') or self._next_batch_arrival_time < next_trans_completion_time:
            time_of_next_event = self._next_batch_arrival_time
            self.prediction_for_the_next_event_after_running_threads = "REQUEST"
        else:
            time_of_next_event = self._next_trans_completion_times.peekitem(0)[0]
            self.prediction_for_the_next_event_after_running_threads = "THREAD GEN"

        self.time_of_next_event, self.duration_of_next_event, thread_ending_sooner = \
            self.sim.cluster.is_there_a_thread_that_ends_sooner(time_of_next_event)

        if self.duration_of_next_event == float('inf'):
            if self.previous_event != "THREAD GEN":
                self.next_event = "THREAD GEN"
            else:
                raise Exception("Next event can't be inf! Probably a bug! (number of active transmissions=" +
                                str(len(self.sim.cluster.topology.active_transmissions)) + ")")
        else:
            self.next_event = "RUN THREADS"

        self.notify_observers(event_name=self.after_estimating_time_of_next_event,
                              next_trans_completion_time=next_trans_completion_time,
                              time_of_next_event=self.time_of_next_event,
                              next_batch_arrival_time=self._next_batch_arrival_time,
                              estimated_next_event=self.next_event,
                              is_thread_ending_sooner=thread_ending_sooner)

        self.previous_event = "EXEC TIME EST"

    def _run_threads_on_hosts(self) -> None:
        self.notify_observers(event_name=self.before_executing_threads)

        self.sim.time += self.duration_of_next_event

        current_completed_threads = self.sim.cluster.run_active_threads(self.duration_of_next_event)

        self.notify_observers(event_name=self.before_transmit_requests_in_network)
        self.sim.cluster.transmit_requests_in_network(self.duration_of_next_event)
        self.sim.cluster.load_balance_threads_in_all_hosts()

        self._completed_threads += current_completed_threads

        if self._completed_requests == self.total_requests_count:
            self.next_event = "DONE"
        else:
            self.next_event = self.prediction_for_the_next_event_after_running_threads

        self.notify_observers(event_name=self.after_transmit_requests_in_network_and_load_balancing_threads,
                              current_completed_threads=current_completed_threads)
        self.previous_event = "RUN THREADS"

    def _initiate_next_batch_of_requests(self) -> None:
        self.notify_observers(event_name=self.before_requests_start)

        try:
            requests = [heapq.heappop(self.__merged_arrival_table)[1]]
            request_subchain_id_pairs = [(0, requests[0])]
            self.sim.time = requests[0].arrival_time
        except IndexError:
            self.next_event = "EXEC TIME EST"
            return

        while self.__merged_arrival_table and self.__merged_arrival_table[0][0] == requests[0].arrival_time:
            requests.append(heapq.heappop(self.__merged_arrival_table)[1])
            request_subchain_id_pairs.append((0, requests[-1]))

        self.requests.extend(requests)
        self._requests_ready_for_thread_generation.extend(request_subchain_id_pairs)
        self.next_event = "THREAD GEN"

        if self.__merged_arrival_table:
            self._next_batch_arrival_time = self.__merged_arrival_table[0][1].arrival_time
        else:
            self._next_batch_arrival_time = float('inf')

        self.previous_event = "REQUEST"

        self.notify_observers(event_name=self.after_requests_start)

    @property
    def completed_requests(self) -> int:
        """
        Return number of all completed requests
        """

        return self._completed_requests

    @completed_requests.setter
    def completed_requests(self, v):
        self._completed_requests = v

    def get_latencies_grouped_by_sfc(self) -> SimulationScenarioResultDict:
        """
        Return list of latencies for all requests of the service chain with the given name
        """

        mask = self.latencies['scenario #'].values == self.sim.scenario['name']
        sim_lats = pd.DataFrame(self.latencies.values[mask], self.latencies.index[mask], self.latencies.columns)
        grouped_lats = sim_lats.groupby("SFC")
        result: SimulationScenarioResultDict = {"service_chains": {}}

        for sfc_name, sfc_latencies in grouped_lats:
            ranges = pd.cut(sfc_latencies['completion_time'], np.arange(0, self.sim.time + 1e9, 1e9))
            grouped_completion_times = ranges.groupby(ranges, observed=False)
            grouped_throughput = grouped_completion_times.count().fillna(0).to_dict()
            grouped_lats_by_iteration = sfc_latencies.groupby("iteration_id")
            r = {"latency": {}, "completion_time": {}, "arrival_time": {}, "traffic_type": {}}

            for iteration_id, sfc_latencies_by_iteration in grouped_lats_by_iteration:
                for key in r.keys():
                    r[key][iteration_id] = {}
                    for _id, result_in_iteration in sfc_latencies_by_iteration.iterrows():
                        r[key][iteration_id][_id] = result_in_iteration[key]

            # TODO: Requests timeout need to be implemented
            sfc: ServiceChainResultDict = {
                'simulation_name': self.sim.name,
                'estimated_cost': 0,
                'total_requests': len(sfc_latencies),
                'successful_requests': len(sfc_latencies),
                'timeout_requests': 0,
                'avg_latency': sfc_latencies["latency"].mean(),
                'throughput': {str(k): grouped_throughput[k] for k in grouped_throughput.keys()},
                'arrival_times': {"iterations": r['arrival_time']},
                'latencies': {"iterations": r['latency']},
                'completion_times': {"iterations": r['completion_time']},
                'traffic_types': {"iterations": r['traffic_type']},
            }

            result["service_chains"][str(sfc_name)] = sfc

        return result

    def plot_latencies(self,
                       save_dir=None,
                       marker='o',
                       show_numbers=None,
                       moving_average=False,
                       save_values=False,
                       show: bool = True):
        plt.ioff()

        perfsim_lats = self.latencies["latency"].copy().reset_index(drop=True)
        fig = plt.figure(figsize=(15, 5), facecolor='w')
        plt.rcParams.update({'font.size': 10})

        if moving_average:
            perfsim_lats = perfsim_lats.rolling(window=3).mean()
        if save_values:
            perfsim_lats.to_csv(path_or_buf=save_dir + "perfsim_lats.csv")
            (perfsim_lats.values / 10 ** 9).tofile(save_dir + "perfsim_lats_values.txt", sep="\n")
        ax1 = perfsim_lats.plot(label="PerfSim (sfc-stress)", marker=marker)
        max_latency = perfsim_lats.max()

        if show_numbers:
            for i, v in enumerate(perfsim_lats):
                ax1.text(i, v + 25, "%0.2f" % (v / 10 ** 6), ha="center")

        plt.ylim(0, max_latency + max_latency * 0.1)
        ax1.set_xlabel("Request #")
        ax1.set_ylabel("Response Time (ms)")
        ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x) / 1000000, ',')))
        fig.tight_layout()
        plt.legend()

        if save_dir is not None:
            Utils.mkdir_p(dir_path=save_dir)
            plt.savefig(save_dir + "/latency_evaluation.pdf")

        if show:
            plt.show()
        else:
            plt.close()

    @property
    def last_transmission_id(self):
        return self._last_transmission_id

    @last_transmission_id.setter
    def last_transmission_id(self, v: int):
        self._last_transmission_id = v

    @property
    def next_trans_completion_times(self):
        return self._next_trans_completion_times

    @next_trans_completion_times.setter
    def next_trans_completion_times(self, v):
        raise AttributeError("next_trans_completion_times is read-only! It's going to be set automatically!")

    @property
    def requests_ready_for_thread_generation(self):
        return self._requests_ready_for_thread_generation

    @requests_ready_for_thread_generation.setter
    def requests_ready_for_thread_generation(self, v):
        raise AttributeError("requests_ready_for_thread_generation is read-only! It's going to be set automatically!")

    @property
    def next_batch_arrival_time(self):
        return self._next_batch_arrival_time

    @next_batch_arrival_time.setter
    def next_batch_arrival_time(self, v):
        raise AttributeError("next_batch_arrival_time is read-only! It's going to be set automatically!")

    def merge_arrival_tables(self):
        for scm_name, traffic_scenario_object in self.sim.scenario['traffic_scenario']['service_chains'].items():
            traffic_proto = self.sim.traffic_prototypes_dict[traffic_scenario_object['traffic_type']]

            for iteration_id, arrival_time in enumerate(traffic_proto.arrival_table):
                for uid in range(traffic_proto.parallel_user):
                    rq_num = iteration_id * traffic_proto.parallel_user + uid
                    req_id = self.sim.scenario["name"] + "_" + traffic_proto.name + "_" + scm_name + "_" + str(rq_num)

                    arrival_time_request_tuple = (arrival_time, Request(request_id=req_id,
                                                                        iteration_id=iteration_id,
                                                                        id_in_iteration=uid,
                                                                        load_generator=self,
                                                                        traffic_prototype=traffic_proto,
                                                                        scm=self.sim.cluster.scm_dict[scm_name],
                                                                        arrival_time=arrival_time))
                    heapq.heappush(self.__merged_arrival_table, arrival_time_request_tuple)
