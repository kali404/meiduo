from django.shortcuts import render
from django.views import View
from MeiDuo_Store.utils.category import get_category
from .models import ContentCategory, Content


class IndexView(View):
    def get(self, request):
        categories = get_category()
        contents = ContentCategory.objects.all()
        content_dict = {}

        for content in contents:
            content_dict[content.key] = content.content_set.filter(status=True).order_by('sequence')
        context = {
            'categories': categories,
            'contents': content_dict
        }
        return render(request, 'index.html', context)
