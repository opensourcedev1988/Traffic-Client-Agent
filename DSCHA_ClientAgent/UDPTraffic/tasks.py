from celery import task, shared_task, uuid
from UDPTraffic.udptraffic import UDPTraffic
from UDPTraffic.udpserver import UDPEchoServer


@shared_task
def start_udp_traffic(vip, vport, packet_rate, app_id):
    """
    To start a task, call
    start_udp_traffic.apply_async((vip, vport, packet_rate), task_id = uuid())
    :param vip:
    :param vport:
    :param packet_rate:
    :param app_id:
    :return:
    """
    udp = UDPTraffic(vip, vport, int(packet_rate))
    # Use source ports 20000 - 35000
    udp.controller_app_id = app_id
    udp.udp_port_range_start = 20000
    udp.udp_port_range_stop = 35000
    udp.start()


@shared_task
def start_udp_server(srv_ip, srv_port):
    """
    To start this udp server, call
    start_udp_server.apply_async((vip, vport, packet_rate), task_id = uuid())
    :param srv_ip:
    :param srv_port:
    :return:
    """
    udp_srv = UDPEchoServer(srv_ip, srv_port)
    udp_srv.start()
    print("UDP server started")