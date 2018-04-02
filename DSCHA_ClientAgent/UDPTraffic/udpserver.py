#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import socketserver


class MyUDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        socket.sendto(data, self.client_address)


class UDPEchoServer(object):

    def __init__(self, ip, port):

        self.ip = ip
        self.port = port
        self.server = None

    def start(self):

        self.server = socketserver.UDPServer((self.ip, self.port), MyUDPHandler)
        print("Start udp server %s:%s" % (self.ip, self.port))
        self.server.serve_forever()


# import socket
#
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
# server_address = '10.2.1.100'
# server_port = 11242
#
# server = (server_address, server_port)
# sock.bind(server)
# print("Listening on " + server_address + ":" + str(server_port))
#
# while True:
#     payload, client_address = sock.recvfrom(4096)
#     print ("Data: %s" % payload)
#     print("Echoing data back to " + str(client_address))
#     sent = sock.sendto(payload, client_address)
