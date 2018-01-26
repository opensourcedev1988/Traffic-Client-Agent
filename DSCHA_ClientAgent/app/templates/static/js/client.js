$(function() {
    $('#createTCPTrafficSubmit').on("click", function () {
        var csrfCookie = document.getElementsByName("csrfmiddlewaretoken")[0].value;
        var dstIP = $('#dstIP')[0].value;
        var dstPort = $('#dstPort')[0].value;
        var srvIP = $('#srvIP')[0].value;
        var srvPort = $('#srvPort')[0].value;
        var packetPause = $('#packetPause')[0].value;
        var connectionCount = $('#connectionCount')[0].value;
        var portStart = $('#portStart')[0].value;

        $.ajax({
            url:'/client/',
            type: "POST",
            dataType: "json",
            data: {dst_ip: dstIP, dst_port: dstPort, srv_ip: srvIP, srv_port: srvPort,
                packet_pause: packetPause, count: connectionCount, port_start: portStart, csrfmiddlewaretoken: csrfCookie},
            success:function(response){
                console.log(response);
            },
            complete:function(){},
            error:function (xhr, textStatus, thrownError){}
        });
    });
});

