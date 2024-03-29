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
        category_list = []
        for i, item in enumerate(self.collection.find()):
            self.insert_to_store_product_category(item)

            first_category_item = {'id': i, 'uuid': item['uuid'], 'name': item['name'], 'url': item['url'],
                                   'children': []}
            if item.get('children'):
                for j, second_category in enumerate(item['children']):
                    second_category_item = {'id': j, 'uuid': second_category['uuid'],
                                            'name': second_category['name'],
                                            'url': second_category['url'], 'children': None}
                    first_category_item['children'].append(second_category_item)
            category_list.append(first_category_item)

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
                json.dumps(category_list),
            ))

            print('spider_store_category保存成功!')

        self.mysql.commit()
        self.mysql.close()

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
