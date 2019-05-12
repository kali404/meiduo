import json

from . import constants
from goods.models import SKU
from MeiDuo_Store.utils.response_code import RETCODE
from MeiDuo_Store.utils.my_json import dumps, loads
from django.shortcuts import render
from django.views import View
from django.http import *
from django_redis import get_redis_connection


# Create your views here.
class CartsView(View):
    def post(self, request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')

        if not all([sku_id, count]):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '缺少必传参数', })
        try:
            sku = SKU.objects.get(pk=sku_id, is_launched=True)
        except:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '商品不存在', })

        try:
            count = int(count)
        except:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '格式错误'})
        if count <= 0:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '数量必须大于０'})
        if count > sku.stock:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '库存不足'})
        user = request.user
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            pl = redis_cli.pipeline()
            pl.hset('cart%d' % user.id, sku_id, count)
            pl.sadd('selected%d' % user.id, sku_id)
            pl.execute()

        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str is None:
                cart_dict = {}
            else:
                cart_dict = loads(cart_str)
            cart_dict[sku_id] = {
                'count': count,
                'selected': True,
            }
            response.set_cookie('cart', dumps(cart_dict), max_age=constants.CART_EXPIRES)
            return response

    def get(self, request):
        user = request.user
        cart_dict = {}
        if user.is_authenticated:  # 判断登陆　
            redis_cli = get_redis_connection('carts')
            cart = redis_cli.hgetall('cart%d' % user.id)
            selected = redis_cli.smembers('selected%d' % user.id)
            # 遍历　二进制转成int
            for sku_id, count in cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected,
                }
        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str is not None:
                cart_dict = loads(cart_str)

        skus = SKU.objects.filter(pk__in=cart_dict.keys(), is_launched=True)
        cart_skus = []
        for sku in skus:
            count = cart_dict[sku.id]['count']
            selected = cart_dict[sku.id]['selected']
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'count': count,
                'selected': str(selected),
                'total_amount': str(sku.price * count)
            })
        context = {
            'cart_skus': cart_skus
        }
        return render(request, 'cart.html', context)

    def put(self, request):
        '''
        修改购物车
        :param request:
        :return:
        '''
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        if not all([sku_id, count]):  # 非空验证时不要验证布尔类型
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '缺少必传参数'})
        try:
            sku = SKU.objects.get(pk=sku_id, is_launched=True)
        except:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '商品不存在,或已下架'})
        try:
            count = int(count)
        except:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '格式错误'})
        if count <= 0:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '数量必须大于０'})
        if count > sku.stock:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '库存不足'})
        if not isinstance(selected, bool):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})

        user = request.user
        response = JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'cart_sku': {
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'count': count,
                'selected': str(selected),
                'total_amount': str(sku.price * count)
            }
        })
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            pl = redis_cli.pipeline()
            pl.hset('cart%d' % user.id, sku_id, count)  # 增加修改
            if selected:
                pl.sadd('selected%d' % user.id, sku_id)
            else:
                pl.srem('selected%d' % user.id, sku_id)
            pl.execute()

        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str is None:
                return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '当前没有购物车数据'})
            cart_dict = loads(cart_str)
            # 2.修改
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            response.set_cookie('cart', dumps(cart_dict), max_age = constants.CART_EXPIRES)
        return response

    def delete(self, request):
            json_dict = json.loads(request.body.decode())
            sku_id = json_dict.get('sku_id')

            try:
                sku = SKU.objects.get(pk=sku_id, is_launched=True)
            except:
                return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '商品不存在,或已下架'})

            user = request.user
            response = JsonResponse({
                    'code': RETCODE.OK,
                    'errmsg': 'ok'
                })
            if user.is_authenticated:
                redis_cli = get_redis_connection('carts')
                pl = redis_cli.pipeline()
                pl.hdel('cart%d' % user.id, sku_id)
                pl.srem('selected%d' % user.id, sku_id)
                pl.execute()
            else:
                cart_str = request.COOKIES.get('cart')
                if cart_str is None:
                    return JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'购物车无效'})
                cart_dict = loads(cart_str)
                if sku_id in cart_dict:
                    del cart_dict[sku_id]

                response.set_cookie('cart',dumps(cart_dict),max_age=constants.CART_EXPIRES)

            return response

class CartsSelectAllView(View):
    """全选购物车"""
    def put(self, request):
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected', True)

        if not isinstance(selected, bool):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数无效'})
        user = request.user
        response = JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            pl = redis_cli.pipeline()
            if selected:
                sku_ids = redis_cli.hkeys('carts%d' % user.id)
                pl.sadd('selected%d' % user.id, *sku_ids)
            else:
                pl.delete('selected%d' % user.id)
            pl.execute()
        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str is None:
                return JsonResponse({'code':RETCODE.OK,'errmsg':'购物车无效'})
            cart_dict = loads(cart_str)
            for sku_ids,dict1 in cart_dict.items():
                dict1['selected'] = selected

            response.set_cookie('cart', dumps(cart_dict), max_age=constants.CART_EXPIRES)
        return response
