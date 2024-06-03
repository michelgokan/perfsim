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

from typing import Union

from perfsim import ReplicaThread


class ThreadSet(set):
    """
    ThreadSet class is used to represent a set of threads in a RunQueue.
    """

    #: The sum of cpu requests of all threads in the set.
    sum_cpu_requests: int

    """
    The type of the set:
        0: BestEffort
        1: Guaranteed
        2: Burstable
        3: Burstable unlimited
        4: Burstable limited
    """
    _type_of_set: Union[int, None]

    def __init__(self, type_of_set: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sum_cpu_requests = 0
        if type_of_set not in [0, 1, 2, 3, 4] and type_of_set != []:
            raise ValueError(
                """type_of_set must be in [0, 1, 2, 3, 4]! 
                    0: BestEffort
                    1: Guaranteed
                    2: Burstable
                    3: Burstable unlimited
                    4: Burstable limited""")
        else:
            self._type_of_set = type_of_set

    @property
    def type_of_set(self) -> int:
        return self._type_of_set

    @type_of_set.setter
    def type_of_set(self, value: int) -> None:
        raise AttributeError("Cannot set type_of_set attribute. Set only during initialization.")

    def add(self, thread: ReplicaThread) -> None:
        if thread.process.ms_replica.microservice.cpu_requests is not None:
            self.sum_cpu_requests += thread.cpu_requests_share

        super().add(thread)

        if thread.id not in thread.core.runqueue.thread_set_dict:
            thread.core.runqueue.thread_set_dict[thread.id] = {self}
        else:
            thread.core.runqueue.thread_set_dict[thread.id].add(self)

    def remove(self, thread: ReplicaThread) -> None:
        if thread.process.ms_replica.microservice.cpu_requests is not None:
            self.sum_cpu_requests -= thread.cpu_requests_share
        thread.core.runqueue.thread_set_dict[thread.id].remove(self)
        super().remove(thread)

    def recalculate_sum_cpu_requests(self) -> int:
        """
        Recalculate the sum of cpu requests of all threads in the set.

        :return: The sum of cpu requests of all threads in the set.
        """

        self.sum_cpu_requests = 0
        for thread in self:
            self.sum_cpu_requests += thread.cpu_requests_share

        return self.sum_cpu_requests

    def __hash__(self):
        return hash(self._type_of_set)
