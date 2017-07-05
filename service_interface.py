#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Service
------
Basic service
.. currentmodule:: simulec.base.interfaces.service_interface

.. autosummary::
    :nosignatures:
    ServiceInterface

"""

from abc import ABCMeta, abstractmethod
from enum import Enum

from event_interface import AbstractEvent




class ServiceMode(Enum):
    """Use async mode to have a priority queue running in a
    separate thread to process events,
    in sync mode adding an event will execute it right away
    """
    ASYNC = 0
    SYNC = 1

class ServiceInterface(metaclass=ABCMeta):
    """interface for services
    """
    def __init__(self, service_mode: ServiceMode
                 , exit_callback=None):
        """
        Arguments
            service_mode : Enum types to ensure the user of the class understands the setting
                           - In ASYNC mode, this service can run with a PriorityQueue for events
                           The events will be ordered by date_time. The events are pushed
                           in that queue that is processed in a separate processing thread.
                           => For instance, that mode is always used by the simulator
                           - In SYNC Mode the event is processed when added
                           => for instance the client can run in SYNC mode if the simulator manages
                           the delaying of Events to play them at the right date
        """
        self._service_mode = service_mode
        # Some exit callbacks which are called at the end of the simulation
        self._exit_callback = exit_callback

    @property
    def is_async(self):
        """returns True if the service has been created in async mode"""
        return self._service_mode == ServiceMode.ASYNC

    def start(self):
        """Call to start the Thread IF in ASYNC mode
        overrides the Thread method to check
        if it should be called or not"""
        raise NotImplementedError

    @abstractmethod
    def process_event(self, event: AbstractEvent):
        """This function must be overloaded by services implementation"""
        raise NotImplementedError


    def add_event(self, event: AbstractEvent):
        """
        Add an event to the list of future events to simulate.

        Args:
            event (AbstractEvent):
                The event to add to the current simulator.
        """
        raise NotImplementedError

    def __iadd__(self, other):
        """
        suport of += operator, calls add_event

        Args:
            other (AbstractEvent):
                The event to add to the current simulator.
        """
        self.add_event(other)


    def cancel(self, key):
        """Cancel all the events `e` which satisfy `key(e)`.

        Args:
            key (Callable):
                key specifies a function of one argument that is used to extract
                a comparison key from each list
                element. (Here AbstractEvent). It can't be None!

        Returns:
            List[AbstractEvent]:
                The list of cancelled events.

        See Also:
            :py:meth:`priority_queue.PriorityQueue.cancel`
        """
        raise NotImplementedError

    def contains(self, key):
        """Answer `True` if their is at least an event `e` which satisfies `key(e)`
        in the priority queue.

        Args:
            key (Callable):
                key specifies a function of one argument that is used to extract
                a comparison key from each list
                element. (Here AbstractEvent). It can't be None!

        Returns:
            bool:
                True if the event contains  at least an event `e` which satisfies
                `key(e)`.

        See Also:
            :py:meth:`priority_queue.PriorityQueue.contains`
        """
        raise NotImplementedError

    def get(self, key):
        """Get a pointer to the events `e` which satisfies `key(e)` in the priority
        queue.

        Args:
            key (Callable):
                key specifies a function of one argument that is used to extract
                a comparison key from each list
                element. (Here AbstractEvent). It can't be None!

        Warning:
            The pointers must only be used for reading purposes! If you want to
            cancel an event, please use the
            `cancel` method!

        Returns:
            List[AbstractEvent]:
                List of events `e` which satisfies `key(e)`.

        See Also:
            :py:meth:`priority_queue.PriorityQueue.get`
        """
        raise NotImplementedError


    def close_recorders(self):
        """A method to close all the recorders of the simulator."""
        raise NotImplementedError


    def create_recorders(self, recorder_db_name):
        """Method to initialise an unique database for the recorders. It creates
        an unique engine and an unique
        metadata instance.

        Args:
            recorder_db_name (str):
                It is the database url. See the create_engine function of sqlalchemy
                for more details. Valid SQLite
                URL forms are:

                    * sqlite:///:memory: (or, sqlite://)
                    * sqlite:///relative/path/to/file.db
                    * sqlite:////absolute/path/to/file.db

        See Also:
            :py:func:`sqlalchemy.create_engine`
        """
        raise NotImplementedError
