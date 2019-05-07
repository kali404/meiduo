from goods.models import GoodsChannel


def get_category():
    categories = {}
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        group_id = channel.group_id
        if group_id not in categories:
            categories[group_id] = {
                'channels': [],
                'sub_cats': [],
            }
        channel_dict = categories[group_id]
        channel_dict['channels'].append({
            'name': channel.category.name,
            'url': channel.url,
        })
        catetory2s = channel.category.subs.all()
        for i2 in catetory2s:
            channel_dict['sub_cats'].append({
                'name': i2.name,
                'sub_cats': i2.subs.all()
            })
    return categories
