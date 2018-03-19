from django.views.generic import DeleteView, View
from django.urls import reverse
from django.shortcuts import render
from .models import TCPTraffic, UDPTraffic
from django.views.generic.edit import CreateView
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import TCPTrafficSerializer, UDPTrafficSerializer
import json


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
        print("Create UDP traffic object")

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


@api_view(['GET'])
def UDPTraffic_RestAPI(request):
    if request.method == 'GET':
        udp_traffics = UDPTraffic.objects.all()
        udp_serializer = UDPTrafficSerializer(udp_traffics, many=True)
        return Response(udp_serializer.data)


@api_view(['GET'])
def TCPTraffic_RestAPI(request):
    if request.method == 'GET':
        tcp_traffics = TCPTraffic.objects.all()
        tcp_serializer = TCPTrafficSerializer(tcp_traffics, many=True)
        return Response(tcp_serializer.data)
