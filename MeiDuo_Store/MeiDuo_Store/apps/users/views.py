import json
import re
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from pymysql import DatabaseError
from verifications.constime import EMAIL_TIME_DUMPS, COOKIES_CODE_TIME
from MeiDuo_Store.utils.response_code import RETCODE
from .models import User
from django.http import *
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
from celery_tasks.mail.tasks import send_user_mali
from django.conf import settings
from MeiDuo_Store.utils import meiduo_signature


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
        check_sms_code = request.POST.get('msg_code')

        if not all(['user_name', 'password', 'cpassworld', 'phone', 'allow', 'check_sms_code']):
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
        redis_cli = get_redis_connection('verify_code')
        sms_code = redis_cli.get('sms-' + phone)

        if not sms_code:
            return HttpResponseForbidden('手机验证失效')

        # print(sms_code.decode(), check_sms_code)

        if check_sms_code != sms_code.decode():
            return HttpResponseForbidden('手机验证码错误')

        redis_cli.delete('sms-' + phone)

        try:
            user = User.objects.create_user(username=user_name, password=password, mobile=phone)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})

        # 保持登陆状态
        #         request.session['user_id'] = user.id
        #           django封装了login
        login(request, user)

        return redirect('/login/')


class UsernameCheckView(View):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'count': count})


class MobileCheckView(View):
    def get(self, request, mobile):
        c = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'count': c})


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 接收
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')
        next_url = request.GET.get('next', '/')
        print(next_url)

        # 验证
        # 2.1非空
        if not all([username, pwd]):
            return HttpResponseBadRequest('参数不完整')
        # 2.2用户名格式
        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseBadRequest('请输入5-20个字符的用户名')
        # 2.3密码格式
        if not re.match('^[0-9A-Za-z]{8,20}$', pwd):
            return HttpResponseBadRequest('请输入8-20位的密码')

        user = authenticate(username=username, password=pwd)
        if user is None:
            return render(request, 'login.html', {'loginerror': '用户名密码错误'})
        else:
            print('我是')
            login(request, user)
            response = redirect(next_url)
            response.set_cookie('username', user.username, max_age=COOKIES_CODE_TIME)
            return response


class LogoutView(View):
    def get(self, request):
        # 退出登陆
        logout(request)
        # 删除cookie中的username(提示作用)
        response = redirect('/')
        response.delete_cookie('username')
        return response


class InfoView(LoginRequiredMixin, View):
    def get(self, request):
        # if not request.user.is_authenticated:
        #     return redirect('/login/')  # 继承的LoginRequiedMixin封装了上诉代码
        user = request.user
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'email': user.email,
            'email_active': user.email_active,
        }

        return render(request, 'user_center_info.html', context)


class EmailView(LoginRequiredMixin, View):
    def put(self, request):
        dict1 = json.loads(request.body.decode())
        email = dict1.get('email')
        if not all([email]):
            return JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '么有邮箱数据',
            })
        if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '邮箱格式错误',
            })
        user = request.user
        user.email = email
        user.save()
        # 加密
        token = meiduo_signature.dumps({'user_id': user.id}, EMAIL_TIME_DUMPS)
        urls = settings.EMAIL_ACTIVE_URL + '?user_id=%s' % token
        send_user_mali.delay(email, urls)
        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok'
        })


class EmailActiveView(View):
    def get(self, request):
        token = request.GET.get('user_id')
        if not all([token]):
            return HttpResponseBadRequest('参数不完整')
        json_t = meiduo_signature.loads(token, EMAIL_TIME_DUMPS)

        if json_t is None:
            return HttpResponseBadRequest('连接无效')
        user_id = json_t.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
        except:
            return HttpResponseBadRequest('激活链接无效')
        else:
            user.email_active = True
            user.save()
        # 响应
        return redirect('/info/')


class AddressView(LoginRequiredMixin, View):
    def get(self, requests):
        return render(requests, 'user_center_site.html')


class CreateAddressView(LoginRequiredMixin, View):
    """新增地址"""

    def post(self, request):
        """实现新增地址逻辑"""
        # 判断是否超过地址上限：最多20个
        # Address.objects.filter(user=request.user).count()
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')

        # 保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址响应给前端实现局部刷新
        address_dict = {
            'code': RETCODE.OK,
            'errmsg': 'OK',
            'id': address.id,
            'receiver': address.receiver,
            'province': address.province.name,
            'province_id': address.province_id,
            'city': address.city.name,
            'city_id': address.city_id,
            'district': address.district.name,
            'district_id': address.district_id,
            'place': address.detail_address,
            'mobile': mobile,
            'tel': tel,
            'email': email
        }

        # 响应保存结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """提供收货地址界面"""
        # 获取用户地址列表
        login_user = request.user
        addresses = Address.objects.filter(user=login_user, is_deleted=False)

        address_dict_list = []
        for address in addresses:
            address_dict = {
                'id': address.id,
                'receiver': address.receiver,
                'province': address.province.name,
                'province_id': address.province_id,
                'city': address.city.name,
                'city_id': address.city_id,
                'district': address.district.name,
                'district_id': address.district_id,
                'place': address.detail_address,
                'mobile': address.mobile,
                'tel': address.phone,
                'email': address.email
            }

        context = {
            'default_address_id': login_user.default_address_id,
            'addresses': address_dict_list,
        }

        return render(request, 'user_center_site.html', context)


class UpdateDestroyAddressView(LoginRequiredMixin, View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "province_id": address.province.id,
            "city": address.city.name,
            "city_id": address.city.id,
            "district": address.district.name,
            "district_id": address.district.id,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class DefaultAddressView(LoginRequiredMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})
