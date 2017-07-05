"""
-------------------

Test for comunication ports

.. currentmodule:: simulec.base.test.test_discovery

.. autosummary::
    :nosignatures:

    TestDiscovery
"""

import unittest
from nose.tools import nottest
from communication_port import CommunicationMode, CommunicationPort
from discovery import DiscoveryServer, DiscoveryDelegate, ServiceType, DiscoveryError


class TestDiscovery(unittest.TestCase):
    SERVICE_DIRECT_RESPONSE_MSG = {"ok":"ok"}
    ALLOCATOR_RESPONSE = {"data":"pong"}

    def service_direct_receive_clbk(self, data: dict, respond_function):
        self.service_direct_received_data = data
        respond_function(TestDiscovery.SERVICE_DIRECT_RESPONSE_MSG)
    def allocator_port_callback(self, data: dict, respond_function):
        self.allocator_received_data = data
        respond_function(TestDiscovery.ALLOCATOR_RESPONSE)

    def setUp(self):
        self.data_b = None
        self.allocator_received_data = None
#setup discoserver
        self.service_direct = CommunicationPort(CommunicationMode.FUNCTION_CALL)
        self.service_direct.port_name="service_direct"
        self.service_direct.receive_callback = self.service_direct_receive_clbk

        self.allocator_port = CommunicationPort(CommunicationMode.FUNCTION_CALL)
        self.allocator_port.port_name="allocator_port"
        self.allocator_port.receive_callback = self.allocator_port_callback

        self.port_disco = CommunicationPort(CommunicationMode.FUNCTION_CALL)
        self.port_disco.port_name="port_disco"
        self.service_tcp_info = {"service_type":"servicetcp",
            "tcp_port":"tcp://localhost:8888"}
        self.allocator_info = {"service_type":ServiceType.ALLOCATOR,
            "service_reference":self.allocator_port}
        self.service_direct_info = {"service_type":"servicedirect",
            "service_reference":self.service_direct}
        self.disco_srv = DiscoveryServer([
            self.service_tcp_info, self.service_direct_info, self.allocator_info],
            discovery_port=self.port_disco)

    @nottest
    def calback_response(self, data):
        """fake callback method"""
        self.data_b = data


    def test_simple_direct_call(self):
        """write from port a to port b"""

        port_source = CommunicationPort(CommunicationMode.FUNCTION_CALL)
        port_source.receive_callback = self.calback_response
        port_source.target_port = self.port_disco
        port_source.port_name="port_source"

        data_a = {"service_type":"servicetcp"}
        port_source.send(data_a)
        self.assertEqual(self.data_b, self.service_tcp_info)
        data_a = {"service_type":"servicedirect"}
        port_source.send(data_a)
        self.assertEqual(self.data_b, self.service_direct_info)
        data_a = {"service_type":"toto"}
        port_source.send(data_a)
        self.assertEqual(self.data_b, {"error":DiscoveryError.SERVICE_UNKNOWN})
        data_a = {"test":"ok"}
        port_source.send(data_a)
        self.assertEqual(self.data_b, {"error":DiscoveryError.MISSING_KEY_IN_REQUEST})


    def test_discovery_delegate(self):
        dd = DiscoveryDelegate()
        port = dd.connect_to_service(service_type=ServiceType.ALLOCATOR
                             , service_handle_response= self.calback_response
                             , discovery_port_target=self.port_disco)
        port.port_name="port"
        msg  ={"data":"ping"}
        print("testing received port")
        self.assertEqual(None, self.allocator_received_data)
        self.assertEqual(None, self.data_b)
        port.send(msg)
        self.assertEqual(msg, self.allocator_received_data)
        self.assertEqual(TestDiscovery.ALLOCATOR_RESPONSE, self.data_b)

if __name__ == '__main__':
    unittest.main()
