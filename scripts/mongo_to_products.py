# -*- coding: utf-8 -*-
# !/usr/bin/env python
import hashlib
import json

import oss2
import pymongo
import pymysql
import requests
from SweetSpiders.common import ThreadPoolSubmit

from scripts.google_translate import GoogleTranslate


class TransferGoodsProducts:
    def __init__(self, db, collection='products'):
        self.mysql = pymysql.connect(
            host='59.110.155.75',
            port=3306,
            user='root',
            passwd='Dana1234!',
            db='b2b2c',
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

        for item in self.collection.find({"categories": [
            ["Women", "妇女", "https://www.tedbaker.com/uk/Womens/c/category_womens"], ["Accessories", "饰品",
                                                                                      "https://www.tedbaker.com/uk/Womens/Accessories/c/category_womens_accessories?int_cmpid=_mn_w_accessories"],
            ["Phone and Tablet Cases", "手机和平板电脑包",
             "https://www.tedbaker.com/uk/Womens/Accessories/Tech-Cases/c/womens_tech_cases?int_cmpid=_mn_w_phone_cases"]]}
        ):
            goods_id, images, url, categories = self.insert_to_goods(item)

            # translated = self.read_categories(categories=categories)
            # products_id = item['_id']
            # self.db['products'].update({'_id': products_id}, {'$set': {'categories_cn': translated}})
            # print('mongo更新完毕!')

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

    def read_categories(self, categories):
        source = [c[0] for c in categories]
        g = GoogleTranslate()
        return list(g.batch_query(source))

    def insert_to_goods(self, item):
        # 将数据导入xx_goods表中
        sql = '''
            insert into b2b2c.xx_goods values(
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
                null,
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
                '2018071812041',
                %s,
                '0',
                '0',
                null,
                '0',
                now(),
                '0',
                now(),
                null,
                '405',
                '308',
                '514',
                '360',
                null,
                %s,
                %s,
                null,
                null,
                0,
                null,
                null,
                '0',
                '3225',
                '360',
                '0.000000',
                '124',
                '405',
                '514'
            );
        '''
        specification_list = []
        specification_color = {"id": "1", "name": "颜色", "nameEn": None, "entries": []}
        length = len(item['colors'])
        for i, color in enumerate(item['colors']):
            # selected = i == 0
            entries_color = {"id": i, "value": color, "valueEn": None, "isSelected": True}
            specification_color['entries'].append(entries_color)
        specification_list.append(specification_color)

        specification_size = {"id": "2", "name": "尺寸", "nameEn": None, "entries": []}
        for j, size in enumerate(item['sizes']):
            # selected = j == 0
            entries_size = {"id": j + length, "value": size, "valueEn": None, "isSelected": True}
            specification_size['entries'].append(entries_size)
        specification_list.append(specification_size)

        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                item['brand'],
                item['brand'],
                '',
                item['introduction'],
                item['now_price'].lstrip('£'),
                item['name'],
                item['now_price'].lstrip('£'),
                '',
                json.dumps(specification_list),
                item['name'],
                item['url'],
            ))

        print('商品保存成功!')

        with self.mysql.cursor() as cur:
            cur.execute('SELECT LAST_INSERT_ID();')
            goods_id = cur.fetchone()[0]

        return goods_id, item['images'], item['url'], item['categories']

    def insert_to_product(self, item, goods_id):
        # 将数据导入xx_product表中

        sql = '''
                insert into b2b2c.xx_product values (
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
                    '2018071015334',
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
        length = len(item['colors'])
        for i, color in enumerate(item['colors']):
            for j, size in enumerate(item['sizes']):
                with self.mysql.cursor() as cur:
                    cur.execute(sql, (
                        item['now_price'].lstrip('£'),
                        item['now_price'].lstrip('£'),
                        item['now_price'].lstrip('£'),
                        json.dumps([{"id": i, "value": color}, {"id": j + length, "value": size}]),
                        goods_id,
                        item['now_price'].lstrip('£'),
                        item['url'],
                    ))

                    print('货品保存成功!')


if __name__ == "__main__":
    t = TransferGoodsProducts(db='TedbakerCrawler')
    t.run()
