import random

from django.shortcuts import render
from django.views import View
from MeiDuo_Store.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from .constime import *
from django.http import *
from MeiDuo_Store.libs.response_code import RETCODE
from celery_tasks.sms.tasks import send_sms


class ImgecodeView(View):
    def get(self, request, uuid):
        print(uuid)
        text, code, image = captcha.generate_captcha()
        redis = get_redis_connection('verify_code')
        redis.setex(uuid, IMAGE_CODE_EXPIRES, code)
        return HttpResponse(content=image, content_type='image/png')  # 指定数据类型,方便浏览器解析


class SmscodeView(View):
    def get(self, request, mobile):
        image_code_request = request.GET.get('image_code')
        # 前端返回 验证码
        image_code_id_request = request.GET.get('image_code_id')
        # 查询字符串uuid
        # print(image_code_request, image_code_id_request, mobile)  # 打印看看正常访问不
        redis_cli = get_redis_connection('verify_code')  # 连接redis 数据库
        image_code_redis = redis_cli.get(image_code_id_request)  # 取验证码
        if not image_code_redis:  # 判空
            return JsonResponse({
                'code': RETCODE.IMAGECODEERR,
                'errmsg': '图片验证码过期'
            })  # 返回 Json 字符串
        if image_code_redis.decode() != image_code_request.upper():
            return JsonResponse({
                'code': RETCODE.IMAGECODEERR,
                'errmsg': '验证码输入错误!'
            })
        # 强制过期
        redis_cli.delete(image_code_id_request)
        if redis_cli.get('sms_flag_' + mobile):
            return JsonResponse({
                'code': RETCODE.IMAGECODEERR,
                'errmsg': '验证码提交频繁'
            })
        # 模拟随机生成6位验证码
        sms_code = '%06d' % random.randint(0, 999999)
        redis_pl = redis_cli.pipeline()
        redis_pl.setex('sms-' + mobile, SMS_CODE_EXPIRES, sms_code)
        redis_pl.setex('sms_flag_' + mobile, SMS_CODE_FLAG_EXPIRES, 1)
        redis_pl.execute()

        send_sms.delay(mobile, [sms_code, SMS_CODE_EXPIRES / 60], 1)
        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': "OK"
        })
