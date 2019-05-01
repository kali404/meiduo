from django.db import models
from django.contrib.auth.models import AbstractUser
from areas.models import Areas
from MeiDuo_Store.utils.models import BaseModel


class User(AbstractUser):
    """自定义用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')
    default_address = models.ForeignKey('Address', related_name='users', null=True, verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey('User', related_name='addersses')
    title = models.CharField(max_length=20, verbose_name='地址名称')  # 标题
    receiver = models.CharField(max_length=20, verbose_name='收货人')  # 收件人的名字
    province = models.ForeignKey(Areas, on_delete=models.PROTECT, related_name='provinces', verbose_name='省')  # 省
    city = models.ForeignKey(Areas, related_name='city', verbose_name='市')  # 市
    district = models.ForeignKey(Areas, related_name='district', verbose_name='区')  # 区
    place = models.CharField(max_length=50, verbose_name='地址')  # 详细地址
    mobile = models.CharField(max_length=11, verbose_name='手机')  # 手机号
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')  # 收件人电话
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')  # 收件人邮箱
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')  # 是否删除

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']
