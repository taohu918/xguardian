/**
 * Created by Administrator on 2016/12/26.
 */

/*
 $('#secret').click(function () {
 //console.log($('#secret').find('span'));
 $.each($('#secret').find('span'), function (i, ele) {
 console.log(ele);
 if ($(ele).is(":hidden")) {
 $(ele).removeClass('hide');
 } else {
 $(ele).addClass('hide');
 }
 })
 });
 */

function secret_show(ths) {
    // alert(ths);
    $.each($(ths).find('span'), function (i, ele) {
        console.log(ele);
        if ($(ele).is(":hidden")) {
            $(ele).removeClass('hide');
        } else {
            $(ele).addClass('hide');
        }
    })
}