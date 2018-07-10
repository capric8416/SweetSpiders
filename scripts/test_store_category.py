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
                'Alexander McQueen',
                '313',
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
                                  "url": item['children'][0]['url'], "children": [
                                     {"id": None, "uuid": item['children'][0]['children'][0]['uuid'],
                                      "name": item['children'][0]['children'][0]['name'],
                                      "url": item['children'][0]['children'][0]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][0]['children'][1]['uuid'],
                                      "name": item['children'][0]['children'][1]['name'],
                                      "url": item['children'][0]['children'][1]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][0]['children'][2]['uuid'],
                                      "name": item['children'][0]['children'][2]['name'],
                                      "url": item['children'][0]['children'][2]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][0]['children'][3]['uuid'],
                                      "name": item['children'][0]['children'][3]['name'],
                                      "url": item['children'][0]['children'][3]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][0]['children'][4]['uuid'],
                                      "name": item['children'][0]['children'][4]['name'],
                                      "url": item['children'][0]['children'][4]['url'], "children": None},
                                 ]},
                                 {"id": None, "uuid": item['children'][1]['uuid'],
                                  "name": item['children'][1]['name'],
                                  "url": item['children'][1]['url'], "children": [
                                     {"id": None, "uuid": item['children'][1]['children'][0]['uuid'],
                                      "name": item['children'][1]['children'][0]['name'],
                                      "url": item['children'][1]['children'][0]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][1]['children'][1]['uuid'],
                                      "name": item['children'][1]['children'][1]['name'],
                                      "url": item['children'][1]['children'][1]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][1]['children'][2]['uuid'],
                                      "name": item['children'][1]['children'][2]['name'],
                                      "url": item['children'][1]['children'][2]['url'], "children": None}
                                 ]},
                                 {"id": None, "uuid": item['children'][2]['uuid'],
                                  "name": item['children'][2]['name'],
                                  "url": item['children'][1]['url'], "children": [
                                     {"id": None, "uuid": item['children'][2]['children'][0]['uuid'],
                                      "name": item['children'][2]['children'][0]['name'],
                                      "url": item['children'][2]['children'][0]['url'], "children": None},
                                 ]},
                                 {"id": None, "uuid": item['children'][3]['uuid'],
                                  "name": item['children'][3]['name'],
                                  "url": item['children'][3]['url'], "children": [
                                     {"id": None, "uuid": item['children'][3]['children'][0]['uuid'],
                                      "name": item['children'][3]['children'][0]['name'],
                                      "url": item['children'][3]['children'][0]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][3]['children'][1]['uuid'],
                                      "name": item['children'][3]['children'][1]['name'],
                                      "url": item['children'][3]['children'][1]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][3]['children'][2]['uuid'],
                                      "name": item['children'][3]['children'][2]['name'],
                                      "url": item['children'][3]['children'][2]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][3]['children'][3]['uuid'],
                                      "name": item['children'][3]['children'][3]['name'],
                                      "url": item['children'][3]['children'][3]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][3]['children'][4]['uuid'],
                                      "name": item['children'][3]['children'][4]['name'],
                                      "url": item['children'][3]['children'][4]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][3]['children'][5]['uuid'],
                                      "name": item['children'][3]['children'][5]['name'],
                                      "url": item['children'][3]['children'][5]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][3]['children'][6]['uuid'],
                                      "name": item['children'][3]['children'][6]['name'],
                                      "url": item['children'][3]['children'][6]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][3]['children'][7]['uuid'],
                                      "name": item['children'][3]['children'][7]['name'],
                                      "url": item['children'][3]['children'][7]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][3]['children'][8]['uuid'],
                                      "name": item['children'][3]['children'][8]['name'],
                                      "url": item['children'][3]['children'][8]['url'], "children": None}
                                 ]},
                                 {"id": None, "uuid": item['children'][4]['uuid'],
                                  "name": item['children'][4]['name'],
                                  "url": item['children'][4]['url'], "children": [
                                     {"id": None, "uuid": item['children'][4]['children'][0]['uuid'],
                                      "name": item['children'][4]['children'][0]['name'],
                                      "url": item['children'][4]['children'][0]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][4]['children'][1]['uuid'],
                                      "name": item['children'][4]['children'][1]['name'],
                                      "url": item['children'][4]['children'][1]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][4]['children'][2]['uuid'],
                                      "name": item['children'][4]['children'][2]['name'],
                                      "url": item['children'][4]['children'][2]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][4]['children'][3]['uuid'],
                                      "name": item['children'][4]['children'][3]['name'],
                                      "url": item['children'][4]['children'][3]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][4]['children'][4]['uuid'],
                                      "name": item['children'][4]['children'][4]['name'],
                                      "url": item['children'][4]['children'][4]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][4]['children'][5]['uuid'],
                                      "name": item['children'][4]['children'][5]['name'],
                                      "url": item['children'][4]['children'][5]['url'], "children": None}
                                 ]},
                                 {"id": None, "uuid": item['children'][5]['uuid'],
                                  "name": item['children'][5]['name'],
                                  "url": item['children'][5]['url'], "children": [
                                     {"id": None, "uuid": item['children'][5]['children'][0]['uuid'],
                                      "name": item['children'][5]['children'][0]['name'],
                                      "url": item['children'][5]['children'][0]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][5]['children'][1]['uuid'],
                                      "name": item['children'][5]['children'][1]['name'],
                                      "url": item['children'][5]['children'][1]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][5]['children'][2]['uuid'],
                                      "name": item['children'][5]['children'][2]['name'],
                                      "url": item['children'][5]['children'][2]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][5]['children'][3]['uuid'],
                                      "name": item['children'][5]['children'][3]['name'],
                                      "url": item['children'][5]['children'][3]['url'], "children": None}
                                 ]},
                                 {"id": None, "uuid": item['children'][6]['uuid'],
                                  "name": item['children'][6]['name'],
                                  "url": item['children'][6]['url'], "children": [
                                     {"id": None, "uuid": item['children'][6]['children'][0]['uuid'],
                                      "name": item['children'][6]['children'][0]['name'],
                                      "url": item['children'][6]['children'][0]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][6]['children'][1]['uuid'],
                                      "name": item['children'][6]['children'][1]['name'],
                                      "url": item['children'][6]['children'][1]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][6]['children'][2]['uuid'],
                                      "name": item['children'][6]['children'][2]['name'],
                                      "url": item['children'][6]['children'][2]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][6]['children'][3]['uuid'],
                                      "name": item['children'][6]['children'][3]['name'],
                                      "url": item['children'][6]['children'][3]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][6]['children'][4]['uuid'],
                                      "name": item['children'][6]['children'][4]['name'],
                                      "url": item['children'][6]['children'][4]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][6]['children'][5]['uuid'],
                                      "name": item['children'][6]['children'][5]['name'],
                                      "url": item['children'][6]['children'][5]['url'], "children": None},
                                     {"id": None, "uuid": item['children'][6]['children'][6]['uuid'],
                                      "name": item['children'][6]['children'][6]['name'],
                                      "url": item['children'][6]['children'][6]['url'], "children": None}
                                 ]},

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
                                    insert into sweet.xx_store_product_category values(
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
                                        ',' + str(cat1_id) + str(cat2_id) + ',',
                                        str(cat2_id),
                                        cat3_data['name'],
                                        cat3_data['url'],
                                        cat3_data['uuid'],
                                    ))
        
                                print('三级分类插入成功!')


if __name__ == "__main__":
    t = TransferGoodsProducts(db='AlexandermcqueenCrawler')
    t.run()
