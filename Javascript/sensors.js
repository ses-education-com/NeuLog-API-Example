// JScript source code
function GetRouterData(Command, ResponseDiv) {
    $("#" + ResponseDiv).text("Command: " + Command);
    $("#_" + ResponseDiv).text("URL: " + 'http://localhost:'+$('#input_port_number').val() + '/NeuLogAPI?' + Command);
    $("#__" + ResponseDiv).text("Pending...");
    $.ajax({
        url: 'http://localhost:'+$('#input_port_number').val() + '/NeuLogAPI?' + Command,
        type: 'GET',
        timeout: 3000,
        error: function (a, b, c) {
            $("#__" + ResponseDiv).text("Error!");
        },
        success: function (data) {
            //$("#" + ResponseDiv).text("Command: "+Command);
            $("#__" + ResponseDiv).text("Result: " + data);
        }
    });
}

var FormCommand,FormResponse;

$(document).ready(function () {

    $('#btn_version').click(function () {
        FormCommand = "GetServerVersion";
        FormResponse = "res_version";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_status').click(function () {
        FormCommand = "GetSeverStatus";
        FormResponse = "res_status";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_get_values').click(function () {
        FormCommand = 'GetSensorValue:' + $('#input_get_values').val()
        FormResponse = "res_get_values";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_reset_sensor').click(function () {
        FormCommand = 'ResetSensor:' + $('#input_reset_sensor').val()
        FormResponse = "res_reset_sensor";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_set_dir').click(function () {
        FormCommand = 'SetPositiveDirection:' + $('#input_set_dir').val()
        FormResponse = "res_set_dir";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_start_exp').click(function () {
        FormCommand = 'StartExperiment:' + $('#input_start_exp').val()
        FormResponse = "res_start_exp";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_stop_exp').click(function () {
        FormCommand = 'StopExperiment'
        FormResponse = "res_stop_exp";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_get_samples').click(function () {
        FormCommand = 'GetExperimentSamples'
        FormResponse = "res_get_samples";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_get_samples_clear').click(function () {
        FormCommand = 'GetExperimentSamplesAndClear'
        FormResponse = "res_get_samples_clear";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_set_range').click(function () {
        FormCommand = 'SetSensorRange:' + $('#input_set_range').val()
        FormResponse = "res_set_range";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_set_id').click(function () {
        FormCommand = 'SetSensorsID:' + $('#input_set_id').val()
        FormResponse = "res_set_id";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_set_rfid').click(function () {
        FormCommand = 'SetRFID:' + $('#input_set_rfid').val()
        FormResponse = "res_set_rfid";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_start_usb').click(function () {
        FormCommand = 'StartUSBSerialConnection'
        FormResponse = "res_start_usb";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_start_bt').click(function () {
        FormCommand = 'StartBluetoothConnection'
        FormResponse = "res_start_bt";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_get_usb_status').click(function () {
        FormCommand = 'GetUSBSerialStatus'
        FormResponse = "res_get_usb_status";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_get_bt_status').click(function () {
        FormCommand = 'GetBluetoothStatus'
        FormResponse = "res_get_bt_status";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_exit').click(function () {
        FormCommand = 'ExitAPI'
        FormResponse = "res_exit";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_gate1').click(function () {
        FormCommand = 'StartGateExp:[1],' + $('#input_gate1').val()
        FormResponse = "res_gate_exp";
        GetRouterData(FormCommand, FormResponse);
    });
    $('#btn_gate2').click(function () {
        FormCommand = 'StartGateExp:[2],' + $('#input_gate2').val()
        FormResponse = "res_gate_exp";
        GetRouterData(FormCommand, FormResponse);
    });
    $('#btn_gate3').click(function () {
        FormCommand = 'StartGateExp:[3],' + $('#input_gate3').val()
        FormResponse = "res_gate_exp";
        GetRouterData(FormCommand, FormResponse);
    });
    $('#btn_gate4').click(function () {
        FormCommand = 'StartGateExp:[4],' + $('#input_gate4').val()
        FormResponse = "res_gate_exp";
        GetRouterData(FormCommand, FormResponse);
    });
    $('#btn_gate5').click(function () {
        FormCommand = 'StartGateExp:[5],' + $('#input_gate5').val()
        FormResponse = "res_gate_exp";
        GetRouterData(FormCommand, FormResponse);
    });
    $('#btn_gate6').click(function () {
        FormCommand = 'StartGateExp:[6],' + $('#input_gate6').val()
        FormResponse = "res_gate_exp";
        GetRouterData(FormCommand, FormResponse);
    });

    $('#btn_read_gate').click(function () {
        FormCommand = 'ReadGateSamples';
        FormResponse = "res_gate_samples";
        GetRouterData(FormCommand, FormResponse);
    });

});

