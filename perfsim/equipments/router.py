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

from typing import TYPE_CHECKING, Dict

from perfsim import RouterPrototype, Nic, Equipment

if TYPE_CHECKING:
    from perfsim import Cluster, Host


class Router(RouterPrototype, Equipment):
    """
    This class represents a router in a network. A router is a device that forwards data packets between computer
    networks. It has a latency and a bandwidth that it can support.
    """

    #: The dictionary of hosts that are connected to this router. The key is the host object and the value is the port
    #: number on the router that the host is connected to.
    hosts: dict[Host, int]

    #: The dictionary of routers that are connected to this router. The key is the router object and the value is the port
    #: number on the router that the router is connected to.
    routers: dict[Router, int]

    #: The dictionary of NICs that are connected to this router. The key is the port number on the router and the value
    #: is a dictionary with the keys "egress" and "ingress" and the values are the NIC objects.
    nics: dict[int, dict[str, Nic]]

    def __init__(self, name: str, latency: int, egress_ingress_bw: int, ports_count: int, cluster: Cluster):
        if ports_count <= 0:
            raise Exception("Can't have zero or negative ports in a router!")

        super().__init__(name=name, latency=latency, egress_ingress_bw=egress_ingress_bw, ports_count=ports_count)
        self.name = name
        self.cluster = cluster
        # self.active_nics = 0
        self.hosts = {}
        self.routers = {}
        self.nics = {}

        for i in range(ports_count):
            self.nics[i] = {
                "egress": Nic(name=name + "_nic" + str(i) + "_egress", bandwidth=egress_ingress_bw, equipment=self),
                "ingress": Nic(name=name + "_nic" + str(i) + "_ingress", bandwidth=egress_ingress_bw, equipment=self)
            }

    def get_nics_by_host(self, host: Host) -> dict[str, Nic]:
        """
        Get the NICs that are connected to the given host.

        :param host:
        :return:
        """

        return self.nics[self.hosts[host]]

    def get_nics_by_router(self, router: Router) -> dict[str, Nic]:
        """
        Get the NICs that are connected to the given router.

        :param router:
        :return:
        """

        return self.nics[self.routers[router]]

    def connect_router(self, router: Router, connect_other_pair: bool = True):
        """
        Connect this router to another router.

        :param router:
        :param connect_other_pair:
        :return:
        """

        if len(self.hosts) + len(self.routers) >= self.ports_count:
            raise Exception(f"Can not connect host {router.name} to router {self.name}!")

        self.routers[router] = len(self.hosts) + len(self.routers)

        if connect_other_pair:
            router.connect_router(router=self, connect_other_pair=False)

    def disconnect_router(self, router: Router, suppress_error: bool = False, disconnect_other_pair: bool = True):
        """
        Disconnect this router from another router.

        :param router:
        :param suppress_error:
        :param disconnect_other_pair:
        :return:
        """

        try:
            self.routers.pop(router)
        except KeyError:
            if not suppress_error:
                raise KeyError(
                    f"Router {router} is not connected to router {self.name}! There is nothing to disconnect.")

        if disconnect_other_pair:
            router.disconnect_router(router=self, disconnect_other_pair=False)

    def connect_host(self, host: Host):
        """
        Connect this router to a host.

        :param host:
        :return:
        """

        if len(self.hosts) + len(self.routers) >= self.ports_count:
            raise Exception(f"Can not connect host {host.name} to router {self.name}!")

        self.hosts[host] = len(self.hosts) + len(self.routers)
        host.router = self

    def disconnect_host(self, host: Host, suppress_error: bool = False):
        """
        Disconnect this router from a host.

        :param host:
        :param suppress_error:
        :return:
        """

        try:
            self.hosts.pop(host)
        except KeyError:
            if not suppress_error:
                raise KeyError(f"Host {host} is not connected to router {self.name}! There is nothing to disconnect.")

        host.router = None

    @classmethod
    def from_router_prototype(cls, name: str, router_prototype: RouterPrototype, cluster: Cluster = None):
        """
        Create a router from a router prototype.

        :param name:
        :param router_prototype:
        :param cluster:
        :return:
        """

        return cls(name=name,
                   latency=router_prototype.latency,
                   egress_ingress_bw=router_prototype.egress_ingress_original_bw,
                   ports_count=router_prototype.ports_count,
                   cluster=cluster)

    def __str__(self):
        return self.name

    @staticmethod
    def from_config(conf: Dict = None, router_prototypes_dict: Dict[str, RouterPrototype] = None) -> dict[str, Router]:
        """
        Create routers from a configuration.

        :param conf:
        :param router_prototypes_dict:
        :return:
        """

        routers_dict = {}

        for _router_id, _router_name in enumerate(conf):
            _router_type = conf[_router_name]
            _rho = Router.from_router_prototype(name=_router_name,
                                                router_prototype=router_prototypes_dict[_router_type])
            routers_dict[_router_name] = _rho

        return routers_dict

    @staticmethod
    def to_dict(routers_list: list[Router]) -> dict[str, Router]:
        """
        Convert a list of routers to a dictionary.

        :param routers_list:
        :return:
        """

        routers_dict = {}

        for router in routers_list:
            routers_dict[router.name] = router

        return routers_dict
