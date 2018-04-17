import logging
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .serializers import UDPTrafficSerializer, UDPServerSerializer
from UDPTraffic.tasks import start_udp_traffic, start_udp_server
from celery.task.control import revoke
from .models import TCPTraffic, UDPTraffic, UDPServer
from celery import uuid

logger = logging.getLogger(__name__)


class UDPTrafficListCreateApiView(ListCreateAPIView):
    serializer_class = UDPTrafficSerializer

    def get_queryset(self):
        return UDPTraffic.objects.all()

    def perform_create(self, serializer):
        # data = serializer.validated_data
        # logger.debug(data)
        # if 'is_start' in data and data['is_start'] is True:
        #     celery_id = uuid()
        #     serializer.validated_data['celery_id'] = celery_id
        #     start_udp_traffic.apply_async((serializer.validated_data['dst_ip'],
        #                                    serializer.validated_data['dst_port'],
        #                                    serializer.validated_data['packet_per_second']),
        #                                   task_id=celery_id)
        serializer.save()


class UDPTrafficDetailApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = UDPTrafficSerializer
    queryset = UDPTraffic.objects.all()

    def patch(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        model_data = serializer.data
        logger.debug("Patch model data:")
        logger.debug(model_data)
        logger.debug(data)
        if 'is_start' in data:
            if model_data['is_start'] is True and data['is_start'] is False:
                request.data['celery_id'] = ''
                logger.info("Stop UDP Traffic, celery id: %s" % model_data['celery_id'])
                revoke(model_data['celery_id'], terminate=True, signal="SIGKILL")
            elif model_data['is_start'] is False and data['is_start'] is True:
                celery_id = uuid()
                request.data['celery_id'] = celery_id
                start_udp_traffic.apply_async((model_data['dst_ip'],
                                               model_data['dst_port'],
                                               model_data['packet_per_second'],
                                               model_data['id']),
                                              task_id=celery_id)
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        model_data = serializer.data
        # Stop server celery task if it's running
        if 'is_start' in model_data and model_data['is_start'] is True:
            logger.info("Stop UDP traffic, celery id: %s" % model_data['celery_id'])
            revoke(model_data['celery_id'], terminate=True, signal="SIGKILL")
        return self.destroy(request, *args, **kwargs)


class UDPServerListCreateApiView(ListCreateAPIView):
    serializer_class = UDPServerSerializer

    def get_queryset(self):
        return UDPServer.objects.all()

    def perform_create(self, serializer):
        data = serializer.validated_data
        if 'is_start' in data and data['is_start'] is True:
            celery_id = uuid()
            serializer.validated_data['celery_id'] = celery_id
            start_udp_server.apply_async((serializer.validated_data['ip'], serializer.validated_data['port']),
                                         task_id=celery_id)
        serializer.save()


class UDPServerDetailApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = UDPServerSerializer
    queryset = UDPServer.objects.all()

    def patch(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        model_data = serializer.data
        if 'is_start' in data:
            if model_data['is_start'] is True and data['is_start'] is False:
                request.data['celery_id'] = ''
                logger.info("Stop UDP server, celery id: %s" % model_data['celery_id'])
                revoke(model_data['celery_id'], terminate=True, signal="SIGKILL")
            elif model_data['is_start'] is False and data['is_start'] is True:
                celery_id = uuid()
                request.data['celery_id'] = celery_id
                start_udp_server.apply_async((model_data['ip'],
                                              model_data['port']),
                                             task_id=celery_id)
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        model_data = serializer.data
        # Stop server celery task if it's running
        if 'is_start' in model_data and model_data['is_start'] is True:
            logger.info("Stop UDP server, celery id: %s" % model_data['celery_id'])
            revoke(model_data['celery_id'], terminate=True, signal="SIGKILL")
        return self.destroy(request, *args, **kwargs)