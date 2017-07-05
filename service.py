#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Service
------
Basic service
.. currentmodule:: simulec.base.service.service

.. autosummary::
    :nosignatures:
    Service
    Scheduler
    SchedulerStopException
    SchedulerBatch

"""

from abc import ABCMeta, abstractmethod
from enum import Enum
import logging
from threading import Event as ThreadEvent, get_ident as current_thread_ident
from .priority_queue import PriorityQueue
from .exception_threading import ExceptionThread
from ..interfaces.event_interface import AbstractEvent
from ..interfaces.service_interface import ServiceInterface, ServiceMode



logger = logging.getLogger(__name__)


class Service(ExceptionThread,ServiceInterface):
    """class to subclass to create a service like client allocator...
    """

    def __init__(self, service_mode: ServiceMode
                 ,exit_callback=None):
        """
        Arguments
            service_mode : Enum types to ensure the user of the class understands the setting
                           - In ASYNC mode, this service can run with a PriorityQueue for events
                           The events will be ordered by date_time. The events are pushed in that queue that is processed
                           in a separate processing thread.
                           => For instance, that mode is always used by the simulator
                           - In SYNC Mode the event is processed when added
                           => for instance the client can run in SYNC mode if the simulator manages
                           the delaying of Events to play them at the right date
        """
        ExceptionThread.__init__(self, name="ServiceThread", daemon=False)
        self._service_mode = service_mode
        # Some exit callbacks which are called at the end of the simulation
        self._exit_callback = exit_callback

        self._event_queue: PriorityQueue = None
        if self.is_async:
            self._event_queue = PriorityQueue()


    def start(self):
        """Call to start the Thread IF in ASYNC mode
        overrides the Thread method to check 
        if it should be called or not"""
        if not self.is_async:
            raise RuntimeError
        print("starting thread")
        ExceptionThread.start(self)

    def add_event(self, event: AbstractEvent):
        """
        Add an event to the list of future events to simulate.

        Args:
            event (AbstractEvent):
                The event to add to the current simulator.
        """
        if self.is_async:
            print("push")
            self._event_queue.push(event)
        else:
            self.process_event(event)

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
        return self._event_queue.cancel(key=key)

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
        return self._event_queue.contains(key=key)

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
        return self._event_queue.get(key=key)
