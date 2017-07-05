"""
-------------------

simple tests for the service class

.. currentmodule:: simulec.base.test.test_service

.. autosummary::
    :nosignatures:
    TestService
"""

import unittest
from nose.tools import nottest
import datetime as dt
import time
from ..communication.communication_port import CommunicationMode, CommunicationPort
from ..communication.discovery import DiscoveryError, DiscoveryServer
from ..service.service import Service
from ..interfaces.service_interface import ServiceMode
from ..interfaces.event_interface import AbstractEvent


class StopDummyServiceException(BaseException):
    pass

class DummyService(Service):
    def __init__(self, service_mode: ServiceMode):
        Service.__init__(self, service_mode=service_mode)
    def run_with_exception(self):
        while True:
            try:
                ev = self._event_queue.pop()
                self.process_event(ev)
            except IndexError:
                time.sleep(0.01)
            except StopDummyServiceException:
                break
    def process_event(self, event: AbstractEvent):
        event.execute()
class StopEvent(AbstractEvent):
    def __init__(self):
        super(StopEvent, self).__init__(date_time=dt.datetime.now())
    def execute(self):
        raise StopDummyServiceException
class DummyEvent(AbstractEvent):
    def __init__(self, name: str):
        super(DummyEvent, self).__init__(date_time=dt.datetime.now())
        self.name=name
        self.executed = False
    def execute(self, scheduler):
        print("dummyevent execute")
        self.executed = True

class TestService(unittest.TestCase):
    def test_sync_add_and_process(self):
        ds = DummyService(ServiceMode.SYNC)
        ev = DummyEvent('test_event')
        ds.add_event(ev)
        self.assertTrue(ev.executed)
    def test_async_add_and_process(self):
        ds = DummyService(ServiceMode.ASYNC)
        ev = DummyEvent('test_event')
        ds.add_event(ev)
        # should not have been executed yet
        self.assertFalse(ev.executed)
        self.assertFalse(ds._event_queue.empty())
        # now let s start the thread
        ds.start()
        self.assertTrue(ds.is_alive())
        time.sleep(0.5)
        self.assertTrue(ev.executed)
        ds.add_event(StopEvent())
        time.sleep(0.5)
        self.assertFalse(ds.is_alive())
        ds.join()
if __name__ == '__main__':
    unittest.main()
