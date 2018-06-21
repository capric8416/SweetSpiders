# -*- coding: utf-8 -*-
# !/usr/bin/env python
import hashlib
import json

import oss2
import pymongo
import pymysql
import requests
from SweetSpiders.common import ThreadPoolSubmit


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

        auth = oss2.Auth('pHrZGmZxcbOqvnod', 'dXzTR9DeVPZ5DeMShrNUIqKTKF7Eg5')
        self.bucket = oss2.Bucket(auth, 'http://oss-cn-qingdao.aliyuncs.com', 'dana1')

    def run(self):
        goods_image = []

        for item in self.collection.find():
            goods_id, image, url = self.insert_to_goods(item)
            self.insert_to_product(item, goods_id)

            goods_image.append([goods_id, image, url])

        self.convert_image_url(goods_image)

        self.mysql.commit()
        self.mysql.close()

    def convert_image_url(self, goods_images):
        """转换图片链接"""

        with ThreadPoolSubmit(func=self.image_download_and_update, iterable=goods_images, concurrency=20) as res:
            for (goods_id, *_), dst in zip(goods_images, res):
                with self.mysql.cursor() as cur:
                    cur.execute('update xx_goods set source_url = %s where id = %s;', dst, goods_id)
                    print(f'更新商品图片成功: {goods_id} {dst}')

    def image_download_and_update(self, src, referer):
        headers = {
            'Referer': referer,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/67.0.3396.79 Safari/537.36'
        }

        data = requests.get(url=src, headers=headers).content
        path = f'sweet/{hashlib.sha1(data).hexdigest()}.jpg'

        self.bucket.put_object(key=path, data=data)

        return f'http://res.danaaa.com/dana1/{path}'

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

        image = item['images'][0]

        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                item['brand'],
                item['images'][0],
                item['description'],
                item['description'],
                item['now_price'].lstrip('£'),
                item['categories'][1][0],
                item['now_price'].lstrip('£'),
                image,
                item['url'],
            ))

            print('商品保存成功!')

        with self.mysql.cursor() as cur:
            cur.execute('SELECT LAST_INSERT_ID();')
            goods_id = cur.fetchone()[0]

        return goods_id, image, item['url']

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
    # t.run()

    t.image_download_and_update(
        src='https://cdn.shopify.com/s/files/1/0903/9008/products/'
            'Purple-Kitty-Suspender-Product-1_1024x1024.jpg?v=1473623377',
        referer=''
    )
