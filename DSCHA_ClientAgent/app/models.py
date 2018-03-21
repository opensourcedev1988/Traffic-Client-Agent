from django.db import models


# Create your models here.
class UDPTraffic(models.Model):

    dst_ip = models.GenericIPAddressField()
    dst_port = models.IntegerField()
    packet_per_second = models.BigIntegerField()
    is_start = models.BooleanField(default=False)
    celery_id = models.CharField(max_length=1024, blank=True)

    def __str__(self):

        return "VIP: {}:{}".format(self.dst_ip, self.dst_port)

class UDPServer(models.Model):
    ip = models.GenericIPAddressField()
    port = models.IntegerField()
    is_start = models.BooleanField(default=False)
    celery_id = models.CharField(max_length=1024, blank=True)

    def __str__(self):

        return "Server: {}:{}".format(self.ip, self.port)


class TCPTraffic(models.Model):

    dst_ip = models.GenericIPAddressField()
    dst_port = models.IntegerField()
    count = models.IntegerField()
    exclude = models.CharField(max_length=300, blank=True)
    ip_version = models.IntegerField()
    packet_per_second = models.BigIntegerField()
    data = models.TextField(blank=True, null=True)
    is_start = models.BooleanField(default=False)
    celery_id = models.CharField(max_length=1024)

    def __str__(self):

        return "Destination: {}:{}".format(self.dst_ip, self.dst_port)
