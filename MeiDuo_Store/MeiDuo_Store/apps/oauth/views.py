import re
from django.contrib.auth import login
from users.models import User
from django.http import *
from django.shortcuts import render, redirect
from django.views import View
from django import http
from QQLoginTool.QQtool import OAuthQQ
from django_redis import get_redis_connection
from MeiDuo_Store.utils.meiduo_signature import *
from MeiDuo_Store.utils.response_code import RETCODE
from .models import OAuthQQUser
from MeiDuo_Store.apps.verifications.constime import COOKIES_TIME_DUMPS


class QQurlView(View):
    def get(self, request):
        # 生成授权地址
        next_url = request.GET.get('next')
        print('\n', next_url)
        # 1.创建工具对象
        qq_tool = OAuthQQ(
            settings.QQ_CLIENT_ID,
            settings.QQ_CLIENT_SECRET,
            settings.QQ_REDIRECT_URI,
            next_url,
        )
        # 2.调用方法，生成url地址
        login_url = qq_tool.get_qq_url()

        # 响应
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'login_url': login_url
        })


class QQopenidView(View):
    def get(self, request):
        # 获取openid
        # 1.接收code
        code = request.GET.get('code')
        next_url = request.GET.get('state')

        # 2.创建工具对象
        qq_tool = OAuthQQ(
            settings.QQ_CLIENT_ID,
            settings.QQ_CLIENT_SECRET,
            settings.QQ_REDIRECT_URI,
            next_url
        )
        try:
            # 获取token
            token = qq_tool.get_access_token(code)
            # 获取openid
            openid = qq_tool.get_open_id(token)
            try:
                # 查表
                oauth_user = OAuthQQUser.objects.get(openid=openid)

            except:
                # 未绑定,首次绑定,返回绑定页面
                # 加密,json数据
                token = dumps({'openid': openid}, COOKIES_TIME_DUMPS)

                context = {'token': token}
                return render(request, 'oauth_callback.html', context)
            else:
                # 绑定过,正常登陆
                login(request, oauth_user.user)
                response = redirect(next_url)
                response.set_cookie('username', oauth_user.user.username)
                return response
        except:
            openid = 0
        return HttpResponse(openid)

    def post(self, request):
        # 用于接受绑定页面的数据
        mobile = request.POST.get('mobile')
        token = request.POST.get('access_token')
        password = request.POST.get('pwd')
        sms_code = request.POST.get('sms_code')

        next_url = request.GET.get('state')

        print('@@', password, '\n')
        # 验证开始,非空,格式验证
        if not all(['password', 'mobile', 'sms_code', 'token']):
            return HttpResponseForbidden('参数不完整')
        if not re.match(r'^[A-Za-z0-9]{5,20}', password):
            return HttpResponseForbidden('请输入5-20位密码')
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号')
        if not sms_code:
            return HttpResponseForbidden('手机验证失效')
        # 验证码
        # redis 数据库的连接
        redis_cli = get_redis_connection('verify_code')
        # 从redis数据库取值
        sms_code_redis = redis_cli.get('sms-' + mobile)
        if sms_code_redis is None:
            return HttpResponseForbidden('手机验证码过期')
        print(sms_code, sms_code_redis)
        # 判断用户输入的短信验证码,和数据库中的验证码是否相同
        if sms_code != sms_code_redis.decode():
            return HttpResponseForbidden('手机验证码错误')
        # 验证成功,后删除redis数据库中的验证码数据
        redis_cli.delete('sms-' + mobile)

        # 解密token
        json = loads(token, COOKIES_TIME_DUMPS)
        # 判断是否被更改
        if json is None:
            return HttpResponseBadRequest('授权已过期')
        # 解密返回json数据,取值
        openid = json['openid']
        print('@@', openid, '##')
        try:
            user = User.objects.get(mobile=mobile)
        except:
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            if not user.check_password(password):
                return HttpResponseBadRequest('账号信息无效')
        OAuthQQUser.objects.create(openid=openid, user=user)
        login(request, user)
        response = redirect(next_url)
        response.set_cookie('username', user.username, max_age=COOKIES_TIME_DUMPS)

        return response
