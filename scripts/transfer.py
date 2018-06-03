# -*- coding: utf-8 -*-
# !/usr/bin/env python


import json
import urllib.parse

import requests
from SweetSpiders.common import CategoryUUID
from SweetSpiders.config import MONGODB_URL
from pymongo import MongoClient


class TransferCategory2Admin:
    """
    三级分类EttingerCrawler
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
        self.url = 'http://sw.danaaa.com/api/spider/category.mo'
        self.mongo = MongoClient(MONGODB_URL)
        self.db = 'EttingerCrawler'
        self.products_collection = 'products'
        self.categories_collection = 'categories'
        self.category_uuid = CategoryUUID()

    def run(self):
        categories = []
        for cat in self.mongo[self.db][self.categories_collection].find({"name": {"$in": ['Men', 'Women']}}):
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


class TransferCategories:
    """二级分类LasciviousCrawler"""

    def __init__(self):
        self.url = 'http://sw.danaaa.com/api/spider/category.mo'
        self.mongo = MongoClient(MONGODB_URL)
        self.db = 'LasciviousCrawler'
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
    三级分类商品上传EttingerCrawler
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
        self.url = 'http://sw.danaaa.com/api/spider/add_by_sku.mo'
        self.mongo = MongoClient(MONGODB_URL)
        self.db = 'EttingerCrawler'
        self.collection = 'products'

    def run(self):
        def _transform(d):
            d = self.transform(d)
            resp = requests.post(url=self.url, data=json.dumps(d))
            print(resp.text)
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
            data['base']['categoryName'] = item['categories'][2][0]
            data['base']['name'] = item['name']
            data['base']['caption'] = item['title']
            data['base']['description'] = item['description']
            data['base']['introduction'] = item['title']
            data['base']['url'] = item['url']

            data['images'] = item['images']

            data['colors'].append({
                'price': item['price'][1:],
                'promotionPrice': '',
                'stock': 10,
                'specName1': 'color',
                'specValue1': item['color'],
                'specName2': 'size',
                'specValue2': None,
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

    def start(self):
        for item in self.mongo[self.db][self.collection].find():
            data = {}
            data["provider"] = item['brand']
            data["storeId"] = item['store_id']
            data["brandId"] = item['brand_id']
            data["currencyId"] = item['coin_id']
            data["categoryUuid"] = item['product_id']
            data["categoryName"] = item['categories'][2][0]
            data["name"] = item['name']
            if not item['name']:
                data["name"] = item['brand']
            data["caption"] = item['title']
            data["description"] = ''.join(item['features'])
            data["introduction"] = item['description']
            data["url"] = item['url']
            for i, img in enumerate(item['images']):
                data['images[%d]' % i] = img
            data["spiderSkus[0].price"] = item['price'][1:]
            data["spiderSkus[0].promotionPrice"] = ''
            data["spiderSkus[0].stock"] = 999
            data["spiderSkus[0].specName1"] = 'color'
            data["spiderSkus[0].specValue1"] = item['color']
            data["spiderSkus[0].specName2"] = 'meterial'
            data["spiderSkus[0].specValue2"] = item['meterial']
            data["spiderSkus[0].specName3"] = ''
            data["spiderSkus[0].specValue3"] = ''
            data["spiderSkus[0].specName4"] = ''
            data["spiderSkus[0].specValue4"] = ''
            data["spiderSkus[0].specName5"] = ''
            data["spiderSkus[0].specValue5"] = ''

            resp = requests.post(url=self.url, data=data)
            print(resp.text)
            # assert resp.status_code == 200


class TransferGoods:
    """二级分类商品上传LasciviousCrawler"""

    def __init__(self):
        self.url = 'http://sw.danaaa.com/api/spider/add_by_sku.mo'
        self.mongo = MongoClient(MONGODB_URL)
        self.db = 'LasciviousCrawler'
        self.collection = 'products'

    def start(self):
        for item in self.mongo[self.db][self.collection].find():
            data = {}
            data["provider"] = item['brand']
            data["storeId"] = item['store_id']
            data["brandId"] = item['brand_id']
            data["currencyId"] = item['coin_id']
            data["categoryUuid"] = item['product_id']
            data["categoryName"] = item['categories'][1][0]
            data["name"] = item['name']
            if not item['name']:
                data["name"] = item['brand']
            data["caption"] = item['name']
            data["description"] = item['description']
            data["introduction"] = item['description']
            data["url"] = item['url']
            for i, img in enumerate(item['images']):
                data['images[%d]' % i] = img
            data["spiderSkus[0].price"] = item['was_price'][1:]
            if not item['was_price']:
                data["spiderSkus[0].price"] = item['now_price'][1:]
                data["piderSkus[0].promotionPrice"] = ''
            else:
                data["spiderSkus[0].promotionPrice"] = item['now_price'][1:]
            data["spiderSkus[0].stock"] = item['stock']
            for i, size in enumerate(item['size']):
                data["spiderSkus[0].specName%d" % int(i + 1)] = 'size'
                data["spiderSkus[0].specValue%d" % int(i + 1)] = size.split('-')[0].strip()

            resp = requests.post(url=self.url, data=data)
            print(resp.text)
            assert resp.status_code == 200


if __name__ == '__main__':
    # admin = TransferCategory2Admin()
    # admin.run()
    # admin = TransferCategories()
    # admin.run()
    admin = TransferGoods2Admin()
    admin.start()
    # admin = TransferGoods()
    # admin.start()
