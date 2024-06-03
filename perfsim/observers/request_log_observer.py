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

from typing import Tuple, List, Union, TYPE_CHECKING

from perfsim import Event, LogObserver

if TYPE_CHECKING:
    from perfsim import Request, MicroserviceReplica, Request, MicroserviceEndpointFunction, MicroserviceReplica


class RequestLogObserver(LogObserver):
    def __init__(self, request: 'Request'):
        super().__init__(name="RequestLogObserver", subject=request, logger=request.load_generator.sim.logger)

    @Event
    def before_init_next_microservices(self,
                                       subchain_id: int,
                                       next_nodes: List[Union[None, Tuple[int, 'MicroserviceEndpointFunction']]]):
        if self.subject.load_generator.sim.debug:
            if self.subject.current_nodes[subchain_id] is None:
                current_node = "None"
            else:
                current_node = str(self.subject.current_nodes[subchain_id][1])

            self.logger.log("- Initializing next microservices for request #" + str(self) + " in scm #" +
                            str(self.subject.scm.name), 3)
            # self.cluster.print_log(" * Active subchain IDs are " + str(self.active_subchain_ids), 3)
            self.logger.log(" * For subchain ID: " + str(subchain_id), 3)

            # if self.is_last_microservice_running():
            #     self.cluster.print_log(" * No microservice left!", 3)
            #     return False
            # else:
            self.logger.log(" * Looking inside subchain #" + str(subchain_id), 3)

            next_nodes_in_subchain = str(next_nodes) if self.subject.current_nodes[subchain_id] is not None else "root"

            self.logger.log("  ** Current node in subchain are " + current_node, 3)
            self.logger.log("  ** Next nodes in subchain are " + str(next_nodes_in_subchain), 3)

            if self.subject.current_replicas_in_nodes[subchain_id] is None:
                self.logger.log("  ** Current replicas for subchain id " + str(subchain_id) + " is not set!", 3)
            else:
                self.logger.log("  ** Current replicas for subchain id " + str(subchain_id) + " are " +
                                str(self.subject.current_replicas_in_nodes[subchain_id]), 3)

            self.logger.log("  *** Setting transmission init time to " + str(self.subject.load_generator.sim.time), 3)

            self.logger.log("  *** Setting status of subchain to IN TRANSMISSION", 3)

            self.print_current_and_next_nodes_and_replicas()

    def print_current_and_next_nodes_and_replicas(self):
        self.logger.log(" * Setting current_replicas_in_nodes to next_replicas_in_nodes", 3)
        self.logger.log("  ** Current replicas = " + str(self.subject.get_current_replicas_names()), 3)
        self.logger.log("   *** Current replicas hosts: " + str(self.subject.get_current_replicas_host_names()), 3)
        self.logger.log("  ** Next replicas = " + str(self.subject.get_next_replicas_names()), 3)
        self.logger.log("   *** Next replicas hosts: " + str(self.subject.get_next_replicas_host_names()), 3)
        self.logger.log("  ** Now, current replicas will be replaces by the next replicas", 3)

    @Event
    def after_init_next_microservices(self,
                                      subchain_id: int,
                                      replicas: List[Union[None, Tuple[int, 'MicroserviceReplica']]]):
        if self.subject.load_generator.sim.debug:
            self.logger.log(" * Request #" + str(self.subject) + " in subchain id " + str(subchain_id) +
                            " reached replicas " + self.subject.get_current_replicas_names()[subchain_id], 3)

            self.print_current_and_next_nodes_and_replicas()

    @Event
    def before_finalizing_subchain(self, subchain_id: int):
        if self.subject.load_generator.sim.debug:
            self.logger.log(" * Finalizing subchain #" + str(subchain_id) + " in scm #" +
                            str(self.subject.scm.name) + " in request #" + str(self), 3)

    @Event
    def before_concluding_request(self):
        if self.subject.load_generator.sim.debug:
            self.logger.log("- All subchains are done! Concluding request #" + str(self.subject))

    @Event
    def before_init_transmission(self,
                                 node: Tuple[int, 'MicroserviceEndpointFunction'],
                                 next_nodes: List[Tuple[int, 'MicroserviceEndpointFunction']]):
        if self.subject.load_generator.sim.debug:
            subchain_id = self.subject.scm.node_subchain_id_map[node]
            current_replica_of_node = self.subject.current_replicas_in_nodes[subchain_id]
            replica_name = "(" + str(current_replica_of_node[0]) + "," + str(current_replica_of_node[1]) + ")"
            host_name = str(current_replica_of_node[1].host)
            current_replicas_host_names = self.subject.get_current_replicas_host_names()
            current_replicas_names = self.subject.get_current_replicas_names()
            current_node_names = self.subject.get_node_names()

            self.logger.log(" * Node (" + str(node[0]) + ", " + str(node[1]) + ") belonging to request " + str(self) +
                            " is done. Initializing transmission to next node...", 3)

            self.logger.log("")
            self.logger.log("<<< INITIATING A SET OF TRANSMISSIONS >>>")
            self.logger.log(" * Initiating a set of transmissions in scm #" + str(self.subject.scm.name) +
                            " from replica #" + str(replica_name) + " of microservice " + str(node[1]) + " in host " +
                            host_name + " belonging to request #" + str(self), 3)
            self.logger.log("  ** Compute time for current node=" + str(self.subject.compute_times[subchain_id][-1]), 3)

            if len(next_nodes) == 0:
                self.logger.log("  ** There is no next node in subchain #" + str(subchain_id) +
                                "! Finalizing subchain!", 3)
            else:
                next_nodes_names = self.subject.get_next_nodes_names(next_nodes)
                next_replicas_names = self.subject.get_next_replicas_names()
                next_replicas_host_names = self.subject.get_next_replicas_host_names()

                self.logger.log("  ** Setting next nodes to ->" + str(next_nodes_names), 3)
                self.logger.log("  ** Current nodes = ->" + str(current_node_names), 3)
                self.logger.log("  ** Setting next replicas to ->" + str(next_replicas_names), 3)
                self.logger.log("  ** Current replicas =" + str(current_replicas_names), 3)
                self.logger.log("  ** Current replicas host names =" + str(current_replicas_host_names), 3)
                self.logger.log("  ** Next replicas host names =" + str(next_replicas_host_names), 3)

    @Event
    def on_init_transmission(self,
                             current_node: Tuple[int, 'MicroserviceEndpointFunction'],
                             next_node: Tuple[int, 'MicroserviceEndpointFunction'],
                             current_replica: Tuple[int, 'MicroserviceReplica'],
                             next_replica: Tuple[int, 'MicroserviceReplica']):
        if self.subject.load_generator.sim.debug:
            next_subchain_id = self.subject.scm.node_subchain_id_map[next_node]

            self.logger.log("   *** Current node's replica is #" + str(current_replica[1]) + " in subchain ID " +
                            str(current_replica[0]) + ")", 3)
            self.logger.log("   *** Next node's replica is #" + str(next_replica[1]) + " in subchain ID " +
                            str(next_replica[0]) + ")", 3)
            self.logger.log("    **** Reserving transmission bandwidth in the NIC of host " +
                            str(current_replica[1].host), 3)
            self.logger.log("       ****** Setting current_replicas_in_nodes of node (" + str(next_node[0]) + ", " +
                            str(next_node[1]) + ") in subchain id " + str(next_subchain_id) + " of request " +
                            str(self.subject.id_in_cpu) + " to (" +
                            str(self.subject.next_replicas_in_nodes[next_subchain_id][0]) +
                            ", " + str(self.subject.next_replicas_in_nodes[next_subchain_id][1]) + ")", 3)

            if self.subject.current_nodes[next_subchain_id] is None:
                current_node_to_log = "None"
            else:
                current_node_to_log = "(" + str(self.subject.current_nodes[next_subchain_id][0]) + "," + \
                                      str(self.subject.current_nodes[next_subchain_id][1]) + ")"

            if self.subject.current_replicas_in_nodes[next_subchain_id] is None:
                current_replica_to_log = "None"
            else:
                current_replica_to_log = "(" + str(self.subject.current_replicas_in_nodes[next_subchain_id][0]) + \
                                         "," + str(self.subject.current_replicas_in_nodes[next_subchain_id][1]) + ")"

            self.logger.log("       ****** Replacing current_node " + current_node_to_log + " in subchain id " +
                            str(next_subchain_id) + " with (" + str(self.subject.next_nodes[next_subchain_id][0]) +
                            ", " + str(self.subject.next_nodes[next_subchain_id][1]) + ")", 3)

            self.logger.log("       ****** Replacing current_replicas_in_nodes " + current_replica_to_log +
                            " in subchain id " + str(next_subchain_id) + " with (" +
                            str(self.subject.next_replicas_in_nodes[next_subchain_id][0]) + ", " +
                            str(self.subject.next_replicas_in_nodes[next_subchain_id][1]) + ")", 3)

    @Event
    def after_init_transmission(self, node: Tuple[int, 'MicroserviceEndpointFunction']):
        if self.subject.load_generator.sim.debug:
            self.logger.log("<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>", 2)
            self.logger.log("", 2)

    @Event
    def before_finish_transmission(self, node: Tuple[int, 'MicroserviceEndpointFunction']):
        if self.subject.load_generator.sim.debug:
            self.logger.log("", 2)
            self.logger.log("### FINISHING A SINGLE TRANSMISSIONS ###", 2)

    @Event
    def after_finish_transmission(self, node: Tuple[int, 'MicroserviceEndpointFunction']):
        if self.subject.load_generator.sim.debug:
            node_subchain_id = self.subject.scm.node_subchain_id_map[node]
            active_replica_in_subchain = self.subject.current_replicas_in_nodes[node_subchain_id]
            replica_name = "(" + str(active_replica_in_subchain[0]) + "," + str(active_replica_in_subchain[1]) + ")"

            self.logger.log(" * Finishing a transmission in scm #" + str(self.subject.scm.name) + " related to "
                                                                                                  "replica #" + str(
                replica_name) + " of " + "microservice " + str(node[1]) + " in host " +
                            str(active_replica_in_subchain[1].host) + " belonging to request #" + str(self) +
                            " (delta time=" + str(self.subject.trans_deltatimes[node_subchain_id]) + ")", 3)
            self.logger.log("########################################", 2)
            self.logger.log("", 2)
