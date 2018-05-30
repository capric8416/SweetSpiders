# -*- coding: utf-8 -*-
# !/usr/bin/env python


import urllib.parse

import requests
from SweetSpiders.config import MONGODB_URL
from pymongo import MongoClient


class TransferCategory2Admin:
    """
    {
        "provider": "",
        "storeId": 0,
        "jsonCategory": [
            {
                "uuid": "uuid-1",　　＃　？？？
                "name": "WOMEN'S",  # 一级分类名
                "url": "http://www.baidu.com",　　＃　一级分类url
                "children": [
                    {
                        "uuid": "uuid-2",
                        "name": "TOPS AND T-SHIRTS",　　＃　二级分类名
                        "url": "http: //www.ccc.com",　　＃　二级分类url
                        "children": [
                            {
                                "uuid": "uuid-3",
                                "name": "DRESSES",　　＃　三级分类名
                                "url": "http://www.bbb.com"　　＃　二级分类url
                            },
                            {
                                "uuid": "uuid-4",
                                "name": "DRESSES",
                                "url": "http://www.bbb.com"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """

    def __init__(self):
        self.url = 'http://sw.danaaa.com/test_spider_category.html'
        self.mongo = MongoClient(MONGODB_URL)
        self.db = ''
        self.collection = ''

    def run(self):
        for item in self.mongo[self.db][self.collection].find():
            data = {}  # 将mongo里面的数据转换成注释对应的

            resp = requests.post(url=self.url, data=data)
            assert resp.status_code == 200


class TransferGoods2Admin:
    """
    {
        "base": {
            "provider": "SKU",
            "storeId": 694,
            "brandId": 313,
            "currencyId": 1,
            "categoryUuid": "categoryUuid-1",
            "categoryName": "DRESSES",
            "name": "my test product",
            "caption": "my test product Caption",
            "description": "Ted modernises a ",
            "introduction": "",
            "url": "http://www.tedbaker.com/uk/Womens/Clothing/Dresses/EMMONA-Embroidered-skater-dress-Ivory/p/137643-IVORY",
        },
        "images": [
            "img_url_1",
            "img_url_2",
        ],
        "colors": [
            {
                "price": 10,
                "promotionPrice": 8.1,
                "stock": 999,
                "specName1": "color",
                "specValue1": "Ivory",
                "specName2": "size",
                "specValue2": "M",
                "specName3": "material",
                "specValue3": "metal",
                "specName4": "country",
                "specValue4": "China",
                "specName5": "gender",
                "specValue5": "male"
            },
            {
                "price": 10,
                "promotionPrice": 8.1,
                "stock": 999,
                "specName1": "color",
                "specValue1": "red",
                "specName2": "size",
                "specValue2": "L",
                "specName3": "material",
                "specValue3": "metal",
                "specName4": "country",
                "specValue4": "China",
                "specName5": "gender",
                "specValue5": "male"
            },
        ]
    }
    """

    def __init__(self):
        self.url = 'http://sw.danaaa.com/test_add_sku.html'
        self.mongo = MongoClient(MONGODB_URL)
        self.db = ''
        self.collection = ''

    def run(self):
        def _transform(d):
            d = self.transform(d)
            resp = requests.post(url=self.url, data=d)
            assert resp.status_code == 200
            goods.clear()

        product_id, goods = None, []
        for item in self.mongo[self.db][self.collection].aggregate([{'$sort': {'product_id': 1}}]):
            if product_id and product_id != item['product_id']:
                _transform(goods)

            product_id = item['product_id']
            goods.append(item)

        if goods:
            _transform(goods)


    def transform(self, items):
        # 将mongo里面的数据转换成注释对应的
        
        data = {
            'base': {},
            'images': [],
            'colors': []
        }

        for item in items:
            data['base']['provider'] = item['store']
            data['base']['storeId'] = item['store_id']

            data['images'] = item['imgs']

            data['colors'].append({
              'price': item['price'],
              'promotionPrice': item['price'],

            })
        
        return self.build_form(data=data)

    def build_form(self, data):
        _ = self

        base_info = urllib.parse.urlencode(data['base'])
        images = urllib.parse.urlencode([('images', url) for url in data['images']])

        colors = {}
        for i, item in enumerate(data['colors']):
            for k, v in item.items():
                colors[f'spiderSkus.[{i}].{k}'] = v

        colors = urllib.parse.urlencode(colors)

        return '&'.join([base_info, images, colors])
