from django.contrib.auth.models import AbstractUser
from django.db import models
from MeiDuo_Store.utils.models import BaseModel


class Areas(models.Model):
    # 自动创建id主键
    name = models.CharField(max_length=30)  # 地区名称
    parent = models.ForeignKey('self', null=True, related_name='subs')  # 父级地区  self自关联 related_name 这个属性命名1端的 关系属性的名字

    class Meta:
        db_table = 'tb_areas'


