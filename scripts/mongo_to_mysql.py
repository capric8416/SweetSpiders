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
    db = client['LasciviousCrawler']
    collection = db['products']

    myConn_list = start_mysql()
    cur = myConn_list[1]
    conn = myConn_list[0]

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
            0,
            null,
            null,
            '0',
            '3225',
            '36',
            '0.000000',
            '36'
        );
    '''

    for item in collection.find():
        try:
            cur.execute(sql, (
                item['brand'],
                item['name'],
                item['images'][0],
                item['description'],
                item['description'],
                item['now_price'].lstrip('£'),
                item['categories'][1][0],
                item['now_price'].lstrip('£'),
                json.dumps([{"title": "null", "source": item['images'][0],
                             "large": item['images'][0] + '?x-oss-process=image/resize,m_lfit,w_800,h_800',
                             "medium": item['images'][0] + '?x-oss-process=image/resize,m_lfit,w_400,h_400',
                             "thumbnail": item['images'][0] + '?x-oss-process=image/resize,m_lfit,w_200,h_200',
                             "order": "null"}, {"title": "null", "source": item['images'][1],
                                                "large": item['images'][1] + '?x-oss-process=image/resize,m_lfit,w_800,h_800',
                                                "medium": item['images'][1] + '?x-oss-process=image/resize,m_lfit,w_400,h_400',
                                                "thumbnail": item['images'][1] + '?x-oss-process=image/resize,m_lfit,w_200,h_200',
                                                "order": "null"}]),
                item['url'],
            ))

            print('保存成功!')
        except Exception as e:
            print(e)

    close_pymysql(cur, conn)
