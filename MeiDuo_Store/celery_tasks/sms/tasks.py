import time

from MeiDuo_Store.libs.yuntongxun.sms import CCP
from celery_tasks.main import celery_app


@celery_app.task(bind=True, name='ccp_send_sms_code', retry_backoff=3)
def send_sms(self, to, data, tempid):
    try:
        time.sleep(5)
        # ccp = CCP()
        # ccp.send_template_sms(to, data, tempid)
        print(data[0])

    except Exception as e:
        # 当失败时，任务重试
        self.retry(exc=e, max_retries=2)

