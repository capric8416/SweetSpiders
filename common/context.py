# -*- coding: utf-8 -*-
# !/usr/bin/env python

import os
import sqlite3
import time
from datetime import datetime

from SweetSpiders.config import SQLITE_PID, TABLE_PID


class RegisterTask:
    def __init__(self, class_name, method_name):
        self.class_name = class_name
        self.method_name = method_name
        self.pid = os.getpid()

        self.table = TABLE_PID

        self.connection = sqlite3.connect(SQLITE_PID)
        self.connection.row_factory = self.dict_factory

    def __enter__(self):
        self.create_table()
        self.insert_into()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.drop_from()
        self.connection.close()

    def create_table(self):
        cursor = self.connection.cursor()
        cursor.execute(self.sql_create_table)
        cursor.execute(self.sql_create_index)
        self.connection.commit()

    def insert_into(self):
        cursor = self.connection.cursor()
        cursor.execute(self.sql_insert_into)
        self.connection.commit()

    def drop_from(self):
        cursor = self.connection.cursor()
        cursor.execute(self.sql_drop_from)
        self.connection.commit()

    def select_all(self):
        cursor = self.connection.cursor()
        cursor.execute(self.sql_select_all)
        self.connection.commit()

        results = cursor.fetchall()
        for item in results:
            item['running'] = f'{time.time() - item["created"]}s'
            item['created'] = datetime.fromtimestamp(item['created']).strftime('%Y-%m-%d %H:%M:%S.%f')

        return results

    def select_tasks(self, pid):
        cursor = self.connection.cursor()
        cursor.execute(self.sql_select_task(pid=pid))
        self.connection.commit()
        return [item['pid'] for item in cursor.fetchall()]

    @property
    def sql_create_table(self):
        return f'''
            create table if not exists {self.table} (
                pid int not null,
                class varchar(255) not null,
                method varchar(255) not null,
                created double not null
            )
        '''

    @property
    def sql_create_index(self):
        return f'''
            create unique index if not exists index_pid on {self.table}(pid)
        '''

    @property
    def sql_insert_into(self):
        return f'''
            insert into {self.table}
            (pid, class, method, created)
            values
            ({self.pid}, "{self.class_name}", "{self.method_name}", {time.time()})
        '''

    @property
    def sql_drop_from(self):
        return f'''
            delete from {self.table} where pid={self.pid}
        '''

    @property
    def sql_select_all(self):
        return f'''
            select * from {self.table}
        '''

    def sql_select_task(self, pid):
        return f'''
            select pid from {self.table} where pid in ({",".join(pid)})
        '''

    @staticmethod
    def dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
