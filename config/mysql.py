# -*- coding: utf-8 -*-
# !/usr/bin/env python

import pymysql

DB_SWEET_SPIDERS = 'sweet_spiders'
TABLE_PID = 'pid'

MYSQL_CONF = {
    'host': '127.0.0.1',
    'port': 3306,
    'db': DB_SWEET_SPIDERS,
    'user': 'root',
    'password': 'mysql',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
