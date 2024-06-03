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

from typing import TYPE_CHECKING, Tuple, List, Union

from perfsim import MicroserviceReplica, Observable, RequestLogObserver, TrafficPrototype

if TYPE_CHECKING:
    from perfsim import LoadGenerator, MicroserviceEndpointFunction, ServiceChainManager


class Request(Observable):
    """
    Request class is used to represent a real request in a service chain.
    Note that a "node" here means a tuple of (subchain_id, microservice_endpoint_function).
    """

    # Latency of the request
    latency: float

    # The service chain manager that is responsible for this request
    scm: ServiceChainManager

    #: The load generator that generated this request
    load_generator: LoadGenerator

    #: Request ID
    id: str

    #: ID of the iteration that this request was generated in
    iteration_id: int

    #: ID of the request within the iteration that this request was generated in
    id_in_iteration: int

    #: The current list of endpoint functions that this request is being routed to (as tuples of (subchain id,endpoint))
    _current_nodes: List[Union[None, Tuple[int, MicroserviceEndpointFunction]]]

    #: The list of current replicas that this request is being routed to (as tuples of (subchain id, replica))
    _current_replicas_in_nodes: List[Union[None, Tuple[int, MicroserviceReplica]]]

    #: The list of next endpoint functions that this request is being routed to (as tuples of (subchain id,endpoint))
    _next_nodes: List[Union[None, Tuple[int, MicroserviceEndpointFunction]]]

    #: The list of next replicas that this request is being routed to (as tuples of (subchain id, replica))
    _next_replicas_in_nodes: List[Union[None, Tuple[int, MicroserviceReplica]]]

    #: The list of the latency lists for each endpoint functions in each subchain (subchain id as key)
    _compute_times: List[List[Union[None, int, float]]]

    #: The list transmission times among replicas per each subchain id as key (and transmission time as value)
    _trans_times: List[Union[None, int, float]]

    #: The list of exact simulation time that the request is being routed to a replica in the subchain (as key)
    _trans_exact_times: List[Union[None, int, float]]

    #: The list of transmissions source replicas per subchain id as key (and transmission source replica as value)
    _trans_src_replicas: List[Union[None, MicroserviceReplica]]

    #: List of exact simulation times that a transmission is being started (per subchain id as key)
    _trans_init_times: List[Union[None, int, float]]

    #: List of all active subchains ids that this request is currently being served in
    _active_subchain_ids: List[int]

    """Keeps track of subchains status. Can take one of the following values:
     - "CREATED"
     - "CONCLUDED"
     - "IN TRANSMISSION"
     - "INIT MICROSERVICE"
     """
    _subchains_status: List[Union[None, str]]

    #: The number of subchains that this request is already being served in
    _completed_subchains_count: int

    #: The request status (IN_PROGRESS, COMPLETED, TIMED_OUT)
    status: str

    #: The traffic prototype in which this request is being created from
    traffic_prototype: TrafficPrototype

    before_init_next_microservices: str
    after_init_next_microservices: str
    before_finalizing_subchain: str
    before_concluding_request: str
    before_init_transmission: str
    after_init_transmission: str
    on_init_transmission: str
    before_finish_transmission: str
    after_finish_transmission: str

    def __init__(self,
                 request_id: str,
                 iteration_id: int,
                 id_in_iteration: int,
                 load_generator: LoadGenerator,
                 traffic_prototype: TrafficPrototype,
                 scm: ServiceChainManager,
                 arrival_time=0):
        self.waiting_time = None
        self.arrival_time = arrival_time
        self.completion_time = None
        self.load_generator = load_generator
        self.traffic_prototype = traffic_prototype
        self.scm = scm
        # self.execution_time = execution_time  # Time required by the job to execute.
        self.current_microservice_id = [-1 for i, v in enumerate(self.scm.subchains)]
        self.latency = 0
        self.current_active_threads = [0 for i, v in enumerate(self.scm.subchains)]
        self.total_current_active_threads = 0
        self.id = request_id
        self.iteration_id = iteration_id
        self.id_in_iteration = id_in_iteration
        self._current_nodes = [None for i, v in enumerate(self.scm.subchains)]
        self._current_replicas_in_nodes = [None for i, v in enumerate(self.scm.subchains)]
        self._next_nodes = [None for i, v in enumerate(self.scm.subchains)]
        self._next_replicas_in_nodes = [None for i, v in enumerate(self.scm.subchains)]
        self.status = "IN_PROGRESS"

        self._compute_times = [[] for i, v in enumerate(self.scm.subchains)]
        self._trans_times = [None for i, v in enumerate(self.scm.subchains)]
        self._trans_exact_times = [None for i, v in enumerate(self.scm.subchains)]
        self._trans_deltatimes = [[] for i, v in enumerate(self.scm.subchains)]
        self._trans_src_replicas = [None for i, v in enumerate(self.scm.subchains)]
        self._trans_init_times = [0 for i, v in enumerate(self.scm.subchains)]
        self._active_subchain_ids = [0]
        # self.current_active_node_in_subchains = [None for i, v in enumerate(self.service_chain_manager.subchains)]
        # self.current_active_node_in_subchains[0] = None
        self._subchains_status = ["CREATED" for i, v in enumerate(self.scm.subchains)]
        self._completed_subchains_count = 0

        super().__init__()
        if self.load_generator.sim.debug_level > 0:
            self.attach_observer(observer=RequestLogObserver(request=self))

    def register_events(self):
        self.register_event("before_init_next_microservices")
        self.register_event("after_init_next_microservices")
        self.register_event("before_finalizing_subchain")
        self.register_event("before_concluding_request")
        self.register_event("before_init_transmission")
        self.register_event("after_init_transmission")
        self.register_event("on_init_transmission")
        self.register_event("before_finish_transmission")
        self.register_event("after_finish_transmission")

    def finalize_subchain(self, subchain_id: int):
        self.notify_observers(event_name=self.before_finalizing_subchain, subchain_id=subchain_id)

        if self._subchains_status[subchain_id] != "CONCLUDED":
            self._subchains_status[subchain_id] = "CONCLUDED"
            self._completed_subchains_count += 1

        self._current_nodes[subchain_id] = None
        self._current_replicas_in_nodes[subchain_id] = None
        self._next_nodes[subchain_id] = None
        self._next_replicas_in_nodes[subchain_id] = None
        self._active_subchain_ids.remove(subchain_id)
        self._compute_times[subchain_id].append(self.load_generator.sim.time - self._trans_init_times[subchain_id])

        if self._completed_subchains_count == len(self.scm.subchains):
            self.conclude(time=self.load_generator.sim.time)

    def set_next_nodes_and_replicas(self, next_nodes: List[Tuple[int, MicroserviceEndpointFunction]]):
        for next_node in next_nodes:
            next_endpoint_func = next_node[1]
            next_endpoint_func_identifier_in_subchain = next_node[0]
            next_replica = next_endpoint_func.microservice.next_replica()
            node_subchain_id = self.scm.node_subchain_id_map[next_node]
            self._next_replicas_in_nodes[node_subchain_id] = (next_endpoint_func_identifier_in_subchain, next_replica)
            self._next_nodes[node_subchain_id] = (next_endpoint_func_identifier_in_subchain, next_endpoint_func)

    def init_transmission(self, node_in_alt_graph: Tuple[int, MicroserviceEndpointFunction]) -> int or bool:
        next_nodes = list(self.scm.alternative_graph.successors(node_in_alt_graph))
        subchain_id = self.scm.node_subchain_id_map[node_in_alt_graph]
        current_replica_of_node = self._current_replicas_in_nodes[subchain_id]

        self.set_next_nodes_and_replicas(next_nodes)
        self._compute_times[subchain_id].append(self.load_generator.sim.time - self._trans_init_times[subchain_id])
        self.notify_observers(event_name=self.before_init_transmission, node=node_in_alt_graph, next_nodes=next_nodes)

        if len(next_nodes) == 0:
            self.finalize_subchain(subchain_id)
            return False

        # min_transmission_time = float('inf')
        # subchain_ids_of_fastest_transmissions = []

        next_node_subchain_ids_transmissions = {}

        for next_node in next_nodes:
            next_node_subchain_id = self.scm.node_subchain_id_map[next_node]
            current_node_replica = self._current_replicas_in_nodes[subchain_id]
            next_node_replica = self._next_replicas_in_nodes[next_node_subchain_id]

            if current_node_replica is None:
                raise Exception("WTF!?")
                # _current_node_replica = self.next_replicas_in_nodes[_next_node_subchain_id]

            current_replica = current_node_replica[1]

            self._subchains_status[next_node_subchain_id] = "IN TRANSMISSION"
            self._trans_init_times[next_node_subchain_id] = self.load_generator.sim.time

            next_node_subchain_ids_transmissions[next_node_subchain_id] = \
                current_replica_of_node[1].host.nic["egress"].reserve_transmission_for_request(
                    request=self,
                    subchain_id=next_node_subchain_id,
                    src_replica=current_replica_of_node[1],
                    source_node=node_in_alt_graph,
                    destination_replica=self._next_replicas_in_nodes[next_node_subchain_id][1],
                    destination_node=next_node)
            self._trans_src_replicas[next_node_subchain_id] = current_replica
            self._active_subchain_ids.append(next_node_subchain_id)

            self.notify_observers(event_name=self.on_init_transmission,
                                  current_node=node_in_alt_graph,
                                  next_node=next_node,
                                  current_replica=current_node_replica,
                                  next_replica=next_node_replica)

            self._current_replicas_in_nodes[next_node_subchain_id] = self._next_replicas_in_nodes[next_node_subchain_id]
            self._current_nodes[next_node_subchain_id] = self._next_nodes[next_node_subchain_id]

        # self.recalculate_transmission_times(next_node_subchain_ids_transmissions)
        # self.find_and_set_next_transmissions_in_all_subchains()

        if len(next_nodes) > 1:
            self.finalize_subchain(subchain_id)

        self.notify_observers(event_name=self.after_init_transmission, node=node_in_alt_graph)

        # return _min_transmission_time
        return next_node_subchain_ids_transmissions

    # def recalculate_transmission_times(self, next_node_subchain_ids_transmissions):
    #     for _next_node_subchain_id in next_node_subchain_ids_transmissions:
    #         previous_transmission_exact_time = next_node_subchain_ids_transmissions[_next_node_subchain_id]
    #         self.transmission_times[_next_node_subchain_id] = \
    #             next_node_subchain_ids_transmissions[_next_node_subchain_id].calculate_transmission_time()
    #         self.transmission_exact_times[_next_node_subchain_id] = \
    #             self.transmission_times[_next_node_subchain_id] + self.load_generator.time
    #
    #         if next_node_subchain_ids_transmissions[_next_node_subchain_id].transmission_exact_time != \
    #                 previous_transmission_exact_time:
    #             self.load_generator._next_trans_completion_times.pop(previous_transmission_exact_time, 0)
    #             self.load_generator._next_trans_completion_times.update({
    #                 self.transmission_exact_times[_next_node_subchain_id]: {
    #                     "request": self,
    #                     "source_host": self.transmission_src_replicas[_next_node_subchain_id].host,
    #                     "transmission": next_node_subchain_ids_transmissions[_next_node_subchain_id]
    #                 }})
    #         self.sim.logger.log(
    #             "     ***** Transmission time is " + str(
    #                 self.transmission_times[_next_node_subchain_id]), 3)

    # def recalculate_transmission_times(self, next_node_subchain_ids_transmissions):
    #     for _next_node_subchain_id in next_node_subchain_ids_transmissions:
    #         self.transmission_times[_next_node_subchain_id] = \
    #             next_node_subchain_ids_transmissions[_next_node_subchain_id].calculate_transmission_time()
    #         self.transmission_exact_times[_next_node_subchain_id] = \
    #             self.transmission_times[_next_node_subchain_id] + self.load_generator.time
    #         self.load_generator._next_trans_completion_times.update({
    #             self.transmission_exact_times[_next_node_subchain_id]: {
    #                 "request": self,
    #                 "source_host": self.transmission_src_replicas[_next_node_subchain_id].host,
    #                 "transmission": next_node_subchain_ids_transmissions[_next_node_subchain_id]
    #             }})
    #         self.sim.logger.log(
    #             "     ***** Transmission time is " + str(self.transmission_times[_next_node_subchain_id]) +
    #             " (payload = " +
    #             str(next_node_subchain_ids_transmissions[_next_node_subchain_id].remaining_payload_size) +
    #             " | remaining network latency = " +
    #             str(next_node_subchain_ids_transmissions[_next_node_subchain_id].total_latency) + ")", 3)

    # def find_and_set_next_transmissions_in_all_subchains(self):
    #     _min_transmission_time = float('inf')
    #     _fastest_transmittable_subchain_ids = []
    #     _active_hosts_in_subchain_ids = []
    #     _source_host = None
    #
    #     for subchain_id in self.active_subchain_ids:
    #         _transmission_time = self.transmission_times[subchain_id]
    #
    #         if _transmission_time is not None and self.statuses[subchain_id] == "IN TRANSMISSION":
    #             if _min_transmission_time == self.transmission_times[subchain_id]:
    #                 _fastest_transmittable_subchain_ids.append(subchain_id)
    #                 _active_hosts_in_subchain_ids.append(self.current_replicas_in_nodes[subchain_id][1].host)
    #             elif self.transmission_times[subchain_id] < _min_transmission_time:
    #                 _min_transmission_time = self.transmission_times[subchain_id]
    #                 _fastest_transmittable_subchain_ids = [subchain_id]
    #                 _active_hosts_in_subchain_ids = [self.current_replicas_in_nodes[subchain_id][1].host]
    #                 _source_host = self.transmission_src_replicas[subchain_id].host
    #
    #             # if _transmission_time == 0 and self.statuses == "IN TRANSMISSION":  # same host
    #             #     self.load_generator._requests_ready_for_thread_generation.append((subchain_id, self))
    #             #     self.load_generator.next_event = "MICROSERVICE"
    #             #     self.finish_transmission(self.current_nodes[_subchain_id])
    #             # else:  # different host
    #     # TODO: is this line needed?
    #     self.next_subchain_ids_to_finish_transmission = _fastest_transmittable_subchain_ids.copy()
    #
    #     next_transmission_exact_time = _min_transmission_time + self.load_generator.time
    #     # self.load_generator.next_trans_completion_times.add(_min_transmission_time)
    #     self.load_generator._next_trans_completion_times.update(
    #         {next_transmission_exact_time: {
    #             "request": self,
    #             "subchain_id": _fastest_transmittable_subchain_ids,
    #             "destination_hosts": _active_hosts_in_subchain_ids,
    #             "source_host": _source_host
    #         }
    #         })
    #     self.sim.logger.log(
    #         "@@@ Add a transmission time in the load generator with duration=" +
    #         str(_min_transmission_time) + " (T=" +
    #         str(next_transmission_exact_time) +
    #         "), however, next transmission is going to end at T=" +
    #         str(
    #             self.load_generator._next_trans_completion_times.peekitem(
    #                 0)[0]) +
    #         " @@@", 2)
    #     self.sim.logger.log(
    #         "@@@ Next subchain ids to finish transmissions in this request " + str(
    #             self) + " = " +
    #         str(self.next_subchain_ids_to_finish_transmission) +
    #         ") @@@", 2)

    def finish_transmission_by_subchain_id(self, subchain_id: int):
        node = self._current_nodes[subchain_id]
        self.finish_transmission(node)

    def finish_transmission(self, node_in_alt_graph: Tuple) -> None:
        self.notify_observers(event_name=self.before_finish_transmission, node=node_in_alt_graph)
        subchain_id = self.scm.node_subchain_id_map[node_in_alt_graph]
        _active_replica_in_subchain = self._current_replicas_in_nodes[subchain_id]
        self._trans_times[subchain_id] = None
        self._subchains_status[subchain_id] = "INIT MICROSERVICE"
        self._trans_deltatimes[subchain_id].append(self.load_generator.sim.time - self.trans_init_times[subchain_id])
        self.notify_observers(event_name=self.after_finish_transmission, node=node_in_alt_graph)

    def init_next_microservices(self, subchain_id: int) -> List[Tuple[int, MicroserviceReplica]]:
        current_node = self._current_nodes[subchain_id]
        if current_node is None:
            next_nodes = [self.scm.root]
        else:
            next_nodes = [self.scm.alternative_graph.successors(current_node)]

        if self._current_replicas_in_nodes[subchain_id] is None:
            # Let's call set_next_nodes_and_replicas because current replica in current subchain is not set
            self.set_next_nodes_and_replicas(next_nodes)

        self.notify_observers(event_name=self.before_init_next_microservices,
                              subchain_id=subchain_id,
                              next_nodes=next_nodes)

        self._trans_init_times[subchain_id] = self.load_generator.sim.time
        self._subchains_status[subchain_id] = "IN TRANSMISSION"

        self._current_replicas_in_nodes = self._next_replicas_in_nodes.copy()
        self._current_nodes = self._next_nodes.copy()

        self.notify_observers(event_name=self.after_init_next_microservices,
                              subchain_id=subchain_id,
                              replicas=self._current_replicas_in_nodes)

        return self._current_replicas_in_nodes

    def get_node_names(self):
        return ["(" + str(n[0]) + "," + str(n[1]) + ")" if n is not None else "None" for n in self._current_nodes]

    @staticmethod
    def get_next_nodes_names(next_nodes: List[Tuple[int, MicroserviceEndpointFunction]]):
        return ["(" + str(n[0]) + "," + str(n[1]) + ")" if n is not None else "None" for n in next_nodes]

    def get_current_replicas_names(self):
        return ["(" + str(r[0]) + "," + str(r[1]) + ")" if r is not None else "None" for r in
                self._current_replicas_in_nodes]

    def get_next_replicas_names(self):
        return ["(" + str(r[0]) + "," + str(r[1]) + ")" if r is not None else "None" for r in
                self._next_replicas_in_nodes]

    def get_current_replicas_host_names(self):
        return [str(r[1].host) if r is not None else "None" for r in self._current_replicas_in_nodes]

    def get_next_replicas_host_names(self):
        return [str(r[1].host) if r is not None else "None" for r in self._next_replicas_in_nodes]

    def conclude(self, time: Union[int, float]):
        self.notify_observers(event_name=self.before_concluding_request)
        # self.__compute_times.append(self.load_generator.time - self.current_microservice_init_time)
        self.load_generator.completed_requests += 1
        self.completion_time = time
        self.latency = self.completion_time - self.arrival_time
        self.status = "COMPLETED"
        self.load_generator.latencies.loc[self.id] = {"scenario #": self.load_generator.sim.scenario['name'],
                                                      "SFC": self.scm.name,
                                                      "iteration_id": self.iteration_id,
                                                      "req_id_in_iteration": self.id_in_iteration,
                                                      "latency": round(self.latency),
                                                      "arrival_time": round(self.arrival_time),
                                                      "completion_time": round(self.completion_time),
                                                      "status": self.status,
                                                      "traffic_type": self.traffic_prototype.name}

    @property
    def compute_times(self):
        return self._compute_times

    @compute_times.setter
    def compute_times(self, value):
        raise AttributeError("Attribute compute_times is read-only! It is not supposed to be set.")

    @property
    def trans_times(self):
        return self._trans_times

    @trans_times.setter
    def trans_times(self, value):
        raise AttributeError("Attribute transmission_times is read-only! It is not supposed to be set.")

    @property
    def trans_exact_times(self):
        return self._trans_exact_times

    @trans_exact_times.setter
    def trans_exact_times(self, value):
        raise AttributeError("Attribute transmission_exact_times is read-only! It is not supposed to be set.")

    @property
    def trans_init_times(self):
        return self._trans_init_times

    @trans_init_times.setter
    def trans_init_times(self, v):
        raise AttributeError("Attribute trans_init_times is read-only! It is not supposed to be set.")

    @property
    def current_nodes(self):
        return self._current_nodes

    @current_nodes.setter
    def current_nodes(self, v):
        raise AttributeError("Attribute current_nodes is read-only! It is not supposed to be set.")

    @property
    def current_replicas_in_nodes(self):
        return self._current_replicas_in_nodes

    @current_replicas_in_nodes.setter
    def current_replicas_in_nodes(self, v):
        raise AttributeError("Attribute current_replicas_in_nodes is read-only! It is not supposed to be set.")

    @property
    def subchains_status(self) -> List[Union[None, str]]:
        return self._subchains_status

    @subchains_status.setter
    def subchains_status(self, v):
        raise AttributeError("Attribute subchains_status is read-only! It is not supposed to be set.")

    @property
    def next_replicas_in_nodes(self):
        return self._next_replicas_in_nodes

    @next_replicas_in_nodes.setter
    def next_replicas_in_nodes(self, v):
        raise AttributeError("Attribute next_replicas_in_nodes is read-only! It is not supposed to be set from outside"
                             "of the class.")

    @property
    def next_nodes(self):
        return self._next_nodes

    @next_nodes.setter
    def next_nodes(self, v):
        raise AttributeError("Attribute next_nodes is read-only! It is not supposed to be set from outside of the "
                             "class.")

    @property
    def trans_deltatimes(self):
        return self._trans_deltatimes

    @trans_deltatimes.setter
    def trans_deltatimes(self, v):
        raise AttributeError("Attribute trans_deltatimes is read-only! It is not supposed to be set from outside of "
                             "the class.")

    def __str__(self):
        return self.id

    def __hash__(self):
        return hash(str(self))

    def __gt__(self, other):
        return self.arrival_time > other.arrival_time

    def __lt__(self, other):
        return self.arrival_time < other.arrival_time

    def __eq__(self, other):
        return self.arrival_time == other.arrival_time

    def __ne__(self, other):
        return self.arrival_time != other.arrival_time

    def __ge__(self, other):
        return self.arrival_time >= other.arrival_time

    def __le__(self, other):
        return self.arrival_time <= other.arrival_time
