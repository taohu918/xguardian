/**
 * Created by TaoHu on 2017/1/22.
 */

$('#exe_mth').change(function () {
    var $panel = $('#ip_str');
    if (this.value == 'exe_mth_salt') {
        $panel.hide();
    } else {
        $panel.show();
    }
});

function post_cmds() {
    var cmds_str = $('#cmds_str').val();
    var ip_str = $('#ip_str').val();
    if (cmds_str && ip_str) {
        $.ajax({
            type: 'POST',
            url: '/eyes/post_cmds/',
            traditional: true,
            dataType: "json",
            data: {'cmds_str': cmds_str, 'ip_str': ip_str},
            success: function (data) {
                var msg = 'total' + data;
                $('#answer_area').text(msg);
                for (var i = 0; i < data; i++) {
                    get_command_result();
                }

            },
            error: function (error_data) {
                // console.log(error_data)
            }
        });//end ajax
    } else {
        $('#answer_area').text('请输入正确的命令和IP');
    }
}//end function


function get_command_result() {
    $.ajax({
        type: 'GET',
        url: '/eyes/get_cmds_res/',
        traditional: true,
        dataType: "json",
        success: function (data) {
            $('#answer_area').append(data);
        },
        complete: function () {
            // get_command_result();
        },
        error: function (error_data) {
            // console.log(error_data)
        }
    });
}