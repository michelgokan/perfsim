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

from perfsim import ResourceNotAvailableError

"""
    The `Resource` class is the base class for all the resources in a `Host`,
    such as `CPU`, 'Memory` or `Nic`.

    Here are the possible initialization parameters:

        `type`
            Type of the resource. In example *Cpu* or *Nic*
            
        `name`
            Name of the resource. In example *Cpu1*.

        `is_throttleable`
            Whether the resource can get throttled or not.

        `max_bandwidth`
            Maximum bandwidth that this host's NIC can support. During initiallization,
            a `Nic` object with the given bandwidth is being created. (can be accessed
            via self.Nic)    

"""


class Resource:
    """
    The `Resource` class is the base class for all the resources in a `Host`.
    """

    #: The type of the resource.
    type: str

    #: The name of the resource.
    name: str

    #: Whether the resource can get throttled or not.
    throttleable: bool

    #: The unit in which the resource is measured.
    unit_of_measure: str

    #: The maximum capacity of the resource.
    capacity: Union[int, float]

    #: The current reserved capacity of the resource.
    __reserved: Union[int, float]

    def __init__(self, type: str, name: str, throttleable: bool, unit_of_measure: str, capacity: Union[int, float]):
        self.type = type
        self.name = name
        self.throttleable = throttleable
        self.unit_of_measure = unit_of_measure
        self.capacity = capacity
        # self.time_slices = np.zeros(1000, dtype=bool)
        self.__reserved = 0

    @property
    def reserved(self):
        """
        Get the reserved capacity of the resource.

        :return:
        """
        return self.__reserved

    @reserved.setter
    def reserved(self, v):
        """
        Set the reserved capacity of the resource.

        :param v:
        :return:
        """
        raise Exception("You can't directly change reserved value. Use the reserve(amount) method instead.")

    def get_utilization(self) -> float:
        """
        Get the utilization of the resource.

        :return:
        """

        return self.capacity / self.reserved

    def is_there_enough_resources_to_reserve(self, amount: int) -> bool:
        """
        Check if there are enough resources to reserve.

        :param amount:
        :return:
        """

        if self.get_available() >= amount:
            return True
        else:
            return False

    def reserve(self, amount: int) -> None:
        """
        Reserve the given amount of resources.

        :param amount:
        :return:
        """

        if self.is_there_enough_resources_to_reserve(amount=amount):
            if amount >= 0:
                self.__reserved += amount
            else:
                raise Exception(
                    "Reserving negative resource (" + str(amount) + "/" + str(self.__reserved) + ") is not possible!")
        else:
            raise ResourceNotAvailableError("You can't reserve more than available resources")

    def release(self, amount: int) -> None:
        """
        Release the given amount of resources.

        :param amount:
        :return:
        """

        if self.reserved < amount and self.throttleable != False:
            raise Exception(
                "Error: The amount of resource to release is bigger than the reserved capacity. Are you "
                "sure you are doing everything correctly?!")
        else:
            self.__reserved -= amount
            if self.__reserved < 0:
                raise Exception("How come reserved resource is less than 0! WTF?")

    def get_available(self) -> int:
        """
        Get the available resources.

        :return:
        """

        return self.capacity - self.reserved
