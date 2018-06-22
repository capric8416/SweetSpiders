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
            db='sweet',
            charset='utf8mb4'
        )

        self.mongo = pymongo.MongoClient('localhost', 27017)
        self.db = self.mongo[db]
        self.collection = self.db[collection]

        # auth = oss2.Auth('pHrZGmZxcbOqvnod', 'dXzTR9DeVPZ5DeMShrNUIqKTKF7Eg5')
        # host = 'oss-cn-beijing.aliyuncs.com'
        # bucket = 'new-dana'
        # endpoint = f'http://{host}'
        # self.base_url = f'http://{bucket}.{host}'
        # self.bucket = oss2.Bucket(auth, endpoint, bucket)

    def run(self):
        goods_image = []

        for item in self.collection.find():
            goods_id, image, url = self.insert_to_goods(item)
            self.insert_to_product(item, goods_id)

            # goods_image.append([goods_id, image, url])

        # self.convert_image_url(goods_image)

        self.mysql.commit()
        self.mysql.close()

    def convert_image_url(self, goods_images):
        """转换图片链接"""

        with ThreadPoolSubmit(
                action='starmap', func=self.image_download_and_update, iterable=goods_images, concurrency=20
        ) as res:
            for goods_id, dst in res:
                with self.mysql.cursor() as cur:
                    cur.execute('update xx_goods set image = %s where id = %s;',
                                (dst + '?x-oss-process=image/resize,m_lfit,w_400,h_400', goods_id))
                    cur.execute('update xx_goods set product_images = %s where id = %s;', (json.dumps([{"title": "null",
                                                                                                        "source": dst,
                                                                                                        "large": dst + '?x-oss-process=image/resize,m_lfit,w_800,h_800',
                                                                                                        "medium": dst + '?x-oss-process=image/resize,m_lfit,w_400,h_400',
                                                                                                        "thumbnail": dst + '?x-oss-process=image/resize,m_lfit,w_200,h_200',
                                                                                                        "order": "null"}]),
                                                                                           goods_id))
                    print(f'更新商品图片成功: {goods_id} {dst}')

    def image_download_and_update(self, goods_id, image, url):
        headers = {
            'Referer': url,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/67.0.3396.79 Safari/537.36'
        }

        data = requests.get(url=image, headers=headers).content
        path = f'{hashlib.sha1(data).hexdigest()}.jpg'

        self.bucket.put_object(key=path, data=data)

        return goods_id, f'{self.base_url}/{path}'

    def insert_to_goods(self, item):
        # 将数据导入xx_goods表中
        sql = '''
            insert into sweet.xx_goods values(
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
                %s,
                '0',
                %s,
                %s,
                %s,
                1,
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
                '27',
                '0.000000',
                '27'
            );
        '''

        image = item['images'][0]

        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                item['brand'],
                item['name'],
                item['images'][0],
                '<p>'+item['description']+'</p>',
                '<p>'+item['description']+'</p>',
                item['now_price'].lstrip('£'),
                item['categories'][1][0],
                item['now_price'].lstrip('£'),
                json.dumps([{"title": "null", "source": item['images'][0],
                             "large": item['images'][0] + '?x-oss-process=image/resize,m_lfit,w_800,h_800',
                             "medium": item['images'][0] + '?x-oss-process=image/resize,m_lfit,w_400,h_400',
                             "thumbnail": item['images'][0] + '?x-oss-process=image/resize,m_lfit,w_200,h_200',
                             "order": "null"}, {"title": "null", "source": item['images'][1],
                                                "large": item['images'][
                                                             1] + '?x-oss-process=image/resize,m_lfit,w_800,h_800',
                                                "medium": item['images'][
                                                              1] + '?x-oss-process=image/resize,m_lfit,w_400,h_400',
                                                "thumbnail": item['images'][
                                                                 1] + '?x-oss-process=image/resize,m_lfit,w_200,h_200',
                                                "order": "null"}]),
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
                insert into sweet.xx_product values (
                    '0',
                    now(),
                    now(),
                    '47',
                    '0',
                    null,
                    '0',
                    1,
                    %s,
                    %s,
                    %s,
                    '2018062015334',
                    %s,
                    '1000',
                    %s,
                    %s,
                    '1',
                    %s,
                    null,
                    null
            );
            '''

        for i, size in enumerate(item['size']):
            with self.mysql.cursor() as cur:
                cur.execute(sql, (
                    item['now_price'].lstrip('£'),
                    item['now_price'].lstrip('£'),
                    item['now_price'].lstrip('£'),
                    json.dumps([{"id": i, "value": size.split('-')[0]}]),
                    goods_id,
                    item['now_price'].lstrip('£'),
                    item['url'],
                ))

                print('货品保存成功!')


if __name__ == "__main__":
    t = TransferGoodsProducts(db='LasciviousCrawler')
    t.run()

