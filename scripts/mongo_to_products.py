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

        auth = oss2.Auth('pHrZGmZxcbOqvnod', 'dXzTR9DeVPZ5DeMShrNUIqKTKF7Eg5')
        host = 'oss-cn-beijing.aliyuncs.com'
        bucket = 'new-dana'
        endpoint = f'http://{host}'
        self.base_url = f'http://{bucket}.{host}'
        self.bucket = oss2.Bucket(auth, endpoint, bucket)

    def run(self):
        goods_image = []

        for item in self.collection.find():
            goods_id, images, url = self.insert_to_goods(item)
            self.insert_to_product(item, goods_id)

            goods_image.append([goods_id, images, url])

        self.convert_image_url(goods_image)

        self.mysql.commit()
        self.mysql.close()

    def convert_image_url(self, goods_images):
        """转换图片链接"""

        with ThreadPoolSubmit(
                action='starmap', func=self.image_download_and_update, iterable=goods_images, concurrency=20
        ) as res:
            for goods_id, dst in res:
                with self.mysql.cursor() as cur:
                    image = dst[0] + '?x-oss-process=image/resize,m_lfit,w_400,h_400'
                    product_images = [
                        {
                            "title": None, "order": None, "source": url,
                            "large": url + '?x-oss-process=image/resize,m_lfit,w_800,h_800',
                            "medium": url + '?x-oss-process=image/resize,m_lfit,w_400,h_400',
                            "thumbnail": url + '?x-oss-process=image/resize,m_lfit,w_200,h_200',
                        }
                        for url in dst
                    ]

                    cur.execute(
                        'update xx_goods set image = %s, product_images = %s where id = %s',
                        (image, json.dumps(product_images), goods_id)
                    )

                    print(f'更新商品图片成功: {goods_id}')

    def image_download_and_update(self, goods_id, images, url):
        headers = {
            'Referer': url,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/67.0.3396.79 Safari/537.36'
        }

        dst = []
        for image in images:
            path, data = self.download_image(url=image, headers=headers)
            self.upload_image(path=path, data=data)
            dst.append(f'{self.base_url}/{path}')

        print(f'下载-上传商品{len(dst)}张图片成功: {goods_id}')

        return goods_id, dst

    def download_image(self, url, headers):
        while True:
            try:
                data = requests.get(url=url, headers=headers).content
            except Exception as e:
                print(f'retry after {e}')
            else:
                return f'{hashlib.sha1(data).hexdigest()}.jpg', data

    def upload_image(self, path, data):
        while True:
            try:
                self.bucket.put_object(key=path, data=data)
            except Exception as e:
                print(f'retry after {e}')
            else:
                break

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

        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                item['brand'],
                item['name'],
                '',
                item['description'],
                item['description'],
                item['now_price'].lstrip('£'),
                item['categories'][1][0],
                item['now_price'].lstrip('£'),
                '',
                item['url'],
            ))

            print('商品保存成功!')

        with self.mysql.cursor() as cur:
            cur.execute('SELECT LAST_INSERT_ID();')
            goods_id = cur.fetchone()[0]

        return goods_id, item['images'], item['url']

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
