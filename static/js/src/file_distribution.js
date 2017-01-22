/**
 * Created by TaoHu on 2017/1/22.
 */

$("#UploadObj").click(function () {
    var upload_obj = $("#file-obj")[0].files[0];
    var target_host = $('#target_host').val();
    var target_path = $('#target_path').val();
    var source_file = $('#source_file').val();

    if (target_host) {
        var form = new FormData();
        form.append("upload_obj", upload_obj);  // 生成一个包含 name & value 的表单元素
        form.append('target_host', target_host);
        form.append('target_path', target_path);
        form.append('source_file', source_file);

        $.ajax({
            type: 'POST',
            url: '/eyes/file_distribution/',
            data: form,
            cache: false,
            processData: false,  // tell jQuery not to process the data
            contentType: false,  // tell jQuery not to set contentType
            success: function (data) {
                var msg = 'total' + data;
                $('#distribution_answer').text(msg);
                for (var i = 0; i < data; i++) {
                    Get_upload_result();
                }
            },
            error: function (arg) {
            }
        })
    } else {
        $('#distribution_answer').text('请输入目标主机IP');
    }
});

function Get_upload_result() {
    $.ajax({
        type: 'GET',
        url: '/eyes/get_distribution_res/',
        traditional: true,
        dataType: "json",
        success: function (data) {
            $('#distribution_answer').append(data);
        },
        complete: function () {
            // get_command_result();
        },
        error: function (error_data) {
            // console.log(error_data)
        }
    });
}