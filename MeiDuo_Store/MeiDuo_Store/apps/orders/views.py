import datetime
import json
from django.core.paginator import Paginator
from django_redis import get_redis_connection

from MeiDuo_Store.utils.response_code import RETCODE
from carts import constants
from django.shortcuts import render, redirect
from django.http import *
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from users.models import Address
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db import transaction


# Create your views here.
class OrderSettlementView(LoginRequiredMixin, View):
    """结算订单"""

    def get(self, request):
        """提供订单结算页面"""
        # 获取登录用户
        user = request.user
        default_address = user.default_address.id
        # 查询地址信息
        try:
            addresses = Address.objects.filter(user=request.user, is_deleted=False)
        except Address.DoesNotExist:
            # 如果地址为空，渲染模板时会判断，并跳转到地址编辑页面
            addresses = None
        print(addresses)
        # 从Redis购物车中查询出被勾选的商品信息
        redis_conn = get_redis_connection('carts')
        redis_cart = redis_conn.hgetall('cart%s' % user.id)
        cart_selected = redis_conn.smembers('selected%s' % user.id)
        cart_dict = {int(sku_id): int(count) for sku_id, count in redis_cart.items()}
        selected_list = [sku_id for sku_id in cart_selected]
        # 准备初始值
        total_count = 0  # 总数量
        total_money = 0  # 总金额
        sku_list = []
        freight = 10

        # 查询商品信息
        skus = SKU.objects.filter(pk__in=selected_list, is_launched=True)
        for sku in skus:
            total_amount = cart_dict[sku.id] * sku.price
            total_money += total_amount
            total_count += cart_dict[sku.id]
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url,
                'count': cart_dict[sku.id],
                'total_amount': total_money,

            })

        pay_money = total_money + freight
        # 渲染界面
        context = {
            'address_list': addresses,
            'sku_list': sku_list,
            'total_count': total_count,
            'total_money': total_money,
            'freight': freight,
            'pay_money': pay_money,
            'default_address': default_address
        }

        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredMixin, View):
    """提交订单"""

    def post(self, request):
        user = request.user
        # 接收
        param_dict = json.loads(request.body.decode())
        address_id = param_dict.get('address_id')
        pay_method = param_dict.get('pay_method')

        # 验证
        if not all([address_id, pay_method]):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不完整'})
        try:
            address = Address.objects.get(pk=address_id, is_deleted=False, user=user.id)
        except:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '收货地址无效'})
        if pay_method not in [1, 2]:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '支付方式无效'})

        # 处理：保存订单数据
        # 1.查询购物车中选中的商品
        redis_cli = get_redis_connection('carts')
        cart_dict = redis_cli.hgetall('cart%d' % user.id)
        cart_dict = {int(sku_id): int(count) for sku_id, count in cart_dict.items()}
        selected_list = redis_cli.smembers('selected%d' % user.id)
        selected_list = [int(sku_id) for sku_id in selected_list]

        # 2.创建订单对象
        with transaction.atomic():
            sid = transaction.savepoint()  # 开启事务
            total_count = 0
            total_amount = 0
            if pay_method == 1:  # 待付款
                status = 2  # 待发货
            else:
                status = 1
            # 主键，不能重复，年月日时分秒9位的用户编号
            now = datetime.datetime.now()
            order_id = '%s%09d' % (now.strftime('%Y%m%d%H%M%S'), user.id)
            order = OrderInfo.objects.create(
                order_id=order_id,
                user_id=user.id,
                address_id=address_id,
                total_count=total_count,
                total_amount=total_amount,
                freight=10,
                pay_method=pay_method,
                status=status
            )
            # 3.查询库存商品对象
            skus = SKU.objects.filter(pk__in=selected_list, is_launched=True)
            for sku in skus:
                count = cart_dict[sku.id]
                # 3.1判断库存，如果库存不足则返回提示，不再向下执行，如果库存足够则继续执行
                if sku.stock < count:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
                # 3.2修改商品的库存、销量

                # 使用乐观锁
                stock_old = sku.stock
                stock_new = sku.stock - count
                sales = sku.sales + count

                result = SKU.objects.filter(pk=sku.id, stock=stock_old).update(stock=stock_new, sales=sales)
                # result表示修改表中行的数量，当前为0或1
                if result == 0:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '服务器忙'})

                # 3.3创建订单商品对象
                order_goods = OrderGoods.objects.create(
                    order_id=order_id,
                    sku_id=sku.id,
                    count=count,
                    price=sku.price
                )
                # 3.4计算总金额、总数量
                total_count += count
                total_amount += count * sku.price
            # 4.修改订单的总金额、总数量
            order.total_count = total_count
            order.total_amount = total_amount
            order.save()

            transaction.savepoint_commit(sid)  # 提交事务
        # 5.删除购物车中选中的商品
        # hash
        redis_cli.hdel('cart%d' % user.id, *selected_list)
        # set
        redis_cli.delete('selected%d' % user.id)
        # 响
        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': '',
            'order_id': order_id
        })


class SuccessView(LoginRequiredMixin, View):
    def get(self, request):
        param_dict = request.GET
        # ?order_id=20190514082750000000001&payment_amount=3398&pay_method=2
        order_id = param_dict.get('order_id')
        payment_amount = param_dict.get('payment_amount')
        pay_method = param_dict.get('pay_method')

        if not all([order_id, payment_amount, pay_method]):
            return render(request, '404.html')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method,
        }

        return render(request, 'order_success.html', context)


class OrderListView(LoginRequiredMixin, View):
    def get(self, request, page_num):
        user = request.user
        # 查询订单对象
        orders = OrderInfo.objects.filter(user_id=user.id).order_by('-create_time')

        # 分页
        paginator = Paginator(orders, 2)
        page = paginator.page(page_num)

        # 转换成前端需要的格式
        order_list = []
        for order in page:
            # 构造订单商品对象
            sku_list = []
            for detail in order.skus.all():
                sku_list.append({
                    'default_image_url': detail.sku.default_image.url,
                    'name': detail.sku.name,
                    'price': detail.price,
                    'count': detail.count,
                    'total': detail.price * detail.count
                })

            # 构造订单对象
            order_list.append({
                'create_time': order.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'order_id': order.order_id,
                'sku_list': sku_list,
                'total_amount': order.total_amount,
                'freight': order.freight,
                'status': order.status
            })

        context = {
            'order_list': order_list,
            'page_num': page_num,
            'page_total': paginator.num_pages
        }

        return render(request, 'user_center_order.html', context)


class OrderCommentView(LoginRequiredMixin, View):
    def get(self, request):
        order_id = request.GET.get('order_id')
        if not all([order_id]):
            return redirect('/orders/info/1/')

        try:
            order = OrderInfo.objects.get(pk=order_id)
        except:
            return render(request, '404.html')

        skus = order.skus.filter(is_commented=False)
        sku_list = []
        for detail in skus:
            sku_list.append({
                'default_image_url': detail.sku.default_image.url,
                'name': detail.sku.name,
                'price': str(detail.price),
                'order_id': order_id,
                'sku_id': detail.sku_id
            })
        return render(request, 'goods_judge.html', {'skus': sku_list})

    def post(self, request):
        # 接收
        param_dict = json.loads(request.body.decode())
        order_id = param_dict.get('order_id')
        sku_id = param_dict.get('sku_id')
        comment = param_dict.get('comment')
        score = param_dict.get('score')
        is_anonymous = param_dict.get('is_anonymous', False)

        # 验证
        if not all([order_id, sku_id, comment, score]):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不完整'})
        try:
            detail = OrderGoods.objects.get(order_id=order_id, sku_id=sku_id)
        except:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '无效的订单、商品编号'})

        # 处理
        # 1.修改订单商品中关于评论的属性
        detail.comment = comment
        detail.score = score
        detail.is_anonymous = is_anonymous
        detail.is_commented = True
        detail.save()
        # 2.修改订单的状态
        order = detail.order
        if order.skus.filter(is_commented=False).count() <= 0:
            order.status = 5
            order.save()

        # 响应
        return JsonResponse({'code': RETCODE.OK, 'errmsg': ''})


class CommentListView(View):
    def get(self, request, sku_id):
        # 查询商品的所有评论信息
        details = OrderGoods.objects.filter(sku_id=sku_id, is_commented=True).order_by('-create_time')
        # 遍历，转换成前端需要的格式
        detail_list = []
        for detail in details:
            detail_list.append({
                'username': '*****' if detail.is_anonymous else detail.order.user.username,
                'score': detail.score,
                'msg': detail.comment
            })

        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': '',
            'goods_comment_list': detail_list
        })
