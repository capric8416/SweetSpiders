# -*- coding: utf-8 -*-
# !/usr/bin/env python
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
            db='sweet',
            charset='utf8mb4'
        )

        self.mongo = pymongo.MongoClient('localhost', 27017)
        self.db = self.mongo[db]
        self.collection = self.db[collection]

    def run(self):
        count = 36494
        for item in self.collection.find({"categories": [
            ["Womenswear", "女装", "https://www.alexandermcqueen.com/gb/alexandermcqueen"],
            ["All Bags", "所有包包", "https://www.alexandermcqueen.com/gb/alexandermcqueen/online/women/bags"],
            ["Crossbody Bags", "斜挎包",
             "https://www.alexandermcqueen.com/gb/alexandermcqueen/online/women/crossbody-bags"]]}
        ):
            self.insert_to_goods(item)
            self.insert_to_spider_product(item)
            self.insert_to_product(item, count)
            count += 1

        self.mysql.commit()
        self.mysql.close()

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
                '2018071012041',
                '[]',
                '0',
                '0',
                null,
                '0',
                now(),
                '0',
                now(),
                null,
                '441',
                '307',
                '313',
                '2400',
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
                '2400',
                '0.000000',
                '24'
            );
        '''

        image = item['images'][0] + '?x-oss-process=image/resize,m_lfit,w_400,h_400'
        with self.mysql.cursor() as cur:
            product_images = [
                {
                    "title": None, "order": None, "source": img_url,
                    "large": img_url + '?x-oss-process=image/resize,m_lfit,w_800,h_800',
                    "medium": img_url + '?x-oss-process=image/resize,m_lfit,w_400,h_400',
                    "thumbnail": img_url + '?x-oss-process=image/resize,m_lfit,w_200,h_200',
                }
                for img_url in item['images']
            ]
        try:
            with self.mysql.cursor() as cur:
                cur.execute(sql, (
                    item['brand'],
                    item['name'],
                    image,
                    item['introduction'],
                    item['introduction'],
                    item['price'].split()[0].replace(',', ''),
                    item['name'],
                    item['price'].split()[0].replace(',', ''),
                    json.dumps(product_images),
                    item['url'],
                ))

                print('xx_goods商品保存成功!')
        except Exception as e:
            print(e)

    def insert_to_spider_product(self, item):
        # 将数据导入xx_spider_product表中

        sql = '''
                insert into sweet.xx_spider_product values(
                    '0',
                    now(),
                    now(),
                    '5',
                    %s,
                    %s,
                    '1',
                    %s,
                    %s,
                    null,
                    %s,
                    %s,
                    null,
                    '313',
                    %s,
                    null,
                    '1',
                    null,
                    '441'
                );
            '''
        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                item['product_id'],
                item['name'],
                '<p>' + item['introduction'] + '</p>',
                json.dumps(item['images']),
                item['name'],
                item['brand'],
                item['url'],
            ))
            print('xx_spider_product保存成功!')

    def insert_to_product(self, item, count):
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
        if item.get('sizes'):
            for i, size in enumerate(item['sizes']):
                try:
                    with self.mysql.cursor() as cur:
                        cur.execute(sql, (
                            item['price'].split()[0].replace(',', ''),
                            item['price'].split()[0].replace(',', ''),
                            item['price'].split()[0].replace(',', ''),
                            json.dumps([{"id": i, "value": size}]),
                            int(count),
                            item['price'].split()[0].replace(',', ''),
                            item['url'],
                        ))

                        print('xx_product货品保存成功!')
                except Exception as e:
                    print(e)

        else:
            for i, color in enumerate(item['color']):
                try:
                    with self.mysql.cursor() as cur:
                        cur.execute(sql, (
                            item['price'].split()[0].replace(',', ''),
                            item['price'].split()[0].replace(',', ''),
                            item['price'].split()[0].replace(',', ''),
                            json.dumps([{"id": i, "value": color}]),
                            int(count),
                            item['price'].split()[0].replace(',', ''),
                            item['url'],
                        ))

                        print('xx_product货品保存成功!')
                except Exception as e:
                    print(e)


if __name__ == "__main__":
    t = TransferGoodsProducts(db='AlexandermcqueenCrawler')
    t.run()
