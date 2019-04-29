# from django.shortcuts import render
# from django.views import View
# from MeiDuo_Store.utils.response_code import RETCODE
# from django import http
# from .models import Areas
# from django.core.cache import   cache
# # from . import contants
#
#
# class AreaView(View):
#     def get(self, request):
#         # 接收
#         area_id = request.GET.get('area_id')
#
#         # 验证：area_id允许为空，表示查询省信息
#
#         # 处理
#         if area_id is None:
#             # 读取缓存
#             province_list = cache.get('province_list')
#
#             if province_list is None:
#                 # 查询省信息
#                 provinces = Area.objects.filter(parent__isnull=True)
#                 # 转换字典
#                 province_list = []
#                 for province in provinces:
#                     province_list.append({
#                         'id': province.id,
#                         'name': province.name
#                     })
#
#                 # 写缓存
#                 cache.set('province_list', province_list, contants.AREA_CACHE_EXPIRES)
#
#             # 响应
#             return http.JsonResponse({
#                 'code': RETCODE.OK,
#                 'errmsg': 'ok',
#                 'province_list': province_list
#             })
#         else:
#             # 读取缓存
#             sub_data = cache.get('area_' + area_id)
#             if sub_data is None:
#                 # 查询指定编号的地区及子级地区
#                 try:
#                     area = Area.objects.get(pk=area_id)
#                 except:
#                     return http.JsonResponse({
#                         'code': RETCODE.PARAMERR,
#                         'errmsg': '地区编号无效'
#                     })
#                 else:
#                     # 获取子级地区
#                     subs = area.subs.all()
#                     sub_list = []
#                     for sub in subs:
#                         sub_list.append({
#                             'id': sub.id,
#                             'name': sub.name
#                         })
#                     # 结果数据
#                     sub_data = {
#                         'id': area.id,
#                         'name': area.name,
#                         'subs': sub_list
#                     }
#                     # 写缓存
#                     cache.set('area_' + area_id, sub_data, contants.AREA_CACHE_EXPIRES)
#
#                 return http.JsonResponse({
#                     'code': RETCODE.OK,
#                     'errmsg': 'ok',
#                     'sub_data': sub_data
#                 })