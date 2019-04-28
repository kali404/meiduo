from django.db import models
from users.models import User
from MeiDuo_Store.utils.models import BaseModel


class OAuthQQUser(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登陆用户数据'
        verbose_name_plural = verbose_name


















