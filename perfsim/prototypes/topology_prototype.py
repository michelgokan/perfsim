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

from copy import deepcopy
from typing import Union, List, Dict, Set

import networkx as nx

from perfsim import Host, Router, MicroserviceReplica, Transmission, TopologyLink, Plotter


class TopologyPrototype(nx.MultiDiGraph):
    hosts_dict: Dict[str, Host]
    routers_dict: Dict[str, Router]
    topology_links_dict: Dict[str, TopologyLink]

    """
    In Kubernetes, we noticed a slight error between desired and actual egress_bandwidths. For example, 
    if we set egress_bandwidth of a pod to 100Mbps, it gets slightly lower bandwidth (~95Mbps - error = 0.05 = 5%). 
    We call this slight error as egress_err. Use 0.05 if you want to indicate an error of 5%. 
    """
    egress_err: float

    """
    In Kubernetes, we noticed a slight error between desired and actual ingress_bandwidths. For example, 
    if we set ingress_bandwidth of a pod to 100Mbps, it gets slightly lower bandwidth (~95Mbps - error = 0.05 = 5%). 
    We call this slight error as ingress_err. Use 0.05 if you want to indicate an error of 5%. 
    """
    ingress_err: float

    active_transmissions: Set[Transmission]

    before_recalculate_transmissions_bw_on_all_links: str

    def __init__(self,
                 name: str,
                 egress_err: float,
                 ingress_err: float,
                 incoming_graph_data=None,
                 hosts: Dict[str, Host] = None,
                 routers: Dict[str, Router] = None,
                 links: Dict[str, TopologyLink] = None,
                 **attr):
        super().__init__(incoming_graph_data, **attr)
        self.incoming_graph_data = incoming_graph_data
        self.attr = attr
        self.name = name
        self.egress_err = egress_err
        self.ingress_err = ingress_err
        self.hosts_dict = {}
        self.routers_dict = {}
        self.topology_links_dict = {}
        self.active_transmissions = set()
        self.active_edges = set()
        self.zombie_edges = set()
        if hosts is not None and routers is not None:
            self.add_equipments(hosts=hosts, routers=routers)
        if links is not None:
            self.add_edges_from(links)

    def add_equipments(self, hosts: Dict[str, Host], routers: Dict[str, Router], **attr):
        self.hosts_dict = hosts
        self.routers_dict = routers

        hosts_for_adding: list = list(self.hosts_dict.values())
        routers_for_adding: list = list(self.routers_dict.values())
        nodes_for_adding = hosts_for_adding + routers_for_adding
        super().add_nodes_from(nodes_for_adding=nodes_for_adding, **attr)

    def add_edges_from(self, ebunch_to_add: dict[str, TopologyLink], **attr):
        edges = []
        for edge in ebunch_to_add.values():
            if edge.source not in self.nodes or edge.destination not in self.nodes:
                raise Exception("Source or Destination of an edge in this topology (" + str(self.name) +
                                ") is not in the graph!")

            edges.append((edge.source, edge.destination, {"name": edge.name,
                                                          "latency": edge.latency,
                                                          "transmissions_portion_of_bandwidth": None,
                                                          "transmissions": set()}))
            self.topology_links_dict[edge.name] = edge

        super().add_edges_from(edges, **attr)
        self.reinitiate_topology()

    def add_edge(self, u_for_edge, v_for_edge, key=None, **attr):
        if isinstance(u_for_edge, Host):
            if not isinstance(v_for_edge, Router):
                raise Exception(f"Can't connect host {u_for_edge} to an object of type "
                                f"{type(v_for_edge).__name__}. A host can only be connected to a Router "
                                f"object!")

            v_for_edge.connect_host(u_for_edge)
        elif isinstance(u_for_edge, Router) and isinstance(v_for_edge, Router):
            v_for_edge.connect_router(router=u_for_edge)
        # else:
        #     raise Exception(f"Something is wrong adding edge to topology {self.name}!")

        return super().add_edge(u_for_edge=u_for_edge, v_for_edge=v_for_edge, key=key, **attr)

    def reinitiate_topology(self):
        for edge in self.edges:
            edge_data = self.get_edge_data(edge[0], edge[1])[0]
            if edge_data["transmissions_portion_of_bandwidth"] is None:
                edge_data["transmissions_portion_of_bandwidth"] = Transmission.get_bandwidth_on_link(edge[0], edge[1])

    def draw(self, show_microservices: bool = True, save_dir: str = None, show: bool = False, type: str = "html"):
        if show_microservices:
            _replica_list = []
            _G = nx.MultiDiGraph()
            _edges = []

            for edge in self.edges:
                edge_data = self.get_edge_data(u=edge[0], v=edge[1])[0]
                _edges.append((edge[0], edge[1], edge_data))

            _G.add_edges_from(ebunch_to_add=_edges)

            # _G = self.copy()
            # _G.__class__ = nx.MultiDiGraph

            for node in self.nodes:
                if isinstance(node, Host):
                    for replica in node.replicas:
                        _replica_list.append((node, replica))

            for _tuple in _replica_list:
                host = _tuple[0] if isinstance(_tuple[0], Host) else _tuple[1]
                replica = _tuple[1] if isinstance(_tuple[1], MicroserviceReplica) else _tuple[0]

                host_to_replica_bw = min(host.nic["egress"].bandwidth, replica.process.ingress_bw)
                replica_to_host_bw = min(replica.process.egress_bw, host.nic["ingress"].bandwidth)

                _G.add_edge(host, replica, name="", bandwidth=str(host_to_replica_bw))
                _G.add_edge(replica, host, name="", bandwidth=str(replica_to_host_bw))
        else:
            _G = self
        return Plotter.draw_graph(_G, name=self.name, save_dir=save_dir, show=show)

    # def recalculate_transmissions_time_on_all_links(self):
    #     for edge in self.edges:
    #         self.recalculate_transmissions_time_on_link(edge)

    @staticmethod
    def recalculate_transmissions_times(transmissions: Set[Transmission]):
        # edge_data = self.get_edge_data(link[0], link[1])[0]
        for trans in transmissions:
            prev_trans_exact_time = trans.transmission_exact_time
            trans.calculate_transmission_time()

            if trans.transmission_exact_time != prev_trans_exact_time:
                # TODO: Is there any way to merge this with request's recalculate_transmission_times ?
                request = trans.subchain_id_request_pair[0]
                subchain_id = trans.subchain_id_request_pair[1]
                load_generator = trans.src_replica.host.cluster.sim.load_generator
                # request.transmission_times[subchain_id] = transmission.calculate_transmission_time()
                request.trans_times[subchain_id] = trans.transmission_time
                request.trans_exact_times[subchain_id] = trans.transmission_exact_time

                prev_trans_from_sorted_dict = load_generator.next_trans_completion_times.get(prev_trans_exact_time)
                trans_from_sorted_dict = load_generator.next_trans_completion_times.get(trans.transmission_exact_time)

                if prev_trans_from_sorted_dict is not None and prev_trans_from_sorted_dict["counter"] > 1:
                    prev_trans_from_sorted_dict["counter"] -= 1
                else:
                    load_generator.next_trans_completion_times.pop(prev_trans_exact_time, 0)

                load_generator.next_trans_completion_times.update(
                    {trans.transmission_exact_time: {
                        "counter": trans_from_sorted_dict["counter"] + 1 if trans_from_sorted_dict is not None else 1
                    }})

    @staticmethod
    def copy_to_dict(topology_prototypes: Union[List[TopologyPrototype], Dict[str, TopologyPrototype]]) \
            -> Dict[str, TopologyPrototype]:
        if isinstance(topology_prototypes, dict):
            return deepcopy(topology_prototypes)
        else:
            topology_prototypes_dict = {}

            for topology_prototype in topology_prototypes:
                topology_prototypes_dict[topology_prototype.name] = deepcopy(topology_prototype)

            return topology_prototypes_dict

    @staticmethod
    def from_config(conf: dict, topology_equipments_dict, link_prototypes_dict) -> Dict[str, TopologyPrototype]:
        topology_prototypes_dict = {}

        for _topology_id, _topology_name in enumerate(conf):
            _topology_nodes = {}
            _hosts_nodes = {}
            _routers_nodes = {}
            _topology_edges = {}

            for _node_index in conf[_topology_name]["nodes"]:
                _node_data = conf[_topology_name]["nodes"][_node_index]
                _node_name = _node_data["name"]

                if _node_data["type"] == "router":
                    _topology_nodes[_node_index] = topology_equipments_dict[_topology_name]["routers"][_node_name]
                    _routers_nodes[_node_index] = topology_equipments_dict[_topology_name]["routers"][_node_name]
                elif _node_data["type"] == "host":
                    _topology_nodes[_node_index] = topology_equipments_dict[_topology_name]["hosts"][_node_name]
                    _hosts_nodes[_node_index] = topology_equipments_dict[_topology_name]["hosts"][_node_name]
                else:
                    raise Exception("Node type is not defined in topology " + str(_topology_name))

            for _edge_name in conf[_topology_name]["edges"]:
                _link_data = conf[_topology_name]["edges"][_edge_name]
                _link_type = _link_data["link_type"]
                _link_prototype = link_prototypes_dict[_link_type]
                _source_index = _link_data["connection"][0]
                _destination_index = _link_data["connection"][1]
                _src = _topology_nodes[_source_index]
                _dest = _topology_nodes[_destination_index]
                _link = TopologyLink.from_prototype(name=_edge_name, prototype=_link_prototype, src=_src, dest=_dest)
                _topology_edges[_link.name] = _link

            _nodes = list(_topology_nodes.values())
            # _edges = [(edge.source, edge.destination) for edge in _topology_edges]
            _tau = TopologyPrototype(name=_topology_name,
                                     egress_err=float(conf[_topology_name]["egress_err"]),
                                     ingress_err=float(conf[_topology_name]["ingress_err"]))
            _tau.add_equipments(hosts=_hosts_nodes, routers=_routers_nodes)
            _tau.add_edges_from(ebunch_to_add=_topology_edges)
            topology_prototypes_dict[_topology_name] = _tau

        return topology_prototypes_dict
