# -*- coding: utf-8 -*-
# !/usr/bin/env python


import datetime
import json
import urllib.parse

import requests
from SweetSpiders.common import CategoryUUID
from SweetSpiders.config import MONGODB_URL
from bson import ObjectId
from pymongo import MongoClient


class JSONEncoder(json.JSONEncoder):
    '''处理ObjectId,该类型无法转为json'''

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return datetime.datetime.strftime(o, '%Y-%m-%d %H:%M:%S')
        return json.JSONEncoder.default(self, o)


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
    """
    "categories": categories[0].provider=xxx&categories[0].storeId=xxx&categories[0].jsonCategory=xxx&
    categories[1].provider=xxx&categories[1].storeId=xxx&categories[1].jsonCategory=xxx
    """

    def __init__(self):
        self.url = 'http://sw.danaaa.com/api/spider/category.mo'
        self.mongo = MongoClient(MONGODB_URL)
        self.db = 'EttingerCrawler'
        self.products_collection = 'products'
        self.categories_collection = 'categories'
        self.category_uuid = CategoryUUID()

    def run(self):
        categories = []
        for cat in self.mongo[self.db][self.categories_collection].find():
            cat.pop('_id')
            categories.append(cat)

        product = self.mongo[self.db][self.products_collection].find_one()
        data = {
            'provider': product['brand'],
            'storeId': product['store_id'],
            'jsonCategory': json.dumps(categories)
        }

        resp = requests.post(url=self.url, data=data)
        print(resp.text)
        assert resp.status_code == 200

    def build_categories(self):
        """构建分类树: 废弃，从商品表获取的分类不全"""

        categories = [item['categories'] for item in self.mongo[self.db][self.products_collection].find()]

        tree = []
        for cat in categories:
            for i, item in enumerate(cat):
                item.append(self.category_uuid.get_or_create(*[x[0] for x in cat[:i + 1]]))

            tree.append({
                'name': cat[0][0], 'url': cat[0][1], 'uuid': cat[0][2],
                'children': [
                    {
                        'name': cat[1][0], 'url': cat[1][1], 'uuid': cat[1][2],
                        'children': [
                            {'name': cat[2][0], 'url': cat[2][1], 'uuid': cat[2][2]}
                        ]
                    }
                ]
            })

        return self.merge(tree)

    def merge(self, target):
        """递归合并children: 废弃，从商品表获取的分类不全"""

        _ = self

        result = []

        name = ''
        for cat in sorted(target, key=lambda d: d['name']):
            if cat['name'] != name:
                if result and 'children' in result[-1]:
                    result[-1]['children'] = self.merge(result[-1]['children'])
                result.append(cat)
                name = cat['name']
            else:
                if 'children' in result[-1]:
                    result[-1]['children'] += cat['children']

        if result and 'children' in result[-1]:
            result[-1]['children'] = self.merge(result[-1]['children'])

        return result


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
        self.db = 'EttingerCrawler'
        self.collection = 'products'

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
            data['base']['provider'] = item['brand']
            data['base']['storeId'] = item['store_id']
            data['base']['brandId'] = item['brand_id']
            data['base']['currencyId'] = item['coin_id']
            data['base']['categoryUuid'] = item['product_id']
            data['base']['categoryName'] = item['cat3_name']
            data['base']['name'] = item['name']
            data['base']['caption'] = item['title']
            data['base']['description'] = item['description']
            data['base']['introduction'] = item['title']
            data['base']['url'] = item['url']

            data['images'] = item['images']

            data['colors'].append({
                'price': item['price'],
                'promotionPrice': item['price'],
                'stock': item['in_stock'],
                'specName1': 'color',
                'specValue1': item['color'],
                'specName2': 'size',
                'specValue2': item['size'],
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


if __name__ == '__main__':
    admin = TransferCategory2Admin()
    admin.run()
