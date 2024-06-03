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

from typing import Dict


class RouterPrototype:
    name: str

    latency: int

    egress_ingress_original_bw: int

    ports_count: int

    def __init__(self, name: str, latency: int, egress_ingress_bw: int, ports_count: int):
        self.name = name
        self.latency = latency
        self.egress_ingress_original_bw = egress_ingress_bw
        self.ports_count = ports_count

    @staticmethod
    def from_config(conf: Dict = None) -> dict[str, 'RouterPrototype']:
        router_prototypes_dict = {}

        for _router_prototype_id, _router_prototype_name in enumerate(conf):
            router_prototypes_dict[_router_prototype_name] = \
                RouterPrototype(name=_router_prototype_name,
                                latency=conf[_router_prototype_name]["latency"],
                                egress_ingress_bw=conf[_router_prototype_name]["bandwidth"],
                                ports_count=conf[_router_prototype_name]["ports_count"])

        return router_prototypes_dict
