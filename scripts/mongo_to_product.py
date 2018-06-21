# -*- coding: utf-8 -*-
# !/usr/bin/env python

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
    db = client['LasciviousCrawler']
    collection = db['products']

    myConn_list = start_mysql()
    cur = myConn_list[1]
    conn = myConn_list[0]

    # 将数据导入xx_spider_product表中

    sql = '''
        insert into sw.xx_spider_product values(
            '0',
            now(),
            now(),
            '46',
            %s,
            %s,
            '1',
            %s,
            %s,
            null,
            %s,
            %s,
            null,
            '923',
            %s,
            null,
            0,
            null,
            '442'
        );
    '''

    for item in collection.find():
        try:
            cur.execute(sql, (
                item['brand'],
                item['categories'][0][0],
                item['description'],
                item['images'][0],
                item['name'],
                item['brand'],
                item['url'],
            ))
            print(sql)
            print('保存成功!')
        except Exception as e:
            print(e)

    close_pymysql(cur, conn)
