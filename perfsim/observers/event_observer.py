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


from abc import ABC
from typing import Callable, TYPE_CHECKING, Dict

from perfsim import Event

if TYPE_CHECKING:
    from perfsim import Observable


class EventObserver(ABC):
    """
    This class is an abstract class that represents an observer of an observable.
    """

    _subject: 'Observable'
    _events: Dict[str, Event]
    callable: Callable
    name: str

    @property
    def events(self):
        """
        Get the events of the observer.

        :return:  The events of the observer.
        """
        return self._events

    @events.setter
    def events(self, v):
        """
        Set the events of the observer. This method should not be used because the events are set by the Event decorator.
        Therefore, this method raises an exception.

        :param v:  The events of the observer.
        :return:  None
        """
        raise Exception("Cannot set events manually. Use Event decorator instead.")

    @property
    def subject(self):
        """
        Get the subject of the observer.

        :return:  The subject of the observer.
        """

        return self._subject

    def __init__(self, name: str, subject: 'Observable'):
        self.name = name
        self._subject = subject
        self._events = Event.methods(self.__class__)

    def observe(self, event_name: str, **kwargs):
        """
        Observe an event.

        :param event_name:  The name of the event to observe.
        :param kwargs:  The arguments of the event.
        :return:  The result of the event.
        """

        return self._events[event_name](self, **kwargs)

    def __hash__(self):
        """
        We make sure only one observer of the same type can be added to the observers set of same observable.

        :return: hash of the observer name
        """
        return hash(self.name)
