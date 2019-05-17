import os

from django.conf import settings
from django.shortcuts import render
from MeiDuo_Store.utils.category import get_category
from .models import ContentCategory


def qingtai_html():
    categories = get_category()
    contents = ContentCategory.objects.all()
    content_dict = {}

    for content in contents:
        content_dict[content.key] = content.content_set.filter(status=True).order_by('sequence')
    context = {
        'categories': categories,
        'contents': content_dict
    }
    response = render(None, 'index.html', context)
    html = response.content.decode()
    paths = os.path.join(settings.BASE_DIR,'static/index.html')
    with open(paths,'w') as f:
        f.write(html)


