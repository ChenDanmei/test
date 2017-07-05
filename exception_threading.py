#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exception Threading
-------------------

Define the Simulator which plays the events.

.. currentmodule:: simulec.event_simulator.exception_threading

.. autosummary::
    :nosignatures:

    ExceptionThread
"""

import sys
import threading
from abc import abstractmethod


class ExceptionThread(threading.Thread):
    """A Thread class which can catch an exception and send it to the main thread.
    From : https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread-in-python

    Attributes:
        exc (Tuple[type,BaseException,Traceback]):
            A tuple which stores the exception of the `ExceptionThread`.

    See Also:
        :py:func:`sys.exc_info`
    """

    def __init__(self, *args, **kwargs):
        """Initialize an `ExceptionThread`. It adds the `exc` field in the

        Args:
            The same than the mother class `threading.Thread`.

        See Also:
            :py:class:`threading.Thread`
        """
        super(ExceptionThread, self).__init__(*args, **kwargs)
        self.exc = None

    @abstractmethod
    def run_with_exception(self):
        """This method must be overridden. It is the main run method which can throw an error."""
        raise NotImplementedError

    def run(self):
        """It runs the thread and catch an exception if one is
        thrown in the `run_with_exception` method.

        Warning:
            Do not override this method but the method `run_with_exception`!
        """
        # noinspection PyBroadException
        print("runing thread")
        try:
            self.run_with_exception()
        except NotImplementedError as e:
            raise e
        except BaseException:
            self.exc = sys.exc_info()

    def join(self, timeout=None):
        """A join method based on the Thread join method which raise an
        error if the thread has thrown one.

        See Also:
            :py:meth:`threading.Thread.join`
        """
        super(ExceptionThread, self).join(timeout=timeout)
        if self.exc:
            msg = 'Thread {0!r} threw an exception: \'{1}\''.format(self.name, self.exc[1])
            try:
                error = self.exc[0](msg).with_traceback(self.exc[2])
            except TypeError:
                raise RuntimeError(msg).with_traceback(self.exc[2])
            else:
                raise error
