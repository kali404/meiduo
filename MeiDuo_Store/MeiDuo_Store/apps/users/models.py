from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    mobile = models.CharField(max_length=11)
    # 邮箱的激活状态
    email_active = models.BooleanField(default=False)

    class Meta:
        db_table = 'tb_user'


