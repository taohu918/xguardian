/**
 * Created by Administrator on 2016/12/13.
 */

function show_item(ths) {
    if ($(ths).next().is(":hidden")) {
        $(ths).next().slideDown(500);    //如果元素为隐藏, 则将它显现. || $(ths).parent().find(".hiding").slideDown(800);
    } else {
        $(ths).next().slideUp(500);     //如果元素为显现,则将其隐藏
    }
}