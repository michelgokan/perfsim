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

from typing import Union, TYPE_CHECKING, Dict, Any

from perfsim import Event, LogObserver

if TYPE_CHECKING:
    from perfsim import Transmission


class TransmissionLogObserver(LogObserver):
    def __init__(self, transmission: 'Transmission'):
        super().__init__(name="TransmissionLogObserver",
                         subject=transmission,
                         logger=transmission.src_replica.host.cluster.sim.logger)

    @Event
    def on_current_bw_change(self, new_bw: Union[float, int], edge_data: Dict[str, Any]):
        if self.subject.src_replica.host.cluster.sim.debug:
            self.logger.log(" - Transmission bandwidth changed for a transmission on link " + edge_data["name"] +
                            " related to request " + str(self.subject.subchain_id_request_pair[0]) +
                            " | subchain id = " + str(self.subject.subchain_id_request_pair[1]) + " with remaining " +
                            "payload size = " + str(self.subject.remaining_payload_size) + "B and remaining network " +
                            "latency of " + str(self.subject.total_latency) + " - Previous bw = " +
                            str(self.subject.current_bw) + " | New bw = " + str(new_bw) + "B/s", 10)

    @Event
    def on_all_transmissions_start(self, duration: Union[float, int]):
        if self.subject.src_replica.host.cluster.sim.debug:
            self.subject.src_replica.host.cluster.sim.logger.log(
                "      ****** Transmitting a transmission related to request " +
                str(self.subject.subchain_id_request_pair[0]) + " | subchain id = " +
                str(self.subject.subchain_id_request_pair[1]) + " with remaining payload size = " +
                str(self.subject.remaining_payload_size) + "B and remaining network latency of " +
                str(self.subject.total_latency) + " with bw=" +
                str(self.subject.current_bw) + "B/s for " + str(duration) + "ns", 10)
        if self.subject.total_latency > 0:
            if duration > self.subject.total_latency:
                if self.subject.src_replica.host.cluster.sim.debug:
                    self.subject.src_replica.host.cluster.sim.logger.log(
                        "       ******* Reducing remaining latency ... (remaining = 0)", 10)
                else:
                    if self.subject.src_replica.host.cluster.sim.debug:
                        self.subject.src_replica.host.cluster.sim.logger.log(
                            "       ******* Reduced remaining latency only ... (remaining = " +
                            str(self.subject.total_latency), 10)

    @Event
    def on_all_transmissions_end(self, duration: Union[float, int], bytes_of_data_transmitted: int):
        if self.subject.src_replica.host.cluster.sim.debug:
            self.subject.src_replica.host.cluster.sim.logger.log(
                "       ******* Transmitted " + str(bytes_of_data_transmitted) + "B of data", 10)
            self.subject.src_replica.host.cluster.sim.logger.log(
                "         ******** - Remaining payload size = " + str(self.subject.remaining_payload_size) + "B", 10)

    @Event
    def on_before_transmission_time_calculation(self):
        if self.subject.src_replica.host.cluster.sim.debug:
            self.subject.src_replica.host.cluster.sim.logger.log(
                "     ***** [Transmission] Calculating transmission time for request " +
                str(self.subject.subchain_id_request_pair[0]) + " and subchain id " +
                str(self.subject.subchain_id_request_pair[1]) + " between " +
                str(self.subject.src_replica.host.name) + " -> " +
                str(self.subject.dst_replica.host.name), 3)

    @Event
    def on_after_transmission_time_calculation(self):
        if self.subject.src_replica.host.cluster.sim.debug:
            self.subject.src_replica.host.cluster.sim.logger.log(
                "      ****** Transmission time = " + str(self.subject.transmission_time), 3)
            self.subject.src_replica.host.cluster.sim.logger.log(
                "       ******* Transmission exact time = " + str(self.subject.transmission_exact_time), 10)
