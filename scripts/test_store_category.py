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
            db='b2b2c',
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
                    second_category_item = {'id': j, 'uuid': second_category['uuid'], 'name': second_category['name'],
                                            'url': second_category['url'], 'children': []}
                    if second_category.get('children'):
                        for k, third_category in enumerate(second_category['children']):
                            third_category_item = {'id': k, 'uuid': third_category['uuid'],
                                                   'name': third_category['name'],
                                                   'url': third_category['url'], 'children': None}
                            second_category_item['children'].append(third_category_item)
                    first_category_item['children'].append(second_category_item)
            category_list.append(first_category_item)

        # 将数据导入xx_spider_store_product_category表中

        sql = '''
            insert into b2b2c.xx_spider_store_product_category values(
                '0',
                now(),
                now(),
                '6',
                null,
                %s,
                'Alexander McQueen',
                '313',
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
            insert into b2b2c.xx_store_product_category values(
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
                        insert into b2b2c.xx_store_product_category values(
                            '0',
                            now(),
                            now(),
                            '5',
                            null,
                            '1',
                            %s,
                            %s,
                            %s,
                            '313',
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

                    with self.mysql.cursor() as cur:
                        cur.execute('SELECT LAST_INSERT_ID();')
                        cat2_id = cur.fetchone()[0]

                        print('二级分类插入成功!')

                        if cat2_data.get('children'):
                            for cat3_data in cat2_data['children']:
                                sql = '''
                                    insert into b2b2c.xx_store_product_category values(
                                        '0',
                                        now(),
                                        now(),
                                        '5',
                                        null,
                                        '2',
                                        %s,
                                        %s,
                                        %s,
                                        '313',
                                        %s,
                                        %s,
                                        %s
                                    );
                                '''
                                with self.mysql.cursor() as cur:
                                    cur.execute(sql, (
                                        cat3_data['name_cn'],
                                        ',' + str(cat1_id) + ',' + str(cat2_id) + ',',
                                        str(cat2_id),
                                        cat3_data['name'],
                                        cat3_data['url'],
                                        cat3_data['uuid'],
                                    ))

                                print('三级分类插入成功!')


if __name__ == "__main__":
    t = TransferGoodsProducts(db='AlexandermcqueenCrawler')
    t.run()
