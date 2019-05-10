from django.shortcuts import render
from django.views import View
from goods.models import GoodsChannel, GoodsCategory, SKU, SKUSpecification
from MeiDuo_Store.utils.response_code import RETCODE
from MeiDuo_Store.utils.category import get_category
from MeiDuo_Store.utils.breadcrumb import get_breadcrumb
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
        except:
            return render(requset, '404.html')

        categories = get_category()
        category3 = sku.category
        breadcrumb = get_breadcrumb(category3)
        option_current = [info.option_id for info in sku.specs.order_by('spec_id')]

        skus = sku.spu.sku_set.filter(is_launched=True)
        sku_option_dict={}
        for sku_temp in skus:
            keys_list = []
            for sku_option in sku_temp.specs.order_by('spec_id'):
                keys_list.append(sku_option.option_id)

            sku_option_dict[tuple(keys_list)]=sku_temp.id

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
                    'sku_id': sku_option_dict[tuple(option_current_temp)],
                    'selected': option.id in option_current,
                })
            specs_list.append(spec_dict)

        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'spu': sku.spu,
            'specs_list': specs_list
        }
        return render(requset, 'detail.html', context)
