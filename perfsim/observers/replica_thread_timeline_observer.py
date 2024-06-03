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

from typing import TYPE_CHECKING, Union

from perfsim import EventObserver, Event

if TYPE_CHECKING:
    from perfsim import ReplicaThread, ReplicaThread


class ReplicaThreadTimelineObserver(EventObserver):
    """
    This class is responsible for logging the replica thread events.
    """

    def __init__(self, replica_thread: 'ReplicaThread'):
        super().__init__(name="ReplicaThreadTimelineObserver", subject=replica_thread)

    @Event
    def before_killing_thread(self):
        if self.subject.core.cpu.host.cluster.sim.log_timeline:
            df_column_name = str(self.subject.process.pname) + "_" + str(self.subject.id) + "_" + \
                             str(int(self.subject.process.cpu_requests_share))

            self.subject.replica.host.timeline_event.append("kill " + df_column_name + " on " +
                                                            str(self.subject.core.name) + "-inst=" +
                                                            str(self.subject.executed_instructions))
            self.subject.replica.host.timeline_time.append(
                str(round(float(self.subject.core.cpu.host.cluster.sim.time), 5)))

    @Event
    def before_executing_thread(self,
                                duration: Union[int, float],
                                simultaneous_flag: bool,
                                instructions_to_consume: Union[int, float]):
        if self.subject.core.cpu.host.cluster.sim.log_timeline:
            column = str(self.subject.process.pname) + "_" + \
                     str(self.subject.id) + "_" + \
                     str(int(self.subject.process.cpu_requests_share))
            self.subject.replica.host.timeline_event.append("exe " + column + " on " + str(self.subject.core.name) +
                                                            " for " + str(int(duration)) + "ns")
            if not simultaneous_flag:
                time = round(float(self.subject.core.cpu.host.cluster.sim.time), 5)
            else:
                time = round(float(self.subject.core.cpu.host.cluster.sim.time - duration), 5)

            self.subject.replica.host.timeline_time.append(str(time))

    @Event
    def after_executing_thread(self,
                               duration: Union[int, float],
                               simultaneous_flag: bool,
                               instructions_to_consume: Union[int, float],
                               relative_share_proportion: Union[int, float]):
        if self.subject.core.cpu.host.cluster.sim.log_timeline:
            column = str(self.subject.id)

            self.subject.core.runqueue.threads_total_time[column][int(self.subject.core.cpu.host.cluster.sim.time)] = \
                duration * relative_share_proportion
