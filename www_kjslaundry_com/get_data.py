# -*- coding: utf-8 -*-
# !/usr/bin/env python

import json
with open('search.json', 'r') as f:
    data = json.load(f)

    product_param = {}
    for product in data:
        # print(product)
        img_urls = []
        product_param['offerprice'] = product.get('offerPrice')
        for img in product.get('images'):
            img_url = img.get('url')
            img_urls.append(img_url)
        product_param['img'] = img_urls
        product_param['title'] = product.get('title')
        product_param['source'] = product.get('pageUrl')
        product_param['description'] = product.get('text')
        product_param['category'] = product.get('category')
        product_param['brand'] = product.get('brand')

        print(product_param)


