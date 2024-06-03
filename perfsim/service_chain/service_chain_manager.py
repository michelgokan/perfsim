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

from typing import Dict, Tuple, List

import networkx as nx
from networkx import DiGraph

from perfsim import ServiceChain, MicroserviceEndpointFunction, Plotter


class ServiceChainManager:
    #: The alternative graph for the service chain, with nodes as a tuple of (node number, MicroserviceEndpointFunction)
    alternative_graph: DiGraph

    #: The last node in the service chain for drawing purposes (LatEx)
    __node_labels_map: Dict[Tuple[int, MicroserviceEndpointFunction], str]

    #: The service chain manager name
    name: str

    #: List of subchains (index as subchain ID) including their nodes as list of tuples
    subchains: List[List[Tuple[int, MicroserviceEndpointFunction]]]

    #: Dictionary of subchain IDs (as values) and tuple of (node number, MicroserviceEndpointFunction) as keys
    node_subchain_id_map: Dict[Tuple[int, MicroserviceEndpointFunction], int]

    #: The root node of the service chain
    __root: Tuple[int, MicroserviceEndpointFunction]

    def __init__(self, name: str, service_chain: ServiceChain):
        self.__node_labels_map = {}
        self.alternative_graph = nx.DiGraph()
        self.service_chain = service_chain

        if len(self.service_chain.nodes) == 0:
            raise Exception("Error: service chain length can't be zero!")

        self.name = name
        # self.requests = []
        self.subchains = []
        self.node_subchain_id_map = {}
        # self.__current_subchain_id = 0
        self.generate_alternative_graph()
        self.extract_subchains(list(self.alternative_graph.nodes)[0], 0)
        # self.root = [n for n, d in self.alternative_graph.in_degree if d == 0][0]
        for node, in_degree in self.alternative_graph.in_degree:
            if in_degree == 0:
                self.__root = node
                break
        # self.root = [n for n, d in self.alternative_graph.in_degree if d == 0][0]
        # self.subchains_count = len(self.subchains)

    @property
    def root(self):
        return self.__root

    @root.setter
    def root(self, root: Tuple[int, MicroserviceEndpointFunction]):
        raise Exception("Error: root can't be set in service chain manager! It's set automatically in initialization.")

    def generate_alternative_graph(self):
        # nx.draw(self.service_chain)
        # plt.show()
        self.subchains = [[]]
        node_replicas_index1 = {}
        node_replicas_index2 = {}
        current_node_out_index = {}
        self.__node_labels_map = {}
        node_counter = 0

        for node, node_data in self.service_chain.nodes(data=True):
            _in_degree = self.service_chain.in_degree(node)

            if node_counter == 0:
                node_replicas_index1[str(node)] = 1
                node_replicas_index2[str(node)] = 1
                current_node_out_index[str(node)] = 0
                _in_degree += 1
            else:
                node_replicas_index1[str(node)] = 0
                node_replicas_index2[str(node)] = 0
                current_node_out_index[str(node)] = -1

            _counter = 0
            while True:
                node_to_add = (_counter, node)
                self.alternative_graph.add_node(node_to_add, **node_data)
                self.__node_labels_map[node_to_add] = r'${' + str(node).replace("_", "-") + '}_' + str(_counter) + '$'

                _counter += 1
                _in_degree -= 1
                if _in_degree < 1:
                    break

            # if _in_degree < 2:
            #     node_to_add = (0, node)
            #     self.alternative_graph.add_node(node_to_add, **node_data)
            #     self.__node_labels_map[node_to_add] = r'${' + str(node).replace("_", "-") + '}_0$'
            # else:
            #     while _in_degree >= 1:
            #         node_to_add = (_counter, node)
            #         self.alternative_graph.add_node(node_to_add, **node_data)
            #         self.__node_labels_map[node_to_add] = \
            #             r'${' + str(node).replace("_", "-") + '}_' + str(_counter) + '$'
            #         _in_degree -= 1
            #         _counter += 1
            #         node_replicas[str(node)] += 1
            node_counter += 1

        nodes = []
        all_edges = sorted(list(self.service_chain.edges), key=lambda x: x[2])

        for edge in all_edges:

            if (current_node_out_index[str(edge[0])], edge[0]) not in nodes:
                nodes.append((current_node_out_index[str(edge[0])], edge[0]))

            a = node_replicas_index1[str(edge[1])]
            if (node_replicas_index1[str(edge[1])], edge[1]) not in nodes:
                nodes.append((node_replicas_index1[str(edge[1])], edge[1]))
                node_replicas_index1[str(edge[1])] += 1
                current_node_out_index[str(edge[1])] += 1

            edge_data = self.service_chain.get_edge_data(u=edge[0], v=edge[1], key=edge[2])
            self.alternative_graph.add_edge(
                (current_node_out_index[str(edge[0])], edge[0]),
                (a, edge[1]), **edge_data)

        # for node in nodes:
        #     _out_edges = sorted(list(self.service_chain.out_edges(node, keys=True)), key=lambda x: x[2])
        #
        #     for out_edge in _out_edges:
        #         edge_data = self.service_chain.get_edge_data(out_edge[0], out_edge[1], out_edge[2])
        #         self.alternative_graph.add_edge(
        #             (node_replicas_index2[str(out_edge[0])], out_edge[0]),
        #             (node_replicas_index2[str(out_edge[1])], out_edge[1]), **edge_data)
        #         node_replicas_index2[str(out_edge[1])] += 1

    def extract_subchains(self, current_node, subchain_id, append=False):
        successors = list(self.alternative_graph.successors(current_node))
        successors_count = len(successors)

        if append or subchain_id >= len(self.subchains):
            self.subchains.append([])
            subchain_id = len(self.subchains) - 1

        self.subchains[subchain_id].append(current_node)
        self.node_subchain_id_map[current_node] = subchain_id

        if successors_count == 0:
            return
        elif successors_count == 1:
            self.extract_subchains(current_node=successors[0], subchain_id=subchain_id)
        else:
            for s in successors:
                self.extract_subchains(current_node=s, subchain_id=subchain_id + 1, append=True)

    def draw_service_chain(self, save_dir: str = None, with_labels: bool = False):
        return Plotter.draw_graph(G=self.get_copy(self.service_chain),
                                  # node_labels_map=self.__node_labels_map,
                                  name=str(self),
                                  save_dir=save_dir,
                                  output_type="html",
                                  with_labels=with_labels)

    def draw_alternative_graph(self, save_dir: str = None, with_labels: bool = False, relabel: bool = False):
        return Plotter.draw_graph(G=self.alternative_graph,
                                  # node_labels_map=self.__node_labels_map,
                                  name=str(self),
                                  save_dir=save_dir,
                                  output_type="html",
                                  with_labels=with_labels,
                                  relabel=relabel)

    @staticmethod
    def get_copy(G):
        _G = nx.MultiDiGraph()
        _edges = []

        for node in G.nodes:
            _G.add_node(node)

        for edge in G.edges:
            edge_data = G.get_edge_data(u=edge[0], v=edge[1])
            _edges.append((edge[0], edge[1], edge_data if len(edge_data) > 0 else None))

        _G.add_edges_from(ebunch_to_add=_edges)
        return _G

    def __str__(self):
        return self.name
