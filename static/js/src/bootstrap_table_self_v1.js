/**
 * Created by TaoHu on 2017/1/19.
 */

var $table = $('#table'),
    $remove = $('#remove'),
    selections = [];
function initTable() {
    // editable: true 时, 会自动在 <td> 下生成 <a data-name=filed> 样式标签
    $table.bootstrapTable({
        height: getHeight(),
        columns: [
            [
                {
                    title: '全选',
                    field: 'state',
                    checkbox: true,
                    rowspan: 2,
                    align: 'center',
                    valign: 'middle'
                },
                {
                    title: 'User ID',
                    field: 'id',
                    rowspan: 2, // 占行 2
                    align: 'center',
                    valign: 'middle',
                    sortable: true,
                    footerFormatter: totalTextFormatter
                },
                {
                    title: '账号状态',
                    field: 'is_active',
                    rowspan: 2,
                    editable: true,
                    align: 'center',
                    valign: 'middle'
                },
                {
                    title: 'Account Detail',
                    //rowspan: 1,   // 默认占一行
                    colspan: 3,
                    align: 'center'
                }
            ],
            [
                {
                    field: 'email',
                    title: 'Login Name',
                    sortable: true,
                    align: 'center',
                    editable: {
                        type: 'text',
                        title: 'Email',
                        validate: function (value) {
                            value = $.trim(value);
                            if (!value) {
                                return 'This field is required';
                            }
                            //if (!/^\$/.test(value)) {
                            //    return 'This field needs to start width $.'
                            //}
                            var data = $table.bootstrapTable('getData'),
                                index = $(this).parents('tr').data('index');
                            console.log(63, data[index]);
                            return '';
                        }
                    },
                    footerFormatter: totalPriceFormatter    // 函数内的参数要与 editable 里定义的一致
                },
                {
                    field: 'name',
                    title: 'User Name',
                    sortable: true,
                    editable: true,
                    footerFormatter: totalNameFormatter,
                    align: 'center'
                },
                {
                    field: 'operate',
                    title: 'Account Operate',
                    align: 'center',
                    events: operateEvents,
                    formatter: operateFormatter
                }
            ]
        ]
    });

    // 隐藏列, 指定 field 名即可
    $(function () {
        $('#table').bootstrapTable('hideColumn', 'id');
    });

    // sometimes footer render error.
    setTimeout(function () {
        $table.bootstrapTable('resetView');
    }, 200);

    // 对 check box 的识别
    $table.on('check.bs.table uncheck.bs.table check-all.bs.table uncheck-all.bs.table', function () {
        $remove.prop('disabled', !$table.bootstrapTable('getSelections').length);
        // save your data, here just save the current page
        selections = getIdSelections();
        alert(selections);
        // push or splice the selections if you want to save all data selections
    });

    $table.on('expand-row.bs.table', function (e, index, row, $detail) {
        if (index % 2 == 1) {
            $detail.html('Loading from ajax request...');
            $.get('LICENSE', function (res) {
                $detail.html(res.replace(/\n/g, '<br>'));
            });
        }
    });

    $table.on('all.bs.table', function (e, name, args) {
        //console.log(118, name, args);
    });

    // Delete 按钮功能
    $remove.click(function () {
        var ids = getIdSelections();
        $table.bootstrapTable('remove', { // http://issues.wenzhixin.net.cn/bootstrap-table/#methods/remove.html
            field: 'id',
            values: ids
        });
        $remove.prop('disabled', true); // 操作完成后, 进入未选中状态, remove 按钮置为不可点击状态
    });

    $(window).resize(function () {
        $table.bootstrapTable('resetView', {
            height: getHeight()
        });
    });
}

function getIdSelections() {
    return $.map($table.bootstrapTable('getSelections'), function (row) {
        return row.id
    });
}

function responseHandler(res) {
    $.each(res.rows, function (i, row) {
        row.state = $.inArray(row.id, selections) !== -1;
    });
    return res;
}
function detailFormatter(index, row) {
    var html = [];
    $.each(row, function (key, value) {
        html.push('<p><b>' + key + ':</b> ' + value + '</p>');
    });
    return html.join('');
}

// 自定义操作, 此处在源码里加上 id 属性以便后面使用 id 选择器
function operateFormatter(value, row, index) {
    return [
        //'<a id=' + 'row_id_' + index + ' class="like" href="javascript:void(0)" title="Like">',
        '<a class="like" href="javascript:void(0)" title="Like">',
        '<i class="glyphicon glyphicon-heart"></i>',
        '</a>  ',
        '<a class="remove" href="javascript:void(0)" title="Remove">',
        '<i class="glyphicon glyphicon-remove"></i>',
        '</a>'
    ].join('');
}
window.operateEvents = {
    'click .like': function (e, value, row, index) {
        // e: 事件类型, j…y.Event {originalEvent: MouseEvent, ...}; value: undefined ??
        // alert('You click like action, row: ' + JSON.stringify(row));
        rowDataSave(index);
    },
    'click .remove': function (e, value, row, index) {
        $table.bootstrapTable('remove', {
            field: 'id',
            values: [row.id]
        });
    }
};


function totalTextFormatter(data) {
    return 'Total';
}

function totalNameFormatter(data) {
    return data.length;
}

function totalPriceFormatter(data) {
    var total = 0;
    $.each(data, function (i, row) {
        total += +(row.email.substring(1));
    });
    return '$' + total;
}

function getHeight() {
    return $(window).height() - $('h1').outerHeight(true);
}

$(function () {
    var scripts = [
            location.search.substring(1) ||
            '/static/plugins/bootstrap-table/bootstrap-table.js',
            '/static/plugins/bootstrap-table/bootstrap-table-export.js',
            '/static/plugins/bootstrap-table/tableExport.js',
            '/static/plugins/bootstrap-table/bootstrap-table-editable.js',
            '/static/plugins/bootstrap-table/bootstrap-table-zh-CN.js',
            '/static/plugins/bootstrap-table/bootstrap-editable.js'
        ],
        eachSeries = function (arr, iterator, callback) {
            callback = callback || function () {
                };
            if (!arr.length) {
                return callback();
            }
            var completed = 0;
            var iterate = function () {
                iterator(arr[completed], function (err) {
                    //console.log(230, arr[completed], err);
                    if (err) {
                        callback(err);
                        callback = function () {
                        };
                    }
                    else {
                        completed += 1;
                        if (completed >= arr.length) {
                            callback(null);
                        }
                        else {
                            iterate();
                        }
                    }
                });
            };
            iterate();
        };
    eachSeries(scripts, getScript, initTable);
});
function getScript(url, callback) {
    var head = document.getElementsByTagName('head')[0];
    var script = document.createElement('script');
    script.src = url;
    var done = false;
    //console.log(256, url, callback, head, script);
    // Attach handlers for all browsers
    script.onload = script.onreadystatechange = function () {
        if (!done && (!this.readyState || this.readyState == 'loaded' || this.readyState == 'complete')) {
            done = true;
            if (callback) {
                callback();
            }
            // Handle memory leak in IE
            script.onload = script.onreadystatechange = null;
        }
    };
    head.appendChild(script);
    // We handle everything using the script element injection
    return undefined;
}

function rowDataSave(index) {
    var url = '/user/row_data_save/';
    var dataDict = {};
    var ele = $('tr[data-index=' + index + ']');
    $(ele).children().each(function () {
        var dataPK = $(this).find('a').attr('data-pk');
        var dataName = $(this).find('a').attr('data-name');

        if (dataPK && dataName) {
            var dataData = $(this).find('a').text();
            console.log(283, dataPK, dataName, dataData);
            dataDict['id'] = dataPK;    // 用户的主键字段为 id, 不需要使用变量
            dataDict[dataName] = dataData;
        }
    });
    $.post(url, dataDict, function (data) {
        console.log(289, data);
    })
}