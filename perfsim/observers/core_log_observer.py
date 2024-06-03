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

from typing import TYPE_CHECKING

from perfsim import Event, LogObserver

if TYPE_CHECKING:
    from perfsim import Core, ReplicaThread


class CoreLogObserver(LogObserver):
    """
    This class is an observer that logs the completion of a thread.
    """

    def __init__(self, core: 'Core'):
        super().__init__(name="CoreLogObserver", subject=core, logger=core.cpu.host.cluster.sim.logger)

    @Event
    def on_thread_completion(self, thread: 'ReplicaThread'):
        """
        Log the completion of a thread.

        :param thread:
        :return:
        """

        if self.subject.cpu.host.cluster.sim.debug:
            self.logger.log("  ** Completed execution of thread #" + str(thread.id) + " in host " +
                            str(thread.replica.host) + " belongs to request " + str(thread.parent_request), 3)
