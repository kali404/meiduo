import datetime
import json
from django.shortcuts import render
from django.views import View
from goods.models import GoodsChannel, GoodsCategory, SKU, SKUSpecification, GoodsVisitCount
from MeiDuo_Store.utils.response_code import RETCODE
from MeiDuo_Store.utils.category import get_category
from MeiDuo_Store.utils.breadcrumb import get_breadcrumb
from django.core.paginator import Paginator
from django.http import *
from django_redis import get_redis_connection


# Create your views here.


class ListView(View):
    def get(self, request, category_id, page_num):
        try:
            category3 = GoodsCategory.objects.get(pk=category_id)
        except:
            return render(request, '404.html')
        categories = get_category()

        breadcrumb = get_breadcrumb(category3)

        skus = category3.sku_set.filter(is_launched=True)
        sort = request.GET.get('sort', 'default')
        if sort == 'price':
            skus = skus.order_by('price')
        elif skus == 'hot':
            skus = skus.order_by('-sales')
        else:
            skus = skus.order_by('-id')
        paginator = Paginator(skus, 5)  # 将列表skus按照每页5条数据进行分页
        page_skus = paginator.page(page_num)  # 获取第page_num页的数据
        total_page = paginator.num_pages  # 总页数

        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sort': sort,
            'page_skus': page_skus,
            'category': category3,
            'page_num': page_num,
            'total_page': total_page
        }

        return render(request, 'list.html', context)


class HotView(View):
    def get(self, request, category_id):
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]

        # 序列化
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_sku_list': hot_skus})


class DetalView(View):
    def get(self, requset, sku_id):
        try:
            sku = SKU.objects.get(pk=sku_id)
            # 查询指定的库存商品
        except:
            return render(requset, '404.html')

        categories = get_category()  # 列表商品导航
        category3 = sku.category  # 根据库存商品获得上品类别对象
        breadcrumb = get_breadcrumb(category3)  # 根据这个对象找对应的商品的分类名字
        option_current = [info.option_id for info in sku.specs.order_by('spec_id')]  # 生成规格选项列表

        skus = sku.spu.sku_set.filter(is_launched=True)  # 查询所有上架商品
        sku_option_dict = {}
        for sku_temp in skus:  # 遍历查询出来的对象
            keys_list = []
            for sku_option in sku_temp.specs.order_by('spec_id'):  # 遍历商品的规格选项
                keys_list.append(sku_option.option_id)  # 将规格选项的ｉｄ添加到列表

            sku_option_dict[tuple(keys_list)] = sku_temp.id

        specs = sku.spu.specs.all()  # 拿
        specs_list = []
        for index, spec in enumerate(specs):
            spec_dict = {
                'name': spec.name,
                'options': []
            }

            options = spec.options.all()
            for option in options:
                option_current_temp = option_current[:]
                option_current_temp[index] = option.id

                SKUSpecification.objects.filter()

                spec_dict['options'].append({
                    'name': option.value,
                    'sku_id': sku_option_dict.get(tuple(option_current_temp), 0),
                    'selected': option.id in option_current,
                })
            specs_list.append(spec_dict)

        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'spu': sku.spu,
            'specs_list': specs_list,
            'category_id':category3.id
        }
        return render(requset, 'detail.html', context)


class DetaVisitView(View):
    def post(self, request, category_id):
        now = datetime.datetime.now()
        date = '%d-%d-%d' % (now.year, now.month, now.day)

        try:
            visit = GoodsVisitCount.objects.get(category_id=category_id, data=date)
        except:
            GoodsVisitCount.objects.create(category_id=category_id, count=1)
        else:
            visit.count += 1
            visit.save()
        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
        })


class HistoryView(View):
    def post(self, request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        if not all([sku_id]):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不能为空'})
        try:
            sku = SKU.objects.get(pk=sku_id)
        except:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不能为空'})
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errsmg': '用户未登陆！'})

        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        user_id = 'history%d' % user.id
        pl.lrem(user_id, 0, sku_id)
        # 删除指定的
        pl.lpush(user_id, sku_id)
        # 再加入
        pl.ltrim(user_id, 0, 4)
        # 限制个数
        pl.execute()
        # 统一执行

        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
        })

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '用户未登陆！'})
        redis_cil = get_redis_connection('history')
        # 连接redis
        sku_ids = redis_cil.lrange('history%d' % user.id, 0, -1)
        # 查询redis数据
        sku_ids = [int(sku_id) for sku_id in sku_ids]
        # redis 取回数据都为二字节
        skus = list()
        for sku_id in sku_ids:
        # 遍历取回数据
            sku = SKU.objects.get(pk=sku_id)
            # 查询商品对象
            skus.append({
                'id': sku_id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })  # 返回前端需要的数据

        return JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'ok',
            'skus':skus,
        })  # 响应数据