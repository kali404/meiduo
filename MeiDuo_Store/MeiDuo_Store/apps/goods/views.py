from django.shortcuts import render
from django.views import View
from goods.models import GoodsChannel, GoodsCategory, SKU
from MeiDuo_Store.utils.response_code import RETCODE
from MeiDuo_Store.utils.category import get_category
from django.core.paginator import Paginator
from django.http import *

# Create your views here.


class ListView(View):
    def get(self, request, category_id, page_num):
        try:
            category3 = GoodsCategory.objects.get(pk=category_id)
        except:
            return render(request, '404.html')
        categories = get_category()
        category2 = category3.parent
        category1 = category2.parent
        breadcrumb = {
            'cat1': {
                'name': category1.name,
                'url': category1.goodschannel_set.all()[0].url
            },
            'cat2': category2,
            'cat3': category3,
        }
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