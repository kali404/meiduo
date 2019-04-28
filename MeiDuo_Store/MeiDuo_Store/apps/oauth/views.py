from asyncio import constants

from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views import View
from django import http
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from itsdangerous import Serializer

from MeiDuo_Store.utils.response_code import RETCODE
from .models import OAuthQQUser
from MeiDuo_Store.apps.verifications.constime import COOKIES_CODE_TIME


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
            # 3.根据code获取token
            token = qq_tool.get_access_token(code)
            # 4.根据token获取openid
            openid = qq_tool.get_open_id(token)
            try:
                # 查表
                oauth_user = OAuthQQUser.objects.get(openid=openid)

            except:
                context = {'token': openid}


                # 未绑定
                return render(request, 'oauth_callback.html')
            else:
                # 绑定过
                pass

        except:
            openid = 0

    def post(self,request):
        # 用于接受绑定页面的数据
        mobile = request.GET.get('mobile')

        pass