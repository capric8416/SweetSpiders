# -*- coding: utf-8 -*-
# !/usr/bin/env python
import oss2
import requests

auth = oss2.Auth('LTAIZRvkU8rp8xQd', 'GnrosNN08FBZY7SUFt6sr82WF8n96c')
bucket = oss2.Bucket(auth, 'http://oss-cn-beijing.aliyuncs.com', 'dana2')

input = requests.get('https://www.daisyjewellery.com/static/media/catalog/product/n/2/n2023_gp.jpg')
# host = 'oss-cn-beijing.aliyuncs.com'
# bucket_name = 'dana2'
# endpoint = f'http://{host}'
# base_url = f'http://{bucket_name}.{host}'
img_name = 'text.jpg'
reback_link = bucket.put_object(img_name, input)
