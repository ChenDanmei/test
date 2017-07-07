"""
Test Communication Port
-------------------

Test for comunication ports

.. currentmodule:: simulec.base.test.test_communication_port

.. autosummary::
    :nosignatures:

    TestCommunicationPort
"""

import unittest
from nose.tools import nottest
from communication_port import CommunicationMode, CommunicationPort
import time


class TestCommunicationPort(unittest.TestCase):
    RESPONSE_MSG = {"response":"ok"}
    def setUp(self):
        self.data_b = None
        self.data_a = None

    @nottest
    def callback_response(self, data):
        """fake callback method"""
        self.data_a = data

    @nottest
    def callback_response_tcp(self, data):
        """fake callback method"""
        self.data_c = data
    @nottest
    def callback_request(self, data, respond_function):
        """fake callback method"""
        self.data_b = data
        if respond_function:
            respond_function(TestCommunicationPort.RESPONSE_MSG)


    def test_simple_direct_call(self):
        """write from port a to port b"""

        port_a = CommunicationPort(CommunicationMode.FUNCTION_CALL_SEND)
        port_b = CommunicationPort(CommunicationMode.FUNCTION_CALL_RECV)

        port_a.target_port = port_b
        port_a.port_name="port_a"
        port_b.port_name="port_b"

        # now test req rep
        port_a.receive_callback = self.callback_response
        port_b.receive_callback = self.callback_request
        data = {"test":"ok_test2"}
        port_a.send(data)
        self.assertEqual(self.data_b, data)
        self.assertEqual(self.data_a, TestCommunicationPort.RESPONSE_MSG)


    def test_tcp(self):
        """write from port a to port b"""
        port_a = CommunicationPort(CommunicationMode.TCP_SEND)
        address = "tcp://localhost:5668"
        port_b = CommunicationPort(CommunicationMode.TCP_RECV, target_address=address)
        port_a.port_name = "port_a"
        port_b.port_name = "port_b"
        port_a.receive_callback = self.callback_response
        port_b.receive_callback = self.callback_request
        port_b.receive_callback_tcp = self.callback_response_tcp
        port_b.task.start()
        #port_b.task.send_message = TestCommunicationPort.RESPONSE_MSG
        port_a.target_port = port_b.task.address
        data_a = {"test":"ok_a"}
        port_a.send(data_a)
        while not port_b.task.recv:
            time.sleep(0.001)
        port_b.receive(port_b.task.data, respond_function=port_b.receive_tcp)
        self.assertEqual(self.data_b, data_a)
        while not port_a.recv:
            time.sleep(0.001)
        port_a.receive(port_a.task.data)
        self.assertEqual(self.data_a, TestCommunicationPort.RESPONSE_MSG)


if __name__ == '__main__':
    unittest.main()
