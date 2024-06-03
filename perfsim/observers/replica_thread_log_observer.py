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

from typing import Union, TYPE_CHECKING

from perfsim import Event, LogObserver

if TYPE_CHECKING:
    from perfsim import ReplicaThread


class ReplicaThreadLogObserver(LogObserver):
    """
    This class is responsible for logging the replica thread events.
    """

    def __init__(self, replica_thread: 'ReplicaThread'):
        super().__init__(name="ReplicaThreadLogObserver",
                         subject=replica_thread,
                         logger=replica_thread.replica.host.cluster.sim.logger)

    @Event
    def before_executing_thread(self,
                                duration: Union[int, float],
                                simultaneous_flag: bool,
                                instructions_to_consume: Union[int, float]):
        if self.subject.core.cpu.host.cluster.sim.debug:
            self.logger.log(
                "  ** Thread #" + str(self.subject.thread_id_in_node) + " is going to execute " + str(instructions_to_consume) +
                " instructions for " + str(duration) + "ns on host " + str(self.subject.core.cpu.host.name) +
                " - current remaining instructions (before execution) = " + str(self.subject.instructions), 3)

    @Event
    def after_executing_thread(self,
                               duration: Union[int, float],
                               simultaneous_flag: bool,
                               instructions_to_consume: Union[int, float],
                               relative_share_proportion: Union[int, float]):
        if self.subject.core.cpu.host.cluster.sim.debug:
            self.logger.log("    *** Executed thread #" + str(self.subject.thread_id_in_node) + " for " + str(duration) +
                            "ns on host " + str(self.subject.core.cpu.host.name) + " - remaining instructions = " +
                            str(self.subject.instructions), 3)

    @Event
    def before_killing_thread(self):
        if self.subject.core.cpu.host.cluster.sim.debug:
            self.logger.log("- Killing thread " + str(self.subject.thread_id_in_node), 1)
