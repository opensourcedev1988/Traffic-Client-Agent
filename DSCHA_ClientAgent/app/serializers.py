from rest_framework import serializers
from .models import TCPTraffic, UDPTraffic, UDPServer


class TCPTrafficSerializer(serializers.ModelSerializer):

    class Meta:
        model = TCPTraffic
        fields = ('id', 'dst_ip', 'dst_port', 'count', 'exclude', 'ip_version', 'data', 'is_start')


class UDPTrafficSerializer(serializers.ModelSerializer):

    class Meta:
        model = UDPTraffic
        fields = ('id', 'dst_ip', 'dst_port', 'packet_per_second', 'is_start', 'celery_id')

class UDPServerSerializer(serializers.ModelSerializer):

    class Meta:
        model = UDPServer
        fields = ('id', 'ip', 'port', 'is_start', 'celery_id')