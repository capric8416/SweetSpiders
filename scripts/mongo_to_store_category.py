# -*- coding: utf-8 -*-
# !/usr/bin/env python
import json

import pymongo
import pymysql


class TransferGoodsProducts:
    def __init__(self, db, collection='categories'):
        self.mysql = pymysql.connect(
            host='59.110.155.75',
            port=3306,
            user='root',
            passwd='Dana1234!',
            db='sweet',
            charset='utf8mb4'
        )

        self.mongo = pymongo.MongoClient('localhost', 27017)
        self.db = self.mongo[db]
        self.collection = self.db[collection]

    def run(self):
        for item in self.collection.find():
            # self.insert_to_store_category(item)
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
                '6',
                null,
                %s,
                'Crabtree & Evelyn',
                '541',
                '1'
            );
        '''
        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                json.dumps([{"id": None, "uuid": item['uuid'], "name": item['name'],
                             "url": item['url'],
                             "children": [
                                 {"id": None, "uuid": item['children'][0]['uuid'],
                                  "name": item['children'][0]['name'],
                                  "url": item['children'][0]['url'], "children": None},
                                 {"id": None, "uuid": item['children'][1]['uuid'],
                                  "name": item['children'][0]['name'],
                                  "url": item['children'][0]['url'], "children": None},
                                 {"id": None, "uuid": item['children'][2]['uuid'],
                                  "name": item['children'][0]['name'],
                                  "url": item['children'][0]['url'], "children": None},
                                 {"id": None, "uuid": item['children'][3]['uuid'],
                                  "name": item['children'][0]['name'],
                                  "url": item['children'][0]['url'], "children": None},
                                 {"id": None, "uuid": item['children'][4]['uuid'],
                                  "name": item['children'][0]['name'],
                                  "url": item['children'][0]['url'], "children": None},
                                 {"id": None, "uuid": item['children'][5]['uuid'],
                                  "name": item['children'][0]['name'],
                                  "url": item['children'][0]['url'], "children": None}
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
                '541',
                %s,
                %s,
                %s
            );
        '''
        with self.mysql.cursor() as cur:
            cur.execute(sql, (
                item['name_cn'],
                item['name'],
                item['url'],
                item['uuid'],
            ))
        with self.mysql.cursor() as cur:
            cur.execute('SELECT LAST_INSERT_ID();')
            cat1_id = cur.fetchone()[0]

            print('一级分类插入成功!')

            if item.get('children'):
                for cat2_data in item['children']:
                    sql = '''
                        insert into sweet.xx_store_product_category values(
                            '0',
                            now(),
                            now(),
                            '5',
                            null,
                            '1',
                            %s,
                            %s,
                            %s,
                            '541',
                            %s,
                            %s,
                            %s
                        );
                    '''
                    with self.mysql.cursor() as cur:
                        cur.execute(sql, (
                            cat2_data['name_cn'],
                            ',' + str(cat1_id) + ',',
                            str(cat1_id),
                            cat2_data['name'],
                            cat2_data['url'],
                            cat2_data['uuid'],
                        ))

                    print('二级分类插入成功!')


if __name__ == "__main__":
    t = TransferGoodsProducts(db='CrabtreeCrawler')
    t.run()
