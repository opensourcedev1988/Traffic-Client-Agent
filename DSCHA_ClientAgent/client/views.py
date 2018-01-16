from django.views.generic import DeleteView, View
from django.urls import reverse
from django.shortcuts import render
from .models import TCPTraffic, UDPTraffic
from django.views.generic.edit import CreateView


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

        pass


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
    template_name = 'create-tcp.html'

    def get_success_url(self):
        return reverse('client')