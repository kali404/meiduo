from celery import Celery
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "MeiDuo_Store.settings.dev"

celery_app = Celery()
celery_app.config_from_object('celery_tasks.config')
# 自动识别

celery_app.autodiscover_tasks([
    'celery_tasks.sms',
    'celery_tasks.mail',
])

