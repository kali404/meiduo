from django.db import models
from .models import SKU
from rest_framework import serializers


class GoodsInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField(label='id', read_only=True)
    name = serializers.CharField(label='名称', max_length=50)
    caption = serializers.CharField(max_length=100, label='副标题')

    class Meta:
        model = SKU
        fields = '__all__'
