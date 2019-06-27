function serverInitRequest() {
    password = document.getElementById("passInput").value;
    document.getElementById("passInput").value = "";
    rootUrl = window.location.origin;
    
    $.ajax({
        url: rootUrl + "/initServerMC",
        method: "POST",
        data: {pass: password},
        async: false,
        success: function(data) {
            returnData = JSON.parse(data);
            if(returnData.success == true) {
                alert(returnData.ip);
            } else {
                alert("Password Incorrect");
            }
        }
    });
}

document.getElementById("startButton").addEventListener("click", serverInitRequest);