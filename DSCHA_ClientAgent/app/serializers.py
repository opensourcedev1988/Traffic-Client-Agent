from rest_framework import serializers
from .models import TCPTraffic, UDPTraffic


class TCPTrafficSerializer(serializers.ModelSerializer):

    class Meta:
        model = TCPTraffic
        fields = ('dst_ip', 'dst_port', 'count', 'exclude', 'ip_version', 'data', 'is_start')


class UDPTrafficSerializer(serializers.ModelSerializer):

    class Meta:
        model = UDPTraffic
        fields = ('dst_ip', 'dst_port', 'packet_per_second', 'is_start')