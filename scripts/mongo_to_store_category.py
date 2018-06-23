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
                'Lascivious',
                '923',
                '1'
            );
        '''

        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                json.dumps([{"id": None, "uuid": item['uuid'], "name": item['name'], "url": item['url'],
                             "children": item['children']}]),
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
                '1',
                %s,
                ',796,795,',
                '795',
                '442',
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

            print('store_category保存成功!')


if __name__ == "__main__":
    t = TransferGoodsProducts(db='LasciviousCrawler')
    t.run()
