from itsdangerous import TimedJSONWebSignatureSerializer as Slizer
from django.conf import settings


def dumps(json, expires):
    """
    签名openid,加密,
    :param openid: 用户的openid
    :return: access_token
    """
    slizer = Slizer(settings.SECRET_KEY, expires)
    token = slizer.dumps(json)

    return token.decode()


def loads(s, expires):
    slizer = Slizer(settings.SECRET_KEY, expires)
    jsons = slizer.loads(s)
    return jsons
