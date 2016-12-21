# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")


from django import template

register = template.Library()


@register.filter
def sum_size(data_set):
    # total_val = sum([float(i.capacity) if i.capacity else 0 for i in data_set])
    tmp_set = [float(i.capacity.split()[0]) if i.capacity else 0 for i in data_set]
    total_val = sum(tmp_set)

    return total_val


@register.filter
def list_count(data_set):
    data_count = len([i.capacity if i.capacity else 0 for i in data_set])

    return data_count
