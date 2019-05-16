from django_redis import get_redis_connection
from MeiDuo_Store.utils.my_json import loads,dumps


def merge_cart_cookie_to_redis(request, response):
    """
    登录后合并cookie购物车数据到Redis
    :param request: 本次请求对象，获取cookie中的数据
    :param response: 本次响应对象，清除cookie中的数据
    :param user: 登录用户信息，获取user_id
    :return: response
    """
    # 获取cookie中的购物车数据

    user = request.user
    # 1.读取cookie中购物车数据
    cart_str = request.COOKIES.get('cart')
    if cart_str is None:
        return response
    cart_dict = loads(cart_str)


    # 2.存入redis中
    redis_cli = get_redis_connection('carts')
    redis_pl = redis_cli.pipeline()
    # 遍历字典，逐个转存
    for sku_id, cart in cart_dict.items():
        # hash
        redis_pl.hset('cart%d' % user.id, sku_id, cart['count'])
        # set
        if cart['selected']:
            redis_pl.sadd('selected%d' % user.id, sku_id)
        else:
            redis_pl.srem('selected%d' % user.id, sku_id)
    redis_pl.execute()

    # 3.删除cookie中购物车数据
    response.delete_cookie('cart')
    return response
