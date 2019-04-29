from django.db import models


class Areas(models.Model):
    name = models.CharField(max_length=30)
    parent = models.ForeignKey('self', null=True, related_name='subs')

    class Meta:
        db_table = 'tb_areas'

