# -*- coding: utf-8 -*-
# !/usr/bin/env python
import json

import pymongo
import pymysql


# --------------------------数据库启动函数------------------------------
def start_mysql():
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        passwd='mysql',
        db='sw',
        charset='gbk')
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
    db = client['KjslaundryCrawler']
    collection = db['products']

    myConn_list = start_mysql()
    cur = myConn_list[1]
    conn = myConn_list[0]

    sqli = "insert into kjslaundry values(0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    for temple in collection.find():
        try:
            cur.execute(sqli, (
                temple['source'].encode('utf8'),
                json.dumps(temple['categories']).encode('utf8'),
                json.dumps(temple['img']).encode('utf8'),
                temple['was_price'].encode('utf8'),
                temple['now_price'].encode('utf8'),
                temple['description'].encode('utf8'),
                json.dumps(temple['size']).encode('utf8'),
                temple['store'].encode('utf8'),
                temple['brand'].encode('utf8'),
                json.dumps(temple['store_id']).encode('utf8'),
                json.dumps(temple['coin_id']).encode('utf8'),
                temple['product_id'].encode('utf8'),
                temple['name'].encode('utf8'),
                temple['update'].encode('utf8')
            ))

            print('保存成功!')
        except Exception as e:
            print(e)

    close_pymysql(cur, conn)
