#!/bin/env python
"""
UDPTraffic
_____  __________ ________     ________               ______          ______
__  / / /___  __ \___  __ \    ___  __ \______ __________  /_____________  /
_  / / / __  / / /__  /_/ /    __  /_/ /_  __ \_  ___/__  //_/__  ___/__  /
/ /_/ /  _  /_/ / _  ____/     _  _, _/ / /_/ // /__  _  ,<   _(__  )  /_/
\____/   /_____/  /_/          /_/ |_|  \____/ \___/  /_/|_|  /____/  (_)


This module provides a simple way to send a measured amount of UDP traffic through the BIG-IP.
It provides both the server and client which are both intended to run on CS1. If desired, the
helper methods (setup_bigIP and cleanup_bigip) can be used to configure the pool, node, and
virtual server to process the UDP traffic.

Sent UDP packets contain a sequence ID. The server uses the received sequence ID's to determine
what packets were dropped. The UDP source port will change for each sent packet to help distribute
the load across TMMs.

For questions, comments, enhancements, or general tips at being awesome, email robz@f5.com
"""
import sys
import time
import errno
import threading
import select
import configparser
import requests
import socket
import datetime
import multiprocessing
from global_var import *


class UDPPacket(object):

    def __init__(self, data):
        self.data = data
        self.ack = False


class UDPTraffic(object):
    """
    The main interface for passing traffic. Instantiate this class to get the party started.

    .. python::
    Example Usage
    from udp_traffic import UDPTraffic
    u = UDPTraffic('10.1.1.125', 1234, '10.1.1.1', 1234)
    u.setup_bigip('10.145.192.3', 'kiddie_pool', 'serve_o_tron')
    u.packet_pause = 0.25   # Send a packet every quarter second
    # Use source ports 12000 - 12500
    u.udp_port_range_start = 12000
    u.udp_port_range_stop = 12500
    u.start()
    # Do something important here
    u.stop()
    u.cleanup_bigip()
    (missing_packets, offline_time) = u.analyze_results()
    for missing in missing_packets:
       print missing.start_seq  # The first packet ID dropped
       print missing.end_seq    # The last packet ID dropped
       print missing.last_timestamp # Timestamp of the first missing packet
       print missing.resume_timestamp # Timestamp of when traffic resumed
    """
    MAX_SEQUENCE = 2 ** 31 - 1

    def __init__(self, destination_ip, destination_port, packet_rate):
        """
        Constructor
        :param destination_ip: (string) IP address to send traffic to (BIG-IP VIP)
        :param destination_port: (integer) Port to send traffic to
        :param server_ip: (string) The local IP address the UDP server should listen on
        :param server_port: (integer) The local port to lisen for UDP packets on
        :return: None
        """
        # The IP/port where the client will send traffic (presumably a BIG-IP VIP)
        self.destination_ip = destination_ip
        self.destination_port = destination_port

        self.report_stat_thread = None
        self.client_read_thread = None
        if sys.platform == "linux" or sys.platform == "linux2":
            self.epoll_obj = select.epoll()
            self.connections = {}
        else:
            self.epoll_obj = None
        self.client_read_timeout = 2
        self.lock = threading.RLock()
        self.sending_client_data = False
        self.read_client_data = False
        self.udp_port_range_start = 20000
        self.udp_port_range_stop = 40000
        self.current_port = self.udp_port_range_start
        self.packet_sequence = 1
        self.report_timer = time.time()
        self.packet_rate = packet_rate
        self.udp_data_dictionary = {}
        self.stat_queue = multiprocessing.Queue()
        self.controller_app_id = None

        # Configure logging
        try:
            import tcutils.common as tc
            self._log = tc.stdout_logger("udp_traffic.log")
        except ImportError:
            # running outside ITE, set own logger
            import logging
            self._log = logging.getLogger("udp_traffic.log")
            self._log.setLevel(logging.INFO)
            log_handler = logging.StreamHandler(sys.stdout)
            log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s| %(message)s",
                                                       datefmt="%H:%M:%S"))
            self._log.addHandler(log_handler)

    def __enter__(self):
        """
        Context manager entry point for scripts that use python's 'with' declaration.
        :return: An instance of the UDPTraffic class
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Perform cleanup if the module was instantuated using a context manager (aka 'with')
        :param exc_type: Exception Type
        :param exc_val: Exception Value
        :param exc_tb: Exception Traceback
        :return: None
        """
        self.stop()

    @property
    def log(self):
        """
        Access the logging interface. Call .info(), .error() or .debug() to log accordingly.
            Returns a logging handle.
        """
        return self._log

    def start(self):
        """
        Start sending UDP traffic to the previously configured destination.
         Packets are sent as fast as possible. If throttling is desired,
         set self.packet_pause to the number of seconds to pause between sends.
        """

        # Clear out our dictionary of results
        # dict data structure {<data>: (<packet obj>, <send time>, <ack time>)}
        self.udp_data_dictionary = {}
        self.connections = {}
        # Start the client thread
        self.sending_client_data = True
        self.read_client_data = True
        # self.client_thread = threading.Thread(target=self._send_client_traffic)
        # self.client_thread.daemon = True
        # self.client_thread.start()
        if self.epoll_obj:
            self.client_read_thread = threading.Thread(target=self._read_server_msg)
            self.client_read_thread.daemon = True
            self.client_read_thread.start()
        self.report_stat_thread = threading.Thread(target=self._report_stat)
        self.report_stat_thread.start()
        self._send_client_traffic()

    def stop(self):
        """
        Stop sending traffic.
        :return: None
        """
        if self.sending_client_data:
            self.sending_client_data = False
        if self.epoll_obj:
            time.sleep(self.client_read_timeout)
            self.read_client_data = False
            self.epoll_obj.close()

    def _send_client_traffic(self):
        """
        Private method
        This is the thread which sends traffic. It will operate until self.sending_client_data is
        set to False by UDPTraffic.stop(). Each packet will be sent from a new source port to
        help distribute load across TMMs.
        :return: None
        """
        self.packet_sequence = 1
        self.current_port = self.udp_port_range_start

        check_list = [[] for i in range(self.client_read_timeout+1)]
        cur_pt = 0
        check_pt = None

        self.log.info("Starting client traffic thread")
        self.log.info("Traffic destination: %s:%d" % (self.destination_ip,
                                                      self.destination_port))
        current_time = time.time()
        # Send packets until the main thread tells us to stop.
        packet_count = 0
        while self.sending_client_data is True:

            while time.time() - current_time < 1:
                if packet_count >= self.packet_rate:
                    break

                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # Send from the specified source port
                try:
                    sock.bind(('0.0.0.0', self.current_port))
                except socket.error as err:

                    # IP/port combo currently in use, skip it.
                    if err == errno.EADDRINUSE:
                        self.log.error("Source port (%d) in use - skipping." %
                                       self.current_port)
                        sock.close()
                        self.current_port += 1

                        # Wrap the UDP source port
                        if self.current_port == self.udp_port_range_stop:
                            self.current_port = self.udp_port_range_start

                        # Jump back to the top of the loop, skipping the send/pause logic
                        continue
                    else:
                        raise

                self.udp_data_dictionary[str(self.packet_sequence)] = [time.time(), None, sock]
                # Register this socket to epoll
                if self.epoll_obj:
                    self.epoll_obj.register(sock.fileno(), select.EPOLLIN)
                    # Update connections dict
                    self.connections[sock.fileno()] = sock
                # Packet is a stringified version of the current sequence number
                sock.sendto(bytes(str(self.packet_sequence), "utf-8"),
                            0, (self.destination_ip, self.destination_port))
                check_list[cur_pt].append(str(self.packet_sequence))

                self.packet_sequence += 1
                self.current_port += 1

                # Wrap the UDP source port
                if self.current_port == self.udp_port_range_stop:
                    self.current_port = self.udp_port_range_start

                # Wrap the sequence number
                if self.packet_sequence > self.MAX_SEQUENCE:
                    self.packet_sequence = 1

                packet_count += 1

            if not self.epoll_obj:
                open_sockets = [socket for t1, t2, socket in self.udp_data_dictionary.values()]
                while len(open_sockets) > 500:
                    fds = select.select(open_sockets[:501], [], [], 0)
                    if fds[0]:
                        for s in fds[0]:
                            recv_data = str(s.recv(1024), "utf-8")
                            self.udp_data_dictionary[recv_data][1] = time.time()
                    open_sockets = open_sockets[501:]
                if open_sockets:
                    fds = select.select(open_sockets, [], [], 0)
                    if fds[0]:
                        for s in fds[0]:
                            recv_data = str(s.recv(1024), "utf-8")
                            self.udp_data_dictionary[recv_data][1] = time.time()

            if time.time() - current_time >= 1:
                cur_pt += 1
                if check_pt is None and cur_pt < self.client_read_timeout + 1:
                    pass
                else:
                    if cur_pt == self.client_read_timeout + 1:
                        cur_pt = 0
                    if check_pt is None or check_pt == self.client_read_timeout + 1:
                        check_pt = 0
                    latency = 0.0
                    check_pkt_count = 0
                    drop_packet = 0
                    avg_latency = -1
                    total_bits = 0
                    self.log.debug("=========Check Data=======")
                    self.log.debug(check_list[check_pt])
                    self.log.debug("=========Check Dict=======")
                    self.log.debug(self.udp_data_dictionary)
                    for data in check_list[check_pt]:
                        total_bits += sys.getsizeof(data)
                        if self.udp_data_dictionary[data][1] is None:
                            drop_packet += 1
                        else:
                            latency += self.udp_data_dictionary[data][1] - self.udp_data_dictionary[data][0]
                            check_pkt_count += 1
                        dict_socket = self.udp_data_dictionary[data][2]
                        del self.udp_data_dictionary[data]
                        if self.epoll_obj:
                            self.epoll_obj.unregister(dict_socket.fileno())
                            del self.connections[dict_socket.fileno()]
                        dict_socket.close()
                    if check_pkt_count != 0:
                        avg_latency = latency/check_pkt_count
                    self.log.info("====================STAT===================")
                    self.log.info("Total bytes sent: %s" % total_bits)
                    self.log.info("Total packets sent: %s" % len(check_list[check_pt]))
                    self.log.info("Total packets received: %s" %
                                  (len(check_list[check_pt]) - drop_packet))
                    self.log.info("Total drop packets: %s" % drop_packet)
                    self.log.info("Average latency: %.4F" % avg_latency)
                    self.stat_queue.put({"app_id": self.controller_app_id,
                                         "byte_sent": total_bits,
                                         "packets_sent": len(check_list[check_pt]),
                                         "packets_receive": len(check_list[check_pt]) - drop_packet,
                                         "drop_packets": drop_packet,
                                         "avg_latency": avg_latency,
                                         "pkt_time": str(datetime.datetime.now())})
                    check_list[check_pt] = []
                    check_pt += 1
                current_time = time.time()
                packet_count = 0

    def _read_server_msg(self):
        self.log.info("Start client reading thread")
        while self.read_client_data:
            if self.epoll_obj:
                # Linux, using epoll the poll data
                events = self.epoll_obj.poll(0)
                for fd, event in events:
                    if event & select.EPOLLIN:
                        recv_data = str(self.connections[fd].recv(1024), "utf-8")
                        self.udp_data_dictionary[recv_data][1] = time.time()
            else:
                # Not linux, sleep to prevent throttling
                time.sleep(0.1)

    def _report_stat(self):
        self.log.info("Start posting stat to harness controller")
        config = configparser.ConfigParser()
        config.read(harness_config_path)
        controller_ip = config.get("harness", "controller")
        url = "http://%s:8000/api/v1/UDPTrafficStat/" % controller_ip

        while self.sending_client_data is True:
            if time.time() - self.report_timer > 5:
                data_list = []
                try:
                    while self.stat_queue.empty() is False:
                        data_list.append(self.stat_queue.get())
                except IOError:
                    pass
                r = requests.post(url,
                                  json={"data_list": data_list})
                # if r.status_code == 201:
                #     self.log.info("Post UDP traffic stats success")
                # else:
                #     self.log.error("Post UDP traffic stats fail")
                #     self.log.error(r.text)
                self.report_timer = time.time()
            time.sleep(0.01)


# def get_parser():
#     parser = OptionParser(usage="usage: %prog [options] packet rate(s)")
#
#     return parser
#
# if __name__ == "__main__":
#
#     parser = get_parser()
#     opts, args = parser.parse_args()
#     if not args:
#         parser.error("Specify packet rate (per second).")
#     # Remove letter R from runid because Testrail API want only numeric value
#     speed = args[0]
#
#     u = UDPTraffic('10.1.2.10', 14589, int(speed))
#     # Use source ports 12000 - 12500
#     u.udp_port_range_start = 20000
#     u.udp_port_range_stop = 35000
#     u.start()
#     # Do something important here
#     time.sleep(300)
#     u.stop()