# -*- coding: utf-8 -*-
# !/usr/bin/env python
import hashlib
import json

import pymongo
import redis
from SweetSpiders.config.mongo import MONGODB_URL
from SweetSpiders.config.redis import REDIS_URL


class CategoriesMapper:
    def __init__(self, db, collection='products', name='category_map'):
        self.mongo = pymongo.MongoClient(MONGODB_URL)
        self.db = self.mongo[db]
        self.collection = self.db[collection]

        self.redis = redis.from_url(REDIS_URL)
        self.name = name

    def run(self):
        for categories in sorted(self.read_categories()):
            self.map_category(categories=categories)

    def read_categories(self):
        return {
            tuple(tuple(c) for c in item['categories'])
            for item in self.collection.find()
        }

    def map_category(self, categories):
        key = self.get_key(categories=categories)
        value = self.get_value(key=key)
        print(key, [category[0] for category in categories], categories[-1][-1], value, end='\t')

        if value:
            print('命中')
        else:
            categories_id = int(input('填写: '))
            assert categories_id, '分类不能为空'

            self.redis.hset(self.name, key, categories_id)

    @staticmethod
    def get_key(categories):
        return hashlib.sha1(json.dumps([item[0] for item in categories]).encode()).hexdigest()

    def get_value(self, key):
        return self.redis.hget(self.name, key)

    def get_value_by_categories(self, categories):
        return self.get_value(key=self.get_key(categories=categories))


if __name__ == '__main__':
    rc = CategoriesMapper(db='AlexandermcqueenCrawler')
    rc.run()
