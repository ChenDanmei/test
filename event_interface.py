#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EventInterface
------

File which contains the definition of the events used by the event simulator.

.. currentmodule:: simulec.base.interfaces.event_interface

.. autosummary::
    :nosignatures:

    AbstractEvent
"""

import datetime as dt
import logging
import functools
from abc import ABCMeta, abstractmethod



@functools.total_ordering
class AbstractEvent(metaclass=ABCMeta):
    """Abstract class to define an event. The instances of this
    class are totally ordered according to their
    date_time.

    Attributes:

        date_time (datetime.datetime):
            The date_time of the event ie. when it must be executed.

        _cancelled (bool):
            A boolean to mark the event as cancelled
    """

    def __init__(self, date_time: dt.datetime):
        """Constructor for AbstractEvent

        Args:
            date_time (datetime.datetime):
                The date_time of the event ie. when it must be executed.
        """
        self.date_time = date_time
        self._cancelled = False
        self._log = logging.getLogger(__name__)

    def __eq__(self, other):
        """Compare two events. The comparison is made on their
        date_time in order to be stored in an event queue by the
        simulator.

        Args:
            other (AbstractEvent):
                Event to compare with.

        Returns:
            bool:
                True if and only if the events happen at the same date_time
        """
        return self.date_time == other.date_time

    def __lt__(self, other):
        """Compare two events. The comparison is made on their
        date_time in order to be stored in an event queue by the
        simulator.

        Args:
            other (AbstractEvent):
                Event to compare with.

        Returns:
            bool:
                True if and only if the other event happen after the current event.
        """
        return self.date_time < other.date_time

    @abstractmethod
    def execute(self, simulator):
        """Abstract method which execute the event. Must be redefined
        in each subclass of `AbstractEvent`.

        Args:
            simulator (AbstractSimulator):
                The simulator which runs the event.
        """
        raise NotImplementedError

    def cancel(self):
        """A method to cancel an event."""
        self._cancelled = True

    @property
    def cancelled(self):
        """A getter method to know if an event is cancelled or not.

        Returns:
            bool:
                True if the event has been cancelled.
        """
        return self._cancelled

