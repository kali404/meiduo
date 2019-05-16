from django.core.cache import cache
from django.shortcuts import render
from django.views import View
from MeiDuo_Store.utils.response_code import RETCODE
from django.http import *
from verifications.constime import AREA_CACHE_EXPIRES
from .models import Areas


class AreaView(View):
    def get(self, request):
        area_id = request.GET.get('area_id')
        if area_id is None:
            prov = Areas.objects.filter(parent__isnull=True)
            pro_list = list()
            for province in prov:
                pro_list.append({
                    'id': province.id,
                    'name': province.name,
                })
            return JsonResponse({
                'code': RETCODE.OK,
                'errmsg': 'ok',
                'province_list': pro_list,
            })
        else:
            try:
                aera = Areas.objects.get(pk=area_id)
            except:
                return JsonResponse({
                    'code': RETCODE.PARAMERR,
                    'errmsg': '地区编号不存在'
                })
            else:
                subs = aera.subs.all()
                sub_list = list()
                for sub in subs:
                    sub_list.append({
                        'id': sub.id,
                        'name': sub.name,
                    })
                sub_data = {
                    'id': aera.id,
                    'name': aera.name,
                    'subs': sub_list
                }
                # 写缓存
                cache.set('area_' + area_id, sub_data, AREA_CACHE_EXPIRES)
        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'sub_data': sub_data
        })


