#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Priority Queue
--------------------

Define a Priority Queue for events in which Event can be cancelled.

.. currentmodule:: simulec.event_simulator.priority_queue

.. autosummary::
    :nosignatures:

    PriorityQueue
"""

import heapq
from threading import Lock as ThreadLock


class PriorityQueue(object):
    """An implementation of priority queue to sort AbstractEvents and to cancel them if necessary. This
    implementation is thread safe.

    Attributes:
        _pq (list)
            The list of events to be executed. It is in fact a priority queue.

        _pq_lock (threading.Lock):
            A thread lock to access to the list of events.

    See Also:
        :py:mod:`heapq`
        :py:class:`threading.Lock`
    """

    def __init__(self):
        """Constructor for PriorityQueue"""
        self._pq = list()
        self._pq_lock = ThreadLock()

    def push(self, event):
        """Push an event in the priority queue.

        Args:
            event (AbstractEvent):
                The event to add.
        """
        with self._pq_lock:
            heapq.heappush(self._pq, event)

    def pop(self):
        """Pop the next events which is not cancelled.

        Returns:
            AbstractEvent:
                The next event which has not been cancelled.

        Raises:
            IndexError: if the heap is empty (no more event).
        """
        with self._pq_lock:
            event = heapq.heappop(self._pq)  # type: AbstractEvent
            while event.cancelled:
                event = heapq.heappop(self._pq)  # type: AbstractEvent
            return event

    def empty(self):
        """Returns True if and only if the priority queue is empty. Here 'empty' means 'contains a non-cancelled
        event to execute' (= the `pop` method can be used safely if there is only one thread in action...)

        Returns:
            bool:
                True if and only if the priority queue is empty.
        """
        with self._pq_lock:
            for e in self._pq:  # type: AbstractEvent
                if not e.cancelled:
                    return False
            return True

    def cancel(self, key):
        """Cancel all events `e` which satisfies `key(e)`.

        Args:
            key (Callable):
                key specifies a function of one argument that is used to extract a comparison key from each list
                element. (Here AbstractEvent). It can't be None!

        Returns:
            List[AbstractEvent]:
                List of cancelled events.
        """
        le = list()
        with self._pq_lock:
            for e in self._pq:  # type: AbstractEvent
                if key(e):
                    e.cancel()
                    le.append(e)
        return le

    def contains(self, key):
        """Answer `True` if their is at least an event `e` which satisfies `key(e)` in the priority queue.

        Args:
            key (Callable):
                key specifies a function of one argument that is used to extract a comparison key from each list
                element. (Here AbstractEvent). It can't be None!

        Returns:
            bool:
                True if the event contains  at least an event `e` which satisfies `key(e)`.
        """
        with self._pq_lock:
            for e in self._pq:  # type: AbstractEvent
                if key(e):
                    break
            else:
                return False
        return True

    def get(self, key):
        """Get a pointer to the events `e` which satisfies `key(e)` in the priority queue.

        Args:
            key (Callable):
                key specifies a function of one argument that is used to extract a comparison key from each list
                element. (Here AbstractEvent). It can't be None!

        Warning:
            The pointers must only be used for reading purposes! If you want to cancel an event, please use the
            `cancel` method!

        Returns:
            List[AbstractEvent]:
                List of events `e` which satisfies `key(e)`.
        """
        le = list()
        with self._pq_lock:
            for e in self._pq:  # type: AbstractEvent
                if key(e):
                    le.append(e)
        return le
