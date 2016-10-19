# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")


from django import template

register = template.Library()


@register.filter
def sum_size(data_set):
    total_val = sum([int(i.capacity) if i.capacity else 0 for i in data_set])

    return total_val
