

def get_breadcrumb(category3):
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
    return breadcrumb