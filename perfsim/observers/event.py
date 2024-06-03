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


class Event:
    """
    This class is a decorator that marks a method as an event.
    """

    def __init__(self, method):
        self._method = method

    def __call__(self, obj, *args, **kwargs):
        return self._method(obj, *args, **kwargs)

    @classmethod
    def methods(cls, subject):
        """
        Get the methods of the subject that are marked as events.

        :param subject:
        :return:  A dictionary of the methods of the subject that are marked as events.
        """

        def g():
            """
            Get the methods of the subject that are marked as events.

            :return: A generator of the methods of the subject that are marked as events.
            """

            for name in dir(subject):
                method = getattr(subject, name)
                if isinstance(method, Event):
                    yield name, method

        return {name: method for name, method in g()}
