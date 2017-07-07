#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CommunicationPort
------
Defines the API to implement a communication port 
.. currentmodule:: simulec.base.communication.communication_port

.. autosummary::
    :nosignatures:
    CommunicationMode
    CommunicationPort

"""
from enum import Enum
from typing import Callable
import logging
import zmq
import pickle
import threading
from parse import *
import time

USE_PORT = "zmq"  # Default definition is "zmq", also we can choose "socket" to use socket send messages.


class CommunicationMode(Enum):
    FUNCTION_CALL_SEND = 0
    FUNCTION_CALL_RECV = 1
    TCP_SEND = 2
    TCP_RECV = 3


class CommunicationPort(object):
    """ The communication port can hold a connection to a ServiceInterface through several
    types of communication listed in CommunicationMode

    **IMPORTANT: This assumes that ou use the appropritae mode of
    communication for the service you try to connect to**
    On a communication recv, the port will call the receive_callback.
    This callback must be like:
    def listen_callback_function(self, data:dict) -> bool:
        ...
    *don't forget to pass the callable to pass self.listen_callback_function if this is a 
    method of a class*
    **Don't forget to set the receive_callback property, if not defined, it won't be called back**

    ## How to use:

    Assuming the service you want to contact is on TCP port 5555 of localhost:
    `port = CommunicationPort(CommunicationMode.TCP, tcp_port="tcp://localhost:5555")`

    If you are using direct object and function calls:
    `port = CommunicationPort(CommunicationMode.FUNCTION_CALL, service_reference=object)`

    to send a message use the same interface as a service:
    port.send(data)

    to receive data you must set the receive_callback:
    port.receive_callback = self._my_receive_function

    **IMPORTANT** the receive callback will be called from the receiving thread
    You must use a synchronized queue in a Service to push the data in it


    """

    def __init__(self, communication_mode: CommunicationMode, target_address=None):
        """see class doc"""
        self._communication_mode = communication_mode
        self._target_port = None
        self._receive_callback = None
        self._receive_callback_tcp = None
        self._log = logging.getLogger(__name__)
        self._listening: bool = False
        self.target_address = target_address  # For the mode TCP_RECV, it's necessary to give its value.
        if self._communication_mode == CommunicationMode.TCP_RECV:
            self.task = self._start_listening(self.target_address)
        if self._communication_mode == CommunicationMode.TCP_SEND:
            self.soc = self._start_sending()
        self._name = ""
        self.recv = False

    @property
    def port_name(self):
        return self._name

    @port_name.setter
    def port_name(self, value):
        self._name = value

    @property
    def receive_callback(self):
        return self._receive_callback

    @receive_callback.setter
    def receive_callback(self, fun):
        self._receive_callback = fun

    @property
    def receive_callback_tcp(self):
        return self._receive_callback_tcp

    @receive_callback_tcp.setter
    def receive_callback_tcp(self, fun):
        self._receive_callback_tcp = fun

    @property
    def target_port(self):
        return self._target_port

    @target_port.setter
    def target_port(self, port):
        self._target_port = port
        if self._communication_mode == CommunicationMode.TCP_SEND:
            self.soc.connect(self._target_port)

    def is_ready(self):
        port_is_ref = isinstance(self._target_port, CommunicationPort)
        message = """When using CommunicationMode.FUNCTION_CALL
        you must set target_port with a CommunicationPort instance
        When using CommunicationMode.TCP
        you must set target_port with a str like "tcp://localhost:5555" 
        """
        ref_ready = (port_is_ref and CommunicationMode.FUNCTION_CALL_SEND ==
                     self._communication_mode)
        tcp_ready = (CommunicationMode.TCP_SEND == self._communication_mode and self._listening)
        res = ref_ready or tcp_ready

        if not res:
            self._log.error(message)
        return res

    def send(self, data: dict):
        """send with req rep pattern"""
        if not self.is_ready():
            raise RuntimeError("{}: communication ports are not ready".format(self.port_name))
        elif self._communication_mode == CommunicationMode.FUNCTION_CALL_SEND:
            # print("{}: calliong receive for request".format(self.port_name))
            self._target_port.receive(data, respond_function=self.receive)
        elif self._communication_mode == CommunicationMode.TCP_SEND:
            self.soc.send(pickle.dumps(data))
            self.task = ReceiveThread(self.soc)
            self.task.start()
        else:
            raise AttributeError("communicationMode needs to be FUNCTION_CALL_SEND or TCP_SEND")


    def receive(self, data: dict, respond_function=None):
        """
        Arguments: 
            response_function:
                response callback source object of the
                request for a REQ-REP pattern 
                when in FUNCTION_CALL mode. if None, no Rep is possible
        """
        if respond_function:
                # print("{}: calling callback with respond function".format(self.port_name))
            self._receive_callback(data, respond_function=respond_function)
            print("1",data)
        else:
                # print("{}: calling callback without respond function".format(self.port_name))
            if self._communication_mode == CommunicationMode.TCP_SEND:
                self._receive_callback(data)

            #if self._communication_mode == CommunicationMode.TCP_RECV:
            #    self._receive_callback(data,respond_function=None)
            #    print("2", data)
            #    self.task.send_message=data
            if self._communication_mode == CommunicationMode.FUNCTION_CALL_RECV \
                    or self._communication_mode == CommunicationMode.FUNCTION_CALL_SEND:
                self._receive_callback(data)
                print("3", data)

    def receive_tcp(self,data: dict):
        if self._communication_mode == CommunicationMode.TCP_RECV:
            self._receive_callback_tcp(data)
            print("2", data)
            self.task.send_message (data)

    def _start_listening(self, address):
        """Only useful for TCP mode, starts a listening thread, 
        when this threads receives data it calls self.receive(data)
        in the reception thread"""
        return ListenThread(address)

    def _start_sending(self):
        if USE_PORT == "zmq":
            context = zmq.Context()
            soc = context.socket(zmq.REQ)
        elif USE_PORT == "socket":
            import socket
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            raise ValueError("USE_PORT needs to be zmq or socket")
        self._listening = True
        return soc


class ReceiveThread(threading.Thread):
    def __init__(self, soc):
        super(ReceiveThread, self).__init__()
        self.soc = soc
        self.data = None
        self.recv = False
    def run(self):
        self.data = pickle.loads(self.soc.recv())
        self.recv = True
        self.soc.close()



class ListenThread(threading.Thread):
    def __init__(self, address):
        super(ListenThread, self).__init__()
        r = parse("tcp://{target}:{port}", address)
        self.address = None
        self.target = r['target']
        self.port = r['port']
        self.data = {}
        self.recv = False
        self._send_message = None


    def _check_address(self):
        if self.target == 'localhost':
            return True
        try:
            host_bytes = self.target.split('.')
            valid = [int(b) for b in host_bytes]
            valid = [b for b in valid if b >= 0 and b <= 255]
            return len(host_bytes) == 4 and len(valid) == 4
        except:
            return False

    #@property
    #def send_message(self):
    #    return self._send_message

    #@send_message.setter
    def send_message(self, value):
        self._send_message = value

    def run(self):
        if USE_PORT == "zmq":
            if not self._check_address():
                raise ValueError("address isn't correct, it needs to be like "
                                 "tcp://localhost:5668 or tcp://127.0.0.1:5668 ")
            self.address = "tcp://{t}:{p}".format(t=self.target, p=self.port)
            context = zmq.Context()
            s = context.socket(zmq.REP)
            s.bind("tcp://*:{}".format(self.port))
            self.data = pickle.loads(s.recv())
            self.recv = True
            while not self._send_message:
                print(self._send_message)
                time.sleep(0.001)
            s.send(pickle.dumps(self._send_message))
            s.close()

        elif USE_PORT == "socket":
            import socket
            self.address = ('{}'.format(self.target), int(self.port))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(self.address)
            s.listen(1)
            ss, addr = s.accept()
            self.data = pickle.loads(ss.recv(512))
            self.recv = True
            while not self._send_message:
                time.sleep(0.001)
            ss.send(pickle.dumps(self._send_message))
            ss.close()
            s.close()
        else:
            raise ValueError("USE_PORT needs to be zmq or socket")
