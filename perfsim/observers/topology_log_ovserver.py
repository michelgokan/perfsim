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

from perfsim import LogObserver, Event

if TYPE_CHECKING:
    from perfsim import Topology


class TopologyLogObserver(LogObserver):
    def __init__(self, topology: 'Topology'):
        super().__init__(name="TopologyLogObserver", subject=topology, logger=topology.sim.logger)

    @Event
    def before_recalculate_transmissions_bw_on_all_links(self):
        if self.subject.sim.debug:
            self.logger.log("Number of active_edges = " + str(len(self.subject.active_edges)))
