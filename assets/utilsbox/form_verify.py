# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

from django import forms


class UploadObj(forms.Form):
    upload_obj = forms.ImageField()
    # target_host = forms.GenericIPAddressField()
