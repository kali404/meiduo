from fdfs_client.client import Fdfs_client

if __name__ == '__main__':
    client = Fdfs_client('client.conf')
    ret = client.upload_by_filename('/home/python/Pictures/802be259a3358cf54129fdc47e868397.jpg')
    print(ret)


