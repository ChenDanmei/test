#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DiscoveryInterface
------
Defines the API to implement a discoverable object 
.. currentmodule:: simulec.base.interfaces.discovery_interface

.. autosummary::
    :nosignatures:
    DiscoveryInterface

"""
from enum import Enum
import pydash
import logging
from communication_port import CommunicationMode, CommunicationPort
from service_interface import ServiceInterface


class DiscoveryError(Enum):
    SERVICE_UNKNOWN = 0
    MISSING_KEY_IN_REQUEST = 1


class ServiceType(Enum):
    CLIENT = 0
    ALLOCATOR = 1
    SCHEDULER = 2
    ELECTRICAL_NETWORK = 3


""" Discovery of services on the network

    It must be possible for a service to 'discover' or 'find' another one and connect to it

    This system is based on a pair:
        - the searching service: called source
        - the researched service: called destination

    This system is based on the existence of a running DiscoveryService which 
    knows where the services are located on the network

    **This assumes that all objects listening must be created and ports opened ahead**



    """
logger = logging.getLogger(__name__)


class DiscoveryServer(object):
    """This server cqn be run using a TCP Communication port
    OR a simple FUNCTION CALL communication port.

    The service looking to discover other services sends to this port
    a request for a ServiceType

    the returned data is the reference of the service
    {
        "service_type":ServiceType.ALLOCATOR,
        "service_reference":self.allocator
    }
    if CommunicationMode = CommunicationMode.TCP
    the returned data is like:
    {
        "service_type":ServiceType.ALLOCATOR,
        "tcp_port":"tcp://localhost:5555"
    }
    if the service is not known:
    {
        "error":DiscoveryError.SERVICE_UNKNOWN
    }
    """

    @staticmethod
    def make_service_data(service_type: ServiceType
                          , service_reference: CommunicationPort = None
                          , service_tcp_port: str = None
                          , service_id=None):
        """Helper to make services data that must be given to the discovery server
        Arguments:
            service_tcp_port (str):
                A string like "tcp://localhost:5555" should not be used at the same time
                than service_reference. used to set up TCP communication
            connection_port_reference (CommunicationPort):
                A reference to a CommunicationPort object used to set up FUNCTION_CALL
                communication, should not be used at the same time than service_tcp_port
            service_id:
                an identifier of the service (like an int for an id, could also be a string)
                this is optional
        """
        if not service_type:
            raise ValueError("service_type must be set")
        if (service_tcp_port and service_reference):
            raise ValueError("do not use service_tcp_port and service_reference at the same time")
        if not (service_tcp_port or service_reference):
            logger.debug("You must use one of the 2 service_tcp_port or service_reference ")
        dico = {
            "service_type": service_type
        }
        if service_reference:
            dico["service_reference"] = service_reference
        else:
            dico["service_tcp_port"] = service_tcp_port
        if service_id:
            dico["service_id"] = service_id
        return dico

    def __init__(self, services_data: dict, discovery_port: CommunicationPort):
        """
        Arguments
            services_data:
                should be a list of data created by make_service_data
            discovery_port:
                communication port with a valid target port
                The receive_callback of the port will be set in this constructor
        """
        self._communication_port = discovery_port
        self._data = services_data

        self._communication_port.receive_callback = self.receive

    @property
    def discovery_port(self):
        return self._communication_port

    def receive(self, data: dict, respond_function):
        """implements the reception interface"""
        # print("receive in discovery server")
        if not "service_type" in data.keys():
            # error
            respond_function({
                "error": DiscoveryError.MISSING_KEY_IN_REQUEST
            })
            return
        # print("looking for :"+str({"service_type":data["service_type"]}))
        # print(self._data)
        res = pydash.find(self._data, {"service_type": data["service_type"]})
        if not res:
            respond_function({
                "error": DiscoveryError.SERVICE_UNKNOWN
            })
            return
        respond_function(res)
        return


from threading import Event as ThreadEvent
import time


class DiscoveryDelegate(object):
    def __init__(self, timeout_msec=500):
        self._ready: ThreadEvent = ThreadEvent()
        self._resdata: dict = None

    def _discovery_handle_response(self, data: dict):
        # print("discovery handle response")
        self._resdata = data
        self._ready.set()

    def connect_to_service(self, service_type: ServiceType
                           , service_handle_response
                           , discovery_port_target):
        """this class is a simple helper to discover services

        Arguments:
            service_type: like ServiceType.ALLOCATOR
            service_port_mode        : like CommunicationMode.TCP
            handle_calback : function(self, dict) to handle data from this service
            discovery_port_mode : the CommunicationPort to the discovery service
            discovery_port_target : the discovery server:
                                    - CommunicationPort reference if discovery_port_mode == FUNCTION_CALL
                                    - port address if discovery_port_mode == TCP 

        Returns:
            an opened port to the required service with the callback set to handle_callback
        """
        discovery_port_mode = CommunicationMode.FUNCTION_CALL if (
            isinstance(discovery_port_target, CommunicationPort)
        ) else CommunicationMode.TCP

        discovery_port = CommunicationPort(discovery_port_mode)
        discovery_port.port_name = "DiscoveryDelegate_connect_port"
        discovery_port.target_port = discovery_port_target
        discovery_port.receive_callback = self._discovery_handle_response
        # print("created discovery port to send to srv")
        # print(discovery_port._communication_mode)
        # print(discovery_port._target_port)
        discovery_port.send({
            "service_type": service_type
        })
        # print("sent message to discovery server")
        while not self._ready.is_set():
            time.sleep(0.01)
        resport: CommunicationPort = None
        if "service_reference" in self._resdata.keys():
            resport = CommunicationPort(communication_mode=
                                        CommunicationMode.FUNCTION_CALL)
            resport.target_port = self._resdata["service_reference"]
        elif "tcp_port" in self._resdata.keys():
            resport = CommunicationPort(communication_mode=
                                        CommunicationMode.TCP)
            resport.target_port = self._resdata["tcp_port"]
        elif "error" in self._resdata.keys():
            logger.error("en error occured duing connection to server, discovery server answered this:\n"
                         + str(self._resdata["error"])
                         + "\nrequest was:\n"
                         + str(service_type))
        else:
            raise ValueError("discovery service answer not not make any sens:\n" + str(self._resdata))

        resport.receive_callback = service_handle_response

        return resport