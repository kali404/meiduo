from django.shortcuts import render
from goods.models import SKU
from MeiDuo_Store.utils.category import get_category
from MeiDuo_Store.utils.breadcrumb import get_breadcrumb
import os
from django.conf import settings
from celery_tasks.main import celery_app


@celery_app.task(name='generate_static_detail_html')
def generate_static_detail_html(sku_id):
    try:
        sku = SKU.objects.get(pk=sku_id)
    except:
        return render(None, '404.html')

    # - 频道分类
    categories = get_category()

    # 面包屑导航
    category3 = sku.category
    breadcrumb = get_breadcrumb(category3)

    # - 库存商品对象(根据主键查询)

    # 标准商品对象
    spu = sku.spu

    option_current = [info.option_id for info in sku.specs.order_by('spec_id')]

    # 查询所有的库存商品与选项信息
    skus = spu.sku_set.filter(is_launched=True)

    sku_option_dict = {}
    for sku_temp in skus:
        option_list = [info.option_id for info in sku_temp.specs.order_by('spec_id')]
        sku_option_dict[tuple(option_list)] = sku_temp.id


    # 规格==》选项===》链接
    # 查询指定标准商品的所有规格
    specs = spu.specs.all()
    spec_list = []
    for index, spec in enumerate(specs):  # [20,5,8,39]
        spec_dict = {
            'name': spec.name,
            'options': []
        }
        # 查询指定规格的所有选项
        options = spec.options.all()
        # 遍历，加入规格字典的列表中
        for option in options:
            # 根据当前选项获取新的完整选项，即保持其它规格的选项不变，只替换本规格的选项
            option_current_temp = option_current[:]
            option_current_temp[index] = option.id
            sku_id = sku_option_dict.get(tuple(option_current_temp), 0)

            spec_dict['options'].append({
                'name': option.value,
                'selected': option.id in option_current,
                'sku_id': sku_id
            })

        spec_list.append(spec_dict)

    # - 热销排行

    context = {
        'categories': categories,
        'breadcrumb': breadcrumb,
        'sku': sku,
        'spu': spu,
        'category_id': category3.id,
        'specs_list': spec_list
    }
    response = render(None, 'detail.html', context)
    html_str = response.content.decode()

    file_path = os.path.join(settings.BASE_DIR, 'static/details/%d.html' % sku.id)
    with open(file_path, 'w') as f1:
        f1.write(html_str)
