# -*- coding: utf-8 -*-
# !/usr/bin/env python
import oss2
import json

import pymongo
import pymysql


class TransferGoodsProducts:
    def __init__(self, db, collection='products'):
        self.mysql = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='mysql',
            db='sw',
            charset='utf8mb4'
        )

        self.mongo = pymongo.MongoClient('localhost', 27017)
        self.db = self.mongo[db]
        self.collection = self.db[collection]

    def run(self):
        for item in self.collection.find():
            goods_id = self.insert_to_goods(item)
            self.insert_to_product(item, goods_id)

        self.mysql.commit()
        self.mysql.close()

    def transfer_image_url(self, img_url):
        """转换图片链接"""
        auth = oss2.Auth('pHrZGmZxcbOqvnod', 'dXzTR9DeVPZ5DeMShrNUIqKTKF7Eg5')
        bucket = oss2.Bucket(auth, 'http://res.danaaa.com', 'dana1')
        pass

    def insert_to_goods(self, item):
        # 将数据导入xx_goods表中
        sql = '''
            insert into sw.xx_goods values(
                '0',
                now(),
                now(),
                '42',
                %s,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                '0',
                %s,
                %s,
                %s,
                0,
                1,
                1,
                1,
                0,
                null,
                %s,
                null,
                '0',
                now(),
                '0',
                now(),
                %s,
                '[]',
                %s,
                %s,
                '0',
                '0',
                '0',
                null,
                null,
                null,
                '2018061012041',
                '[]',
                '0',
                '0',
                null,
                '0',
                now(),
                '0',
                now(),
                null,
                '442',
                '302',
                '923',
                null,
                null,
                null,
                %s,
                null,
                null,
                0,
                null,
                null,
                '0',
                '3225',
                '36',
                '0.000000'
            );
        '''

        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                item['brand'],
                item['images'][0],
                item['description'],
                item['description'],
                item['now_price'].lstrip('£'),
                item['categories'][1][0],
                item['now_price'].lstrip('£'),
                item['images'][0],
                item['url'],
            ))

            print('商品保存成功!')

        with self.mysql.cursor() as cur:
            cur.execute('SELECT LAST_INSERT_ID();')
            return cur.fetchone()[0]

    def insert_to_product(self, item, goods_id):
        # 将数据导入xx_product表中

        sql = '''
                insert into sw.xx_product values (
                    '0',
                    now(),
                    now(),
                    '47',
                    %s,
                    null,
                    '0',
                    0,
                    %s,
                    %s,
                    %s,
                    '2018062015334',
                    %s,
                    %s,
                    %s,
                    %s,
                    null,
                    %s,
                    null,
                    null
            );
            '''

        for size in item['size']:
            with self.mysql.cursor() as cur:
                cur.execute(sql, (
                    item['stock'],
                    item['now_price'].lstrip('£'),
                    item['now_price'].lstrip('£'),
                    item['now_price'].lstrip('£'),
                    json.dumps([{'size': size}]),
                    item['stock'],
                    goods_id,
                    item['now_price'].lstrip('£'),
                    item['url'],
                ))

                print('货品保存成功!')


if __name__ == "__main__":
    t = TransferGoodsProducts(db='LasciviousCrawler')
    t.run()
