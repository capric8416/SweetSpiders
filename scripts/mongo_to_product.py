# -*- coding: utf-8 -*-
# !/usr/bin/env python

import json

import pymongo
import pymysql


# --------------------------数据库启动函数------------------------------
def start_mysql():
    conn = pymysql.connect(
        host='59.110.155.75',
        port=3306,
        user='root',
        passwd='Dana1234!',
        db='sweet',
        charset='utf8mb4')
    cur = conn.cursor()
    myConn_list = [conn, cur]
    return myConn_list


# --------------------------关闭数据库--------------------------------


def close_pymysql(cur, conn):
    cur.close()
    conn.commit()
    conn.close()


if __name__ == "__main__":
    client = pymongo.MongoClient('localhost', 27017)
    db = client['CrabtreeCrawler']
    collection = db['products']

    myConn_list = start_mysql()
    cur = myConn_list[1]
    conn = myConn_list[0]

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
            '541',
            %s,
            null,
            '1',
            null,
            '270'
        );
    '''

    for item in collection.find({"categories": [
        ["Travel", "旅行", "http://www.crabtree-evelyn.com/uk/en/shop-by-category/travel/"],
        ["Hair", "头发", "http://www.crabtree-evelyn.com/uk/en/travel/hair/"]]}
    ):
        try:
            cur.execute(sql, (
                item['product_id'],
                item['categories'][0][0],
                '<p>' + item['introduction'] + '</p>',
                json.dumps(item['images']),
                item['name'],
                item['brand'],
                item['url'],
            ))
            print('保存成功!')
        except Exception as e:
            print(e)

    close_pymysql(cur, conn)
