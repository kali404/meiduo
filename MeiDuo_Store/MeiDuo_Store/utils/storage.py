from django.core.files.storage import Storage
from django.conf import settings


class FdfsStorage(Storage):
    def url(self,name):
        return settings.FDFS_URL + name
