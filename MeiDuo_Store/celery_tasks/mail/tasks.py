from django.core.mail import send_mail
from django.conf import settings
from celery_tasks.main import celery_app


@celery_app.task(name='send_user_mali', bind=True, backoff_retry=3)
def send_user_mali(self, to_mail, verify_url):
    subject = '美多商城验证'
    msg = '<p>尊敬的用户您好！</p>' \
          '<p>感谢您使用美多商城。</p>' \
          '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
          '<p><a href="%s">%s<a></p>' % (to_mail, verify_url, verify_url)

    try:
        send_mail(subject, '', settings.EMAIL_FROM, [to_mail], html_message=msg)
        print(verify_url,'to_mail',to_mail)
    except Exception as e:
        self.retry(exc=e, max_retries=2)
