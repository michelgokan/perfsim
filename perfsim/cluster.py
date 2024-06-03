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

from typing import TYPE_CHECKING, Tuple, Dict, Union

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D

from perfsim import ClusterScheduler, Topology, ServiceChainManager, Utils, \
    MicroserviceEndpointFunction, ServiceChain, Observable, ClusterLogObserver

if TYPE_CHECKING:
    from perfsim import Microservice, Simulation


class Cluster(Observable):
    """
    A *Cluster* is imitating a real heterogeneous cluster with a configurable ``NetworkTopology``,
    ``PlacementScenario`` and a set of ``ServiceChainManager``s.
    """

    #: A reference to the parent LoadGenerator instance
    # load_generator: LoadGenerator

    #: Name of the cluster
    name: str

    #: A dictionary of all service chains running on the cluster (key=id, value=service chain)
    __scm_dict: Dict[str, ServiceChainManager]

    #: The hosts and routers placement scenario on the cluster
    # placement_scenario: PlacementScenario

    #: The network topology of the cluster
    topology: Topology

    #: List of all `Microservice` references running on this cluster
    __microservices_dict: Dict[str, Microservice]

    #: The `ClusterScheduler` of this cluster responsible for scheduling replicas on the given topology
    cluster_scheduler: ClusterScheduler

    #: The timeout threshold for network transmissions
    network_timeout: float

    #: The parent `Simulation` instance
    sim: Simulation

    def __init__(self,
                 name: str,
                 simulation: Simulation,
                 # placement_scenario: PlacementScenario,
                 topology: Topology,
                 service_chains_dict: Dict[str, ServiceChain] = None,
                 scm_dict: Dict[str, ServiceChainManager] = None,
                 network_timeout: float = float('inf')):
        """
        A *Cluster* is imitating a real heterogeneous cluster with a configurable `NetworkTopology`,
        `PlacementScenario` and a set of `ServiceChainManager` instances.

        :param: name: Name of the cluster
        :param: service_chain_managers: A dict of all service chains running on the cluster
        :param: placement_algorithm: The hosts and routers' placement scenario on the cluster
        :param: topology: The network topology of the cluster
        :param: network_timeout: The network timeout
        """

        if service_chains_dict is None and scm_dict is None:
            raise Exception("Either service_chains_dict or scm_dict must be provided")
        elif service_chains_dict is not None and scm_dict is not None:
            raise Exception("Only one of service_chains or scm_dict must be provided")

        self.name = name
        self.sim = simulation

        if service_chains_dict is not None:
            self.set_service_chains_dict(service_chains_dict=service_chains_dict)
        else:
            self.set_scm_dict(scm_dict=scm_dict)

        self.topology = topology
        self.network_timeout = network_timeout if network_timeout != -1 else float('inf')

        self.__set_hosts_cluster()
        self.__set_routers_cluster()

        self.cluster_scheduler = ClusterScheduler(cluster=self)
        self.topology.reinitiate_topology()
        super().__init__()
        if self.sim.debug_level > 0:
            self.attach_observer(observer=ClusterLogObserver(cluster=self))

    def reinit(self):
        """
        Reinitialize the cluster

        :return: None
        """

        self.__init__(name=self.name,
                      simulation=self.sim,
                      topology=self.topology,
                      scm_dict=self.__scm_dict,
                      network_timeout=self.network_timeout)

    def count_total_service_edges(self):
        """
        Counts the total number of edges in the service topology that is being deployed in this cluster.

        :return: The total number of edges in the service topology
        """

        total_edges_count = 0
        for service_chain_manager in self.__scm_dict.values():
            total_edges_count += len(service_chain_manager.service_chain.edges)
        return total_edges_count

    def register_events(self):
        """
        Register all events of the cluster

        :return: None
        """

        self.register_event("after_finish_running_threads_on_a_host")
        self.register_event("after_finish_running_a_thread")
        self.register_event("before_transmitting_requests_in_network")
        self.register_event("in_transmitting_an_active_transmission")
        self.register_event("after_transmitting_an_active_transmission")
        self.register_event("before_calling_is_there_a_thread_that_ends_sooner_function")
        self.register_event("before_checking_a_thread_ends_sooner")
        self.register_event("after_calling_is_there_a_thread_that_ends_sooner_function")
        self.register_event("before_load_balancing_a_host")

    def __set_hosts_cluster(self):
        """
        Set the cluster of all hosts in the topology to this cluster

        :return:  None
        """

        for _host in self.topology.hosts_dict.values():
            _host.cluster = self

    def __set_routers_cluster(self):
        """
        Set the cluster of all routers in the topology to this cluster

        :return:
        """

        for _router in self.topology.routers_dict.values():
            _router.cluster = self

    @property
    def scm_dict(self) -> Dict[str, ServiceChainManager]:
        """
        List of all `ServiceChainManager` references running on this cluster

        :return: The list of all `ServiceChainManager` references running on this cluster
        """

        return self.__scm_dict

    def __add_scm(self, scm: ServiceChainManager):
        """
        Add a service chain manager to the cluster

        :param scm: The service chain manager to add to the cluster
        :return:  None
        """

        if scm.name not in self.scm_dict:
            self.__scm_dict[scm.name] = scm
        else:
            raise ValueError(f'ServiceChainManager with name {scm.name} already exists')

    def __add_microservices(self, microservices_dict: Dict[str, Microservice]):
        """
        Add a set of microservices to the cluster

        :param microservices_dict: The set of microservices to add to the cluster
        :return:  None
        """

        for ms in microservices_dict.values():
            self.__add_microservice(microservice=ms)

    def set_service_chains_dict(self, service_chains_dict: Dict[str, ServiceChain]):
        """
        Set the service chains of the cluster

        :param service_chains_dict: The service chains to set
        :return: None
        """
        self.__microservices_dict = {}
        self.__scm_dict = {}

        for sfc in service_chains_dict.values():
            self.__add_scm(scm=ServiceChainManager(name=sfc.name, service_chain=sfc))
            self.__add_microservices(microservices_dict=sfc.microservices_dict)

    def set_scm_dict(self, scm_dict: Dict[str, ServiceChainManager]):
        """
        Set the service chain managers of the cluster. This method is used to set the service chain managers of the
        cluster when the cluster is created from a dictionary of service chain managers.

        :param scm_dict:
        :return:
        """

        self.__microservices_dict = {}
        self.__scm_dict = {}

        for scm in scm_dict.values():
            self.__add_scm(scm=scm)
            self.__add_microservices(microservices_dict=scm.service_chain.microservices_dict)

    @scm_dict.setter
    def scm_dict(self, scm_dict: Dict[str, ServiceChainManager]):
        """
        Set the service chain managers of the cluster. This method is used to set the service chain managers of the
        cluster when the cluster is created from a dictionary of service chain managers.

        :param scm_dict:
        :return:
        """

        raise Exception('ServiceChainManagersDict is read only! Use set_scm_dict instead')

    def is_there_a_thread_that_ends_sooner(self, time_of_next_event: int) -> Tuple[float, float, bool]:
        """
        Check all active threads to see if there is one that ends sooner that ``time_of_next_event``
        """

        self.notify_observers(event_name="before_calling_is_there_a_thread_that_ends_sooner_function",
                              time_of_next_event=time_of_next_event)

        if len(self.cluster_scheduler.active_threads) == 0:
            # If there are no active threads, then by default we know the next event, whatever it is, is the next
            it_takes_more_time_to_finish_at_least_one_thread_before_next_event = False
        else:
            it_takes_more_time_to_finish_at_least_one_thread_before_next_event = True
        duration_of_next_event = time_of_next_event - self.sim.time
        # run_threads = True

        # hosts_to_consider = set()
        # TODO: a possible optimization would be that instead of checking all hosts/cores,
        #  only check hosts that has threads! (is it possible?) Instead of iterating over
        #  hosts, iterate over threads (?)

        for thread in self.cluster_scheduler.active_threads:
            if thread.core.runqueue is not None and thread.on_rq:
                # hosts_to_consider.add(host)
                if self.sim.time > time_of_next_event:
                    raise Exception("What the hell!? Did we miss a request somewhere in the chain...!?")
                else:
                    duration_to_finish = thread.get_exec_time_on_rq()
                    time_to_finish = duration_to_finish + self.sim.time
                    self.notify_observers(event_name="before_checking_a_thread_ends_sooner",
                                          thread=thread,
                                          duration_to_finish=duration_to_finish,
                                          time_to_finish=time_to_finish,
                                          time_of_next_event=time_of_next_event)

                    if time_to_finish < time_of_next_event:
                        it_takes_more_time_to_finish_at_least_one_thread_before_next_event = False
                        time_of_next_event = time_to_finish
                        duration_of_next_event = duration_to_finish

        if it_takes_more_time_to_finish_at_least_one_thread_before_next_event:
            duration_of_next_event = time_of_next_event - self.sim.time

        self.notify_observers(event_name="after_calling_is_there_a_thread_that_ends_sooner_function",
                              result=it_takes_more_time_to_finish_at_least_one_thread_before_next_event,
                              time_of_next_event=time_of_next_event,
                              duration_of_next_event=duration_of_next_event)

        return time_of_next_event, duration_of_next_event, it_takes_more_time_to_finish_at_least_one_thread_before_next_event

    def run_threads_on_hosts(self, duration: float) -> int:
        """
        Run all threads on all active hosts for ``duration`` nanoseconds

        :param duration: Duration of threads execution in nanoseconds
        """

        completed_threads = 0

        for host in self.cluster_scheduler.active_hosts:
            host_completed_threads = 0

            for core in host.cpu.cores:
                current_completed_threads = core.exec_threads(duration)
                host_completed_threads += current_completed_threads
                completed_threads += current_completed_threads

            self.notify_observers(event_name="finish_running_threads_on_a_host",
                                  host=host,
                                  completed_threads_on_host=host_completed_threads,
                                  completed_threads_on_all_hosts=completed_threads)

        return completed_threads

    def run_active_threads(self, duration: Union[int, float]) -> int:
        """
        Transmit all requests in network for ``duration`` nanoseconds

        :param duration: Duration of threads execution in nanoseconds
        """

        completed_threads = 0

        for thread in self.cluster_scheduler.active_threads:
            current_completed_threads = thread.exec(duration=duration)
            completed_threads += current_completed_threads
            self.notify_observers(event_name="finish_running_a_thread",
                                  current_completed_threads=current_completed_threads,
                                  completed_threads=completed_threads)

        return completed_threads

    def transmit_requests_in_network(self, duration: Union[int, float]):
        """
        Transmit all requests in network for duration nanoseconds

        :param: duration: Duration of network transmissions in nanoseconds

        :return: None
        """

        if duration == float('inf'):
            return

        is_there_any_finished_transmissions = False
        self.notify_observers(event_name="before_transmitting_requests_in_network")

        for trans in list(self.topology.active_transmissions):
            request_subchainid_pair = trans.subchain_id_request_pair
            req = request_subchainid_pair[0]
            subchain_id = request_subchainid_pair[1]
            host = trans.src_replica.host
            # transmission = host.nic["egress"].transmissions[(_active_subchain_id, request)]
            self.notify_observers(event_name="in_transmitting_an_active_transmission",
                                  request=req,
                                  active_subchain_id=subchain_id,
                                  duration=duration)

            if req.subchains_status[subchain_id] == "IN TRANSMISSION":
                remaining_transmission_time = trans.transmit(duration)

                if -0.001 < remaining_transmission_time < 0.001:
                    duration += remaining_transmission_time

                req.trans_times[subchain_id] = remaining_transmission_time
                if req.trans_exact_times[subchain_id] != trans.transmission_exact_time:
                    req_trans_from_sorted_dict = \
                        self.sim.load_generator.next_trans_completion_times.get(req.trans_exact_times[subchain_id])
                    trans_from_sorted_dict = \
                        self.sim.load_generator.next_trans_completion_times.get(trans.transmission_exact_time)
                    # We keep track of number of transmissions at each timestamp using the "counter" key!
                    # Using this counter prevents poping multiple dying transmissions from the SortedDict.

                    if req_trans_from_sorted_dict is not None and req_trans_from_sorted_dict["counter"] > 1:
                        req_trans_from_sorted_dict["counter"] -= 1
                    else:
                        self.sim.load_generator.next_trans_completion_times.pop(req.trans_exact_times[subchain_id], 0)

                    self.sim.load_generator.next_trans_completion_times.update({trans.transmission_exact_time: {
                        "counter": trans_from_sorted_dict["counter"] + 1 if trans_from_sorted_dict is not None else 1
                    }})
                req.trans_exact_times[subchain_id] = trans.transmission_exact_time

                if req.trans_times[subchain_id] < 0:
                    raise Exception("Error (time = " + str(self.sim.time) + " ): Remaining transmission " +
                                    "time (" + str(req._trans_times[subchain_id]) +
                                    ") is less than zero! Something went really wrong here!")

                self.notify_observers(event_name="after_transmitting_an_active_transmission",
                                      request=req,
                                      active_subchain_id=subchain_id,
                                      duration=duration)

                if req.trans_times[subchain_id] <= 0:
                    req.status = "MICROSERVICE"
                    is_there_any_finished_transmissions = True
                    # request.load_generator.requests_in_transmission.remove(request)
                    req.load_generator.requests_ready_for_thread_generation.append((subchain_id, req))
                    host.nic["egress"].release_transmission_for_request(req, subchain_id)
                    req.finish_transmission_by_subchain_id(subchain_id)

                    transmission_in_sorted_dict = req.load_generator.next_trans_completion_times.peekitem(0)
                    if transmission_in_sorted_dict[0] == self.sim.time:
                        if transmission_in_sorted_dict is not None and transmission_in_sorted_dict[1]["counter"] > 1:
                            transmission_in_sorted_dict[1]["counter"] -= 1
                        else:
                            req.load_generator.next_trans_completion_times.popitem(0)

        # TODO: This can be optimized - instead of recalculating for all links, we can recalculate for just
        #  a portion of links
        if is_there_any_finished_transmissions:
            self.topology.recalculate_transmissions_bw_on_all_links()

    def load_balance_threads_in_all_hosts(self):
        """
        Perform CPU load-balancing on all hosts

        :return: None
        """
        # for host in self.cluster_scheduler.hosts.values():
        for host in list(self.cluster_scheduler.active_hosts):
            self.notify_observers(event_name="before_load_balancing_a_host", host=host)
            host.cpu.load_balance()

    def run_idle(self, until: int) -> None:
        """
        Running threads idle for ``until`` - ``core.runqueue.time`` nanoseconds

        :param until: The time when running idle stops.
        """
        for host_name, host in self.cluster_scheduler.hosts_dict.items():
            for core in host.cpu.cores:
                core.runqueue.run_idle(until - core.cpu.host.cluster.sim.time)

    @property
    def microservices_dict(self):
        """
        List of all `Microservice` references running on this cluster

        :return: The list of all `Microservice` references running on this cluster
        """
        return self.__microservices_dict

    @microservices_dict.setter
    def microservices_dict(self, value):
        raise Exception("This property is read-only! Alter microservices via service_chain_managers!")

    def __add_microservice(self, microservice: Microservice):
        """
        Add a microservice to the cluster.

        :param microservice: The microservice to add to the cluster

        :return: None
        """
        if microservice.name not in self.microservices_dict:
            # raise Exception("Microservice with name '" + microservice.name + "' already exists in the cluster!")
            # Maybe microservice with the same name exists in the cluster, which serves multiple service chains.
            # So we should not raise an exception here.
            self.__microservices_dict[microservice.name] = microservice

    def __remove_microservice(self, microservice: Microservice):
        """
        Remove a microservice from the cluster.

        :param microservice: The microservice to remove from the cluster

        :return: None
        """
        if microservice.name not in self.microservices_dict:
            raise Exception("Microservice with name '" + microservice.name + "' does not exist in the cluster!")
        del self.__microservices_dict[microservice.name]

    def draw_all_service_chains(self, save_dir: str = None, show: bool = True):
        """
        Draw all service chains of the cluster

        :param save_dir:
        :param show:
        :return:
        """

        function_color = '#FFDB58'
        scm_color = "#808080"

        _G = nx.MultiDiGraph()
        color_map = []
        edge_labels = {}
        node_labels = {}

        for _scm in self.scm_dict:
            _G.add_edges_from(_scm.service_chain.edges)
            _G.add_edge(_scm, list(_scm.service_chain.nodes)[0])

            for u, v, c in _scm.service_chain.edges:
                edge_data = _scm.service_chain.get_edge_data(u, v, c)
                edge_labels[u, v] = edge_data["name"] + ":" + str(edge_data["payload"]) + "B"

        for _node in _G:
            node_labels[_node] = str(_node)
            if isinstance(_node, MicroserviceEndpointFunction):
                color_map.append(function_color)
            else:  # elif isinstance(ServiceChainManager)
                color_map.append(scm_color)

        pos = nx.spring_layout(_G)
        # fig = plt.figure(figsize=(15, 5), facecolor='w')
        fig = plt.figure(1, figsize=(12, 12))
        plt.rcParams.update({'font.size': 10})
        ax = plt.gca()
        nx.draw_networkx_nodes(_G, pos=pos, node_color=color_map, ax=ax, node_size=900)
        nx.draw_networkx_labels(_G, pos=pos, labels=node_labels, font_size=12, font_color='0')
        # connectionstyle='arc3, rad = 0.3')

        for e in _G.edges:
            # _reverse_edges = _G.number_of_edges(e[1], e[0])
            ax.annotate("",
                        xy=pos[e[0]],
                        xycoords='data',
                        xytext=pos[e[1]],
                        textcoords='data',
                        alpha=0.5,
                        arrowprops=dict(arrowstyle="<-",
                                        color="0",
                                        alpha=0.5,
                                        shrinkA=20,
                                        shrinkB=20,
                                        patchA=None,
                                        patchB=None,
                                        connectionstyle=
                                        "arc3, rad = rrr".replace('rrr', str(0.3 * e[2])), ), )
        plt.axis('off')

        nx.draw_networkx_edge_labels(_G, pos=pos, edge_labels=edge_labels, label_pos=0.2, font_size=8)

        plt.title("Service chains of cluster " + self.name)
        plt.legend(handles=[Line2D([0], [0], marker='o', label='Microservice endpoint function', color='w',
                                   markerfacecolor=function_color),
                            Line2D([0], [0], marker='o', label='Load generator (SFC name)', color='w',
                                   markerfacecolor=scm_color)])

        if save_dir is not None:
            Utils.mkdir_p(save_dir)
            plt.savefig(save_dir + "/service_chains.pdf")

        if show:
            plt.show()
        else:
            plt.close()

    def calculate_average_latency_in_seconds(self):
        """
        Calculate the average latency in seconds

        :return: The average latency in seconds
        """

        all_latencies = self.sim.load_generator.latencies["latency"]
        return all_latencies.mean() / 10 ** 9

    def print_and_plot_scenarios(self, printing: bool = True, plotting: bool = True):
        """
        Print and plot the scenarios

        :param printing:
        :param plotting:
        :return:
        """

        host_count = str(len(self.topology.hosts_dict))
        avg_latencies = self.calculate_average_latency_in_seconds()

        if printing:
            print("Average latency with " + host_count + " hosts: " + str(avg_latencies) + "s")

        if plotting:
            folder_name = "results/" + host_count + "_hosts"
            self.sim.load_generator.plot_latencies(save_dir=folder_name, marker='o', moving_average=True,
                                                   save_values=False, show=False)
            self.topology.draw(save_dir=folder_name, show=False)
            self.draw_all_service_chains(save_dir=folder_name, show=False)
            self.plot_hosts_cpu_heatmaps(save_dir=folder_name + "/cpu", show=False)

    def plot_hosts_cpu_heatmaps(self, save_dir: str = None, show: bool = True):
        """
        Plot the hosts' CPU heatmaps

        :param save_dir: The directory to save the heatmaps
        :param show:  Whether to show the heatmaps or not
        :return:  None
        """

        for host in self.cluster_scheduler.hosts_dict.values():
            host.cpu.plot(save_dir=save_dir, show=show)
