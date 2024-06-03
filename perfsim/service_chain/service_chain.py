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
from typing import List, Dict, Union, Tuple

import networkx as nx

from perfsim import MicroserviceEndpointFunction, Microservice, ServiceChainLink


class ServiceChain(nx.MultiDiGraph):
    """
    This class represents a service chain.
    """

    #: microservices_dict is a dictionary of microservices in the service chain
    microservices_dict: Dict[str, Microservice]

    def __init__(self,
                 name: str,
                 nodes: List[MicroserviceEndpointFunction] = None,
                 edges: List[ServiceChainLink] = None,
                 incoming_graph_data=None,
                 **attr):
        super().__init__(incoming_graph_data, **attr)
        self.microservices_dict = {}
        self.name = name
        if nodes is not None:
            self.add_nodes_from(nodes)
        if edges is not None:
            self.add_edges_from(edges)

    def add_nodes_from(self, nodes_for_adding: List[MicroserviceEndpointFunction], **attr):
        """
        Add nodes from a list of nodes.

        :param nodes_for_adding: The list of nodes to add.
        :param attr: The attributes to add to the nodes.
        :return:  None
        """

        if "validate_before_adding" not in attr or attr["validate_before_adding"]:
            for _node in nodes_for_adding:
                self._validate_node(node=_node)

        super().add_nodes_from(nodes_for_adding=nodes_for_adding, **attr)

        for _node in nodes_for_adding:
            self.microservices_dict[_node.microservice.name] = _node.microservice

    def add_edges_from(self, ebunch_to_add: List[ServiceChainLink], **attr):
        """
        Add edges from a list of edges.

        :param ebunch_to_add:
        :param attr:
        :return:
        """

        edges = [(edge.source, edge.destination, edge_id, {"payload": edge.request_size, "name": edge.name})
                 for edge_id, edge in enumerate(ebunch_to_add)]
        super().add_edges_from(edges, **attr)

    def add_node(self, node_for_adding, **attr):
        """
        Add a node to the service chain.

        :param node_for_adding:
        :param attr:
        :return:
        """

        if "validate_before_adding" not in attr or attr["validate_before_adding"]:
            self._validate_node(node_for_adding)

        super().add_node(node_for_adding, **attr)

        self.microservices_dict[node_for_adding.microservice.name] = node_for_adding.microservice

    @staticmethod
    def _validate_node(node):
        """
        Validate a node.

        :param node: The node to validate.
        :return: True if the node is valid, False otherwise.
        """

        if not isinstance(node, MicroserviceEndpointFunction):
            raise Exception("Node should of type MicroserviceEndpointFunction!")
        else:
            return True

    @staticmethod
    def copy_to_dict(service_chains: Union[List[ServiceChain], Dict[str, ServiceChain]]) \
            -> Tuple[Dict[str, ServiceChain], Dict[str, Microservice]]:
        """
        Copy service chains to a dictionary.

        :param service_chains:
        :return:
        """

        if isinstance(service_chains, dict):
            service_chains_dict = deepcopy(service_chains)
        else:
            service_chains_dict = {}
            for service_chain in service_chains:
                service_chains_dict[service_chain.name] = deepcopy(service_chain)

        ms_dict = {}

        for service_chain in service_chains_dict.values():
            ms_dict = ms_dict | service_chains_dict[service_chain.name].microservices_dict

        return service_chains_dict, ms_dict

    # TODO: functools.singledispatchmethod has a bug, hopefully it'll be fixed in Python 3.11!
    @staticmethod
    def microservices_to_dict_from_list(service_chains: list[ServiceChain]) -> dict[str, Microservice]:
        """
        Convert a list of service chains to a dictionary of microservices.

        :param service_chains: The list of service chains.
        :return:  The dictionary of microservices.
        """

        ms_dict = {}

        for service_chain in service_chains:
            ms_dict = ms_dict | service_chain.microservices_dict

        return ms_dict

    @staticmethod
    def microservices_to_dict_from_dict(service_chains: dict[str, ServiceChain]) -> dict[str, Microservice]:
        """
        Convert a dictionary of service chains to a dictionary of microservices.

        :param service_chains:  The dictionary of service chains.
        :return: The dictionary of microservices.
        """

        ms_dict = {}

        for service_chain_name, service_chain in enumerate(service_chains.values()):
            ms_dict = ms_dict | service_chain.microservices_dict

        return ms_dict

    @staticmethod
    def from_config(conf: dict, microservice_prototypes_dict) -> dict[str, ServiceChain]:
        """
        Create a service chain from a configuration.

        :param conf:
        :param microservice_prototypes_dict:
        :return:
        """

        service_chains_dict = {}
        microservices_dict = {}

        for _sfc_id, _sfc_name in enumerate(conf):
            _sfc_nodes = {}
            _sfc_edges = []

            for _node_index in conf[_sfc_name]["nodes"]:
                _node_data = conf[_sfc_name]["nodes"][_node_index]
                _node_application_name = _node_data["microservice"]
                _node_endpoint_function_name = _node_data["endpoint"]

                if _node_application_name not in microservices_dict.keys():
                    _microservice_prototype = microservice_prototypes_dict[_node_application_name]
                    _ms = Microservice.from_prototype(name=_node_application_name, prototype=_microservice_prototype)
                    microservices_dict[_node_application_name] = _ms

                _node = microservices_dict[_node_application_name].endpoint_functions[_node_endpoint_function_name]
                _sfc_nodes[_node_index] = _node

            for _edge_name in conf[_sfc_name]["edges"]:
                _edge_data = conf[_sfc_name]["edges"][_edge_name]
                _request_size = _edge_data["request_size"]
                _source_index = _edge_data["connection"][0]
                _destination_index = _edge_data["connection"][1]
                _source = _sfc_nodes[_source_index]
                _dest = _sfc_nodes[_destination_index]
                _edge = ServiceChainLink(name=_edge_name, request_size=_request_size, source=_source, dest=_dest)
                _sfc_edges.append(_edge)

            _nodes = list(_sfc_nodes.values())
            _edges = _sfc_edges
            _sfc = ServiceChain(name=_sfc_name)
            _sfc.add_nodes_from(nodes_for_adding=_nodes)
            _sfc.add_edges_from(ebunch_to_add=_edges)
            service_chains_dict[_sfc_name] = _sfc

        return service_chains_dict
