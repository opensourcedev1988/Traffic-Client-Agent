from django.contrib import admin
from client.models import TCPTraffic, UDPTraffic

# Register your models here.
admin.site.register(TCPTraffic)
admin.site.register(UDPTraffic)