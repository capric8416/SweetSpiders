# -*- coding: utf-8 -*-
# !/usr/bin/env python
import json

import pymongo
import pymysql


class TransferGoodsProducts:
    def __init__(self, db, collection='categories'):
        self.mysql = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='mysql',
            db='sweet',
            charset='utf8mb4'
        )

        self.mongo = pymongo.MongoClient('localhost', 27017)
        self.db = self.mongo[db]
        self.collection = self.db[collection]

    def run(self):
        for item in self.collection.find():
            self.insert_to_store_category(item)
            self.insert_to_store_product_category(item)

        self.mysql.commit()
        self.mysql.close()

    def insert_to_store_category(self, item):
        # 将数据导入xx_spider_store_product_category表中
        sql = '''
            insert into sweet.xx_spider_store_product_category values(
                '0',
                now(),
                now(),
                '5',
                null,
                %s,
                'Alexandermcqueen',
                '313',
                '1'
            );
        '''
        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                json.dumps([{"id": None, "uuid": item['uuid'], "name": item['name'], "url": item['url'],
                             "children": [
                                 {"id": None, "uuid": item['children'][0]['uuid'], "name": item['children'][0]['name'],
                                  "url": item['children'][0]['url'], "children": [
                                     {"id": None, "uuid": item['children']['children'][0]['uuid'],
                                      "name": item['children']['children'][0]['name'],
                                      "url": item['children']['children'][0]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][1]['children']['uuid'],
                                      "name": item['children']['children'][1]['name'],
                                      "url": item['children']['children'][1]['url'], "children": None},
                                     {"id": None, "uuid": item['children']['children'][2]['uuid'],
                                      "name": item['children']['children'][2]['name'],
                                      "url": item['children']['children'][2]['url'], "children": None}]},
                                 {"id": None, "uuid": item['children'][1]['uuid'], "name": item['children'][1]['name'],
                                  "url": item['children'][1]['url'], "children": [
                                     {"id": None, "uuid": item['children']['children'][0]['uuid'],
                                      "name": item['children']['children'][0]['name'],
                                      "url": item['children']['children'][0]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][1]['children']['uuid'],
                                      "name": item['children']['children'][1]['name'],
                                      "url": item['children']['children'][1]['url'], "children": None},
                                     {"id": None, "uuid": item['children']['children'][2]['uuid'],
                                      "name": item['children']['children'][2]['name'],
                                      "url": item['children']['children'][2]['url'], "children": None}]},
                             ]}]),
            ))

            print('spider_store_category保存成功!')

    def insert_to_store_product_category(self, item):
        # 将数据导入xx_store_product_category表中
        sql = '''
            insert into sweet.xx_store_product_category values(
                '0',
                now(),
                now(),
                '5',
                null,
                '0',
                %s,
                ',',
                null,
                '313',
                %s,
                %s,
                %s
            );
        '''
        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                item['name'],
                item['name'],
                item['url'],
                item['uuid'],
            ))

        sql = '''
            insert into sweet.xx_store_product_category values(
                '0',
                now(),
                now(),
                '5',
                null,
                '1',
                %s,
                ',一级分类id,',
                '一级分类id',
                '313',
                %s,
                %s,
                %s
            );
        '''
        for name_item in item['children']:
            with self.mysql.cursor() as cur:
                cur.execute(sql, (
                    name_item['name'],
                    name_item['name'],
                    name_item['url'],
                    name_item['uuid'],
                ))

        sql = '''
            insert into sweet.xx_store_product_category values(
                '0',
                now(),
                now(),
                '5',
                null,
                '2',
                %s,
                ',一级分类id,二级分类id,',
                '二级分类id',
                '313',
                %s,
                %s,
                %s
            );
        '''

        for third_item in item['children']['children']:
            with self.mysql.cursor() as cur:
                cur.execute(sql, (
                    third_item['name'],
                    third_item['name'],
                    third_item['url'],
                    third_item['uuid'],
                ))

                print('store_category保存成功!')


if __name__ == "__main__":
    t = TransferGoodsProducts(db='AlexandermcqueenCrawler')
    t.run()
