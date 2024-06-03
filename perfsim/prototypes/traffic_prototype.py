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
from math import floor
from typing import Union, List, Dict


class TrafficPrototype:
    """
    TrafficPrototype is a class that holds the traffic configuration, that later on can be used to
    generate traffic for various service chains using a load generator.
    """

    #: The total number of iterations that requests is going to be generated, which is calculated as the product of
    #: simulation duration times arrival rate. E.g., if simulation duration is 60 second, arrival rate is 10 requests
    #: per second, and number of parallel users are 30 then total number of iterations will be 10 * 60 = 600, in which
    #: 30 * 600 = 1800 requests will be generated in total.
    __iterations_count: int

    #: The delta time between two consecutive batch of requests (in nanoseconds)
    __arrival_interval_ns: int

    #: The number of parallel users.
    __parallel_users: int

    #: The duration in which the traffic is going to be simulated (in seconds).
    __duration: int

    #: The total number of requests that will be generated.
    __requests_count: int

    #: The time in second at which the first request is going to be generated.
    __start_at: int

    #: The time in nanoseconds at which the last request is going to be generated.
    __arrival_table: list[int]

    def __init__(self, name: str, arrival_interval_ns: int = 1, duration: int = 1, parallel_user: int = 1,
                 start_at: int = 0):
        self.name = name
        self.__arrival_interval_ns = arrival_interval_ns
        self.__duration = duration
        self.__parallel_user = parallel_user
        self.__start_at = start_at
        self.__arrival_table = []
        self.recalc_all_properties()

    @property
    def arrival_table(self):
        return self.__arrival_table

    @arrival_table.setter
    def arrival_table(self, v):
        raise NotImplementedError("You can't directly set arrival table! Change other parameters instead or "
                                  "call recalc_arrival_table method.")

    @property
    def start_at(self):
        return self.__start_at

    @start_at.setter
    def start_at(self, v):
        self.__start_at = v
        self.recalc_all_properties()

    @property
    def arrival_interval_ns(self):
        return self.__arrival_interval_ns

    @arrival_interval_ns.setter
    def arrival_interval_ns(self, v):
        self.__arrival_interval_ns = v
        self.recalc_all_properties()

    @property
    def duration(self):
        return self.__duration

    @duration.setter
    def duration(self, v):
        self.__duration = v
        self.recalc_all_properties()

    @property
    def parallel_user(self):
        return self.__parallel_user

    @parallel_user.setter
    def parallel_user(self, v):
        self.__parallel_user = v
        self.recalc_all_properties()

    @property
    def iterations_count(self):
        """
        Total number of batch request arrivals
        """
        return self.__iterations_count

    @iterations_count.setter
    def iterations_count(self, v):
        raise Exception(
            "You can't directly set iterations count in the simulation! Change arrival_interval_ns and/or duration instead.")

    @property
    def requests_count(self):
        return self.__requests_count

    @requests_count.setter
    def requests_count(self, v):
        raise Exception("You can't directly set total requests count in the simulation! "
                        "Change arrival_interval_ns, duration and/or parallel_user instead.")

    def recalc_iterations_count(self) -> int:
        self.__iterations_count = floor(self.__duration * 1000000000 / self.__arrival_interval_ns)
        return self.__iterations_count

    def recalc_requests_count(self) -> int:
        self.__requests_count = self.__iterations_count * self.__parallel_user
        return self.__requests_count

    def recalc_arrival_table(self):
        if self.__start_at > self.__duration:
            self.__arrival_table = []
        else:
            self.__arrival_table = [self.__start_at * 10 ** 9]
            for i in range(1, self.__iterations_count):
                self.arrival_table.append(self.arrival_table[i - 1] + self.__arrival_interval_ns)

    def recalc_all_properties(self):
        self.recalc_iterations_count()
        self.recalc_requests_count()
        self.recalc_arrival_table()

    @staticmethod
    def copy_to_dict(traffic_prototypes: Union[List[TrafficPrototype], Dict[str, TrafficPrototype]]) \
            -> Dict[str, TrafficPrototype]:
        if isinstance(traffic_prototypes, dict):
            return deepcopy(traffic_prototypes)
        else:
            traffic_prototypes_dict = {}

            for _traffic_prototype in traffic_prototypes:
                traffic_prototypes_dict[_traffic_prototype.name] = deepcopy(_traffic_prototype)

            return traffic_prototypes_dict

    @staticmethod
    def from_config(conf: Dict = None) -> dict[str, TrafficPrototype]:
        traffic_prototypes_dict = {}

        for _traffic_id, _traffic_name in enumerate(conf):
            traffic_prototypes_dict[_traffic_name] = \
                TrafficPrototype(name=_traffic_name,
                                 arrival_interval_ns=conf[_traffic_name]["arrival_interval_ns"],
                                 duration=conf[_traffic_name]["duration"],
                                 parallel_user=conf[_traffic_name]["parallel_user"])

        return traffic_prototypes_dict
