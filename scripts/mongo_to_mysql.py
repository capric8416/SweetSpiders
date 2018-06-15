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

    sql = '''
        insert into sw.xx_goods values(
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
            null,
            '0',
            %s,
            %s,
            %s,
            '\0',
            '',
            '',
            '',
            '\0',
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
            '2018061012041',
            '[]',
            '0',
            '0',
            null,
            '0',
            now(),
            '0',
            now(),
            null,
            '442',
            '302',
            '923',
            null,
            null,
            null,
            %s,
            null,
            null,
            '',
            null,
            null,
            '0',
            '3225',
            '36',
            '0.000000'
        );
    '''

    for item in collection.find():
        try:
            cur.execute(sql, (
                item['brand'],
                item['images'][0],
                item['description'],
                item['description'],
                item['now_price'].lstrip('£'),
                item['categories'][1][0],
                item['now_price'].lstrip('£'),
                item['images'][0],
                item['url'],
            ))

            print('保存成功!')
        except Exception as e:
            print(e)

    close_pymysql(cur, conn)
