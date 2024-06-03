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

from abc import ABC, abstractmethod
from typing import Dict, Set

from perfsim import EventObserver


class Observable(ABC):
    """
    This class is an abstract class that represents an observable.
    """

    #: A dictionary of observers, indexed by event type.
    observers: Dict[str, Set[EventObserver]]
    notify_observers_on_event: bool
    registered_events: Set[str]

    def attach_observer(self, observer: EventObserver):
        """
        Attach an observer to the observable.

        :param observer: The observer to attach.
        :return:  None
        """
        for event_name in observer.events:
            if event_name not in self.observers.keys():
                if event_name not in self.registered_events:
                    raise Exception(f"Event {event_name} is not registered. "
                                    f"Please first register the event using register_event method.")
                self.observers[event_name] = set()
            self.observers[event_name].add(observer)

    def notify_all_observers(self, **kwargs):
        """
        Notify all observers.

        :param kwargs:  The arguments to pass to the observers.
        :return:
        """
        for event_name, observers in self.observers.items():
            for observer in observers:
                observer.observe(**kwargs)

    def notify_observers(self, event_name: str, **kwargs):
        """
        Notify the observers of an event.

        :param event_name: The name of the event.
        :param kwargs:  The arguments to pass to the observers.
        :return:  None
        """
        if self.notify_observers_on_event and event_name in self.observers:
            for observer in self.observers[event_name]:
                observer.observe(event_name=event_name, **kwargs)

    def detach_observer(self, observer: EventObserver):
        """
        Detach an observer from the observable.

        :param observer: The observer to detach.
        :return:  None
        """
        for event_name in observer.events:
            self.observers[event_name].discard(observer)

    def register_event(self, event_name: str):
        """
        Register an event.

        :param event_name:
        :return:
        """
        setattr(self, event_name, event_name)
        self.registered_events.add(event_name)

    def __init__(self):
        self.observers = {}
        self.notify_observers_on_event = True
        self.registered_events = set()
        self.register_events()

    @abstractmethod
    def register_events(self):
        """
        This is for performance optimization purposes. Instead of generating strings for each event, we can register the
        event_names as attributes, then we send the event_name as reference, instead of copying the string every time.
        This (slightly) improves performance, specially because we are calling the notify_observers method several times
        for each request during the simulation.

        :return:
        """
        pass
