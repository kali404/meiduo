import re

from django.contrib.auth import login
from django.shortcuts import render

# Create your views here.
from django.views import View
from .models import User

from django.http import *


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        """
        return render(request, 'register.html')

    def post(self, request):
        user_name = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassworld = request.POST.get('cpwd')
        phone = request.POST.get('phone')
        allow = request.POST.get('allow')

        if not all(['user_name', 'password', 'cpassworld', 'phone', 'allow']):
            return HttpResponseForbidden('参数不完整')
        if not re.match(r'^[A-Za-z0-9]{5,20}', user_name):
            return HttpResponseForbidden('请输入5-20位用户名')
        if User.objects.filter(username=user_name):
            return HttpResponseForbidden('用户名以存在')
        if not re.match(r'^[A-Za-z0-9]{5,20}', password):
            return HttpResponseForbidden('请输入5-20位密码')
        if cpassworld != password:
            return HttpResponseForbidden('密码输入不一致')
        if not re.match(r'^1[345789]\d{9}$', phone):
            return HttpResponseForbidden('请输入正确的手机号')
        if User.objects.filter(mobile=phone):
            return HttpResponseForbidden('手机号以存在')

        user = User.objects.create_user(username=user_name, password=password, mobile=phone)
        #         保持登陆状态
        #         request.session['user_id'] = user.id
        #           django封装了login
        login(request, user)

        return HttpResponse('注册成功')
