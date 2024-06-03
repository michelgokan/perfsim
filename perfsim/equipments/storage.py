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

from typing import TYPE_CHECKING

from perfsim import Resource

if TYPE_CHECKING:
    from perfsim import Host


class Storage(Resource):
    """
    This class represents a storage device in a host. A storage device is a device that stores data. It has a capacity
    and a speed at which it can transfer data.
    """
    def __init__(self,
                 storage_id: str,
                 capacity: float,
                 speed: float,  # in bytes/s (can be determined using sysbench)
                 host: Host):
        super().__init__(type="storage",
                         name="storage_" + str(storage_id),
                         throttleable=False,
                         unit_of_measure="bytes",
                         capacity=capacity * 1024 * 1024 * 8)
        self.speed = speed
        self.host = host

    def get_transfer_time_in_ns(self, bytes: float) -> float:
        """
        Get the time it takes to transfer the given number of bytes in nanoseconds.

        :param bytes:
        :return:
        """

        return (bytes * 10 ** 9) / self.speed
