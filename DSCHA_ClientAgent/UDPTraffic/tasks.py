from celery import task, shared_task, uuid
from celery.task.control import revoke
from UDPTraffic.udptraffic import UDPTraffic


@shared_task
def start_udp_traffic(vip, vport, packet_rate):
    """
    To start a task, call
    start_udp_traffic.apply_async((vip, vport, packet_rate), task_id = uuid())
    :param vip:
    :param vport:
    :param packet_rate:
    :return:
    """
    u = UDPTraffic(vip, vport, int(packet_rate))
    # Use source ports 20000 - 35000
    u.udp_port_range_start = 20000
    u.udp_port_range_stop = 35000
    u.start()


def stop_udp_traffic(task_id):

    revoke(task_id, terminate=True, signal="SIGKILL")