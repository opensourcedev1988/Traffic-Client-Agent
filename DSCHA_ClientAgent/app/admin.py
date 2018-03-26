from django.contrib import admin
from app.models import TCPTraffic, UDPTraffic, UDPServer

# Register your models here.
admin.site.register(TCPTraffic)
admin.site.register(UDPTraffic)
admin.site.register(UDPServer)