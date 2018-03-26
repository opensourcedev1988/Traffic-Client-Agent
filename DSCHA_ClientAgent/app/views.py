import json
import logging
from UDPTraffic.tasks import start_udp_traffic, start_udp_server
from celery.task.control import revoke
from django.views.generic import DeleteView, View
from django.urls import reverse
from celery import uuid
from django.shortcuts import render
from .models import TCPTraffic, UDPTraffic, UDPServer
from django.views.generic.edit import CreateView
from django.http import HttpResponse
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .serializers import UDPTrafficSerializer, UDPServerSerializer


logger = logging.getLogger(__name__)


# Create your views here.
def main_page(request):
    return render(request, "index.html")


class ClientView(View):

    def get(self, request):

        tcp_traffic = TCPTraffic.objects.all()
        udp_traffic = UDPTraffic.objects.all()

        context = {
            "tcps": tcp_traffic,
            "udps": udp_traffic
        }

        return render(request, "client.html", context)

    def post(self, request):
        dst_ip = request.POST['dst_ip']
        dst_port = request.POST['dst_port']
        packet_per_second = request.POST['packet_per_second']

        udp_traffic = UDPTraffic(dst_ip=dst_ip, dst_port=dst_port,
                                 packet_per_second=packet_per_second,)
        udp_traffic.save()
        logger.info("Create UDP traffic object")

        return HttpResponse(json.dumps({"dst_ip": dst_ip}))


class ServerView(View):

    def get(self, request):

        # Retrieve data base and display existing client info or
        # create a new one
        return render(request, "server.html")

    def post(self, request):

        pass


class CreateTCPTraffic(CreateView):
    model = TCPTraffic
    fields = ['dst_ip','dst_port', 'count',
              'exclude', 'ip_version', 'data']
    # template_name = 'create-tcp.html'

    def get_success_url(self):
        return reverse('client')


class UDPTrafficListCreateApiView(ListCreateAPIView):
    serializer_class = UDPTrafficSerializer

    def get_queryset(self):
        return UDPTraffic.objects.all()

    def perform_create(self, serializer):
        data = serializer.validated_data
        if 'is_start' in data and data['is_start'] is True:
            celery_id = uuid()
            serializer.validated_data['celery_id'] = celery_id
            start_udp_traffic.apply_async((serializer.validated_data['dst_ip'], serializer.validated_data['dst_port'], serializer.validated_data['packet_per_second']),
                                          task_id=celery_id)
        serializer.save()


class UDPTrafficDetailApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = UDPTrafficSerializer
    queryset = UDPTraffic.objects.all()

    def patch(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        model_data = serializer.data
        if 'is_start' in data:
            if model_data['is_start'] is True and data['is_start'] is False:
                request.data['celery_id'] = ''
                logging.info("Stop UDP Traffic, celery id: %s" % model_data['celery_id'])
                revoke(model_data['celery_id'], terminate=True, signal="SIGKILL")
            elif model_data['is_start'] is False and data['is_start'] is True:
                celery_id = uuid()
                request.data['celery_id'] = celery_id
                start_udp_traffic.apply_async((model_data['dst_ip'],
                                               model_data['dst_port'],
                                               model_data['packet_per_second']),
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