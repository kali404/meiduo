from django.shortcuts import render
from django.views import View
from MeiDuo_Store.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from .constime import IMAGE_CODE_EXPIRES
from django.http import *


class ImgecodeView(View):

    def get(self, request, uuid):
        print(uuid)
        text, code, image = captcha.generate_captcha()
        redis = get_redis_connection('verify_code')
        redis.setex(uuid, IMAGE_CODE_EXPIRES, code)
        return HttpResponse(content=image, content_type='image/png')  # 指定数据类型,方便浏览器解析


