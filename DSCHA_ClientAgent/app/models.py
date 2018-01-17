from django.db import models


# Create your models here.
class UDPTraffic(models.Model):

    dst_ip = models.GenericIPAddressField()
    dst_port = models.IntegerField()
    srv_ip = models.GenericIPAddressField()
    srv_port = models.IntegerField()
    packet_pause = models.FloatField()
    count = models.IntegerField()
    port_start = models.IntegerField()
    is_start = models.BooleanField(default=False)

    def __str__(self):

        return "VIP: {}:{} Server: {}:{}".format(self.dst_ip, self.dst_port,
                                                 self.srv_ip, self.srv_port)


class TCPTraffic(models.Model):

    dst_ip = models.GenericIPAddressField()
    dst_port = models.IntegerField()
    count = models.IntegerField()
    exclude = models.CharField(max_length=300, blank=True)
    ip_version = models.IntegerField()
    data = models.TextField(blank=True, null=True)
    is_start = models.BooleanField(default=False)

    def __str__(self):

        return "Destination: {}:{}".format(self.dst_ip, self.dst_port)
