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

import math
from typing import TYPE_CHECKING, Union

from perfsim import RunQueue, Resource, Observable, CoreLogObserver

if TYPE_CHECKING:
    from perfsim import CPU


class Core(Resource, Observable):
    """
    This class represents a core in a CPU. A core is a processing unit that can execute threads. It has a run queue
    that contains the threads that are currently assigned to it. The core can execute threads for a certain duration.
    """

    #: The CPU that this core belongs to
    __cpu: CPU

    #: The core's unique identifier in the CPU
    id_in_cpu: int

    #: The run queue that this core is currently assigned to.
    runqueue: RunQueue

    def __init__(self, cpu: CPU, core_id: Union[str, int], core_id_in_cpu: int):
        name = "core_" + str(core_id)
        self.core_id = core_id
        self.id_in_cpu = core_id_in_cpu
        self.pair_id = int(math.floor(self.id_in_cpu / 2))
        super().__init__(type="core", name=name, throttleable=True, unit_of_measure="shares",
                         capacity=cpu.max_cpu_requests)
        self.cpu = cpu
        self.runqueue = RunQueue(core=self)
        Observable.__init__(self)
        if cpu.host.cluster is not None and cpu.host.cluster.sim.debug:
            self.attach_observer(CoreLogObserver(core=self))

    def reinit(self):
        """
        Reinitialize the core

        :return:
        """
        self.__init__(cpu=self.cpu, core_id=self.core_id, core_id_in_cpu=self.id_in_cpu)

    def register_events(self):
        """
        Register events for the core

        :return:
        """

        self.register_event("on_thread_completion")

    def get_core_clock_cycle(self) -> float:
        """
        Returns the clock cycle of the core

        :return:
        """

        return 1 / self.cpu.clock_rate

    def exec_threads(self, duration: Union[int, float]) -> int:
        """
        Executes threads on the core for `duration` nanoseconds

        :param: duration: The execution duration
        """

        completed_threads = 0
        thread_id = 0
        simultaneous_flag = False
        prev_total_be_threads = len(self.runqueue.best_effort_active_threads)  #: BE = Best Effort
        prev_total_ge_cpu_rqsts = self.runqueue.guaranteed_active_threads.sum_cpu_requests  #: GE = Guaranteed
        rq_prev_active_threads = 0

        if len(self.runqueue.rq) == 0:
            self.runqueue.run_idle(duration=duration)
        else:
            while thread_id < len(self.runqueue.rq):
                thread = self.runqueue.rq[thread_id]
                if thread.on_rq and thread.instructions != 0:
                    thread.exec(duration, simultaneous_flag)
                    simultaneous_flag = True
                    if thread.instructions <= 0:
                        self.notify_observers(event_name="on_thread_completion")
                        completed_threads += 1
                    thread_id += 1
                    rq_prev_active_threads += 1
                else:
                    thread_id += 1
                    raise Exception("I'm not sure, but I believe there might be a potential bug here!")

        if not prev_total_be_threads and prev_total_ge_cpu_rqsts < self.cpu.max_cpu_requests and rq_prev_active_threads:
            ratio_of_idle = (self.cpu.max_cpu_requests - prev_total_ge_cpu_rqsts) / self.cpu.max_cpu_requests
            self.runqueue.threads_total_time["idle"][int(self.cpu.host.cluster.sim.time)] = duration * ratio_of_idle

        return completed_threads

    def __str__(self):
        """
        Returns the string representation of the core

        :return:
        """

        return "host_" + str(self.cpu.host) + "_cpu_" + str(self.cpu) + "_core_" + str(self.id_in_cpu)
