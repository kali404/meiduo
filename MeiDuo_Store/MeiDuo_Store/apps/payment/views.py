from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.views import View
from django.http import *
from MeiDuo_Store.utils.response_code import RETCODE
from orders.models import OrderInfo
from alipay import AliPay
from django.conf import settings
import os
from .models import Payment


class AlipayUrlView(View):
    def get(self, request, order_id):
        try:
            order = OrderInfo.objects.get(pk=order_id)
        except:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '订单编号无效'})

        # 创建支付宝对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/payment/keys/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/payment/keys/app_public_key.pem'),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 生成支付地址的参数
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单编号k
            total_amount=str(order.total_amount),  # 支付总金额
            subject='美多商城-订单支付',
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=None
        )

        # 拼接支付地址
        url = settings.ALIPAY_GATEWAY + order_string

        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': '',
            'alipay_url': url
        })


class AlipayVerifyView(View):
    def get(self, request):
        # 接收支付宝返回的数据
        param_dict = request.GET.dict()
        # QeuryDict转成字典

        # 获取支付宝返回值中的签名并删除
        signature = param_dict.pop("sign")
        # 创建支付宝对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/payment/keys/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/payment/keys/app_public_key.pem'),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        # 验证
        result = alipay.verify(param_dict, signature)
        if result:
            # 支付成功
            order_id = param_dict.get('out_trade_no')
            alipay_id = param_dict.get('trade_no')
            Payment.objects.create(
                order_id=order_id,
                trade_id=alipay_id
            )
            # 修改订单状态为待发货
            OrderInfo.objects.filter(pk=order_id).update(status=2)
            return render(request, 'pay_success.html', {'trade_no': alipay_id})
        else:
            # 支付失败
            return HttpResponse('支付失败')