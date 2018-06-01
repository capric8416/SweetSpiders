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
    db = client['EttingerCrawler']
    collection = db['products']

    myConn_list = start_mysql()
    cur = myConn_list[1]
    conn = myConn_list[0]

    sqli = "insert into xx_goods values(0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    for temple in collection.find():
        try:
            cur.execute(sqli, (
                temple['url'],
                json.dumps(temple['categories']),
                json.dumps(temple['img']),
                temple['was_price'],
                temple['now_price'],
                temple['description'],
                json.dumps(temple['size']),
                temple['store'],
                temple['brand'],
                temple['store_id'],
                temple['coin_id'],
                temple['product_id'],
                temple['name'],
                temple['created']
            ))

            print('保存成功!')
        except Exception as e:
                print(e)

    close_pymysql(cur, conn)
