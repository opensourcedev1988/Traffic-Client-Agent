$(function() {
    $('#createUDPTrafficSubmit').on("click", function () {
        var csrfCookie = document.getElementsByName("csrfmiddlewaretoken")[0].value;
        var dstIP = $('#dstIP')[0].value;
        var dstPort = $('#dstPort')[0].value;
        var packetPerSecond = $('#packetPerSecond')[0].value;

        $.ajax({
            url:'/client/',
            type: "POST",
            dataType: "json",
            data: {dst_ip: dstIP, dst_port: dstPort,
                   packet_per_second: packetPerSecond, csrfmiddlewaretoken: csrfCookie},
            success:function(response){
                console.log(response);
            },
            complete:function(){},
            error:function (xhr, textStatus, thrownError){}
        });
    });
});

