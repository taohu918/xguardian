/**
 * Created by TaoHu on 2017/1/22.
 */

$('#console').click(
    function () {
        /* document.getElementById('#iframe').style.height = "200px";*/
        $('#iframe').attr('src', 'http://172.16.79.150:3000/').height(450).css('border', 'thick double #CAFF70');
        $(window).scrollTop(0);
    }
);

$(function () {
    $("#assets").removeClass("hiding");
    $("#assets_info").addClass("sub_item");
});