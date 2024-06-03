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


class TopologyLinkPrototype:
    """
    The link's latency
    """
    latency: int

    def __init__(self, name: str, latency: int):  # , bandwidth: int):
        self.name = name
        self.latency = latency
        # self.bandwidth = bandwidth

    @staticmethod
    def from_config(conf: Dict = None) -> dict[str, 'TopologyLinkPrototype']:
        link_prototypes_dict = {}

        for _link_prototype_id, _link_prototype_name in enumerate(conf):
            link_prototypes_dict[_link_prototype_name] = \
                TopologyLinkPrototype(name=_link_prototype_name, latency=conf[_link_prototype_name]["latency"])

        return link_prototypes_dict
