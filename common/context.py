# -*- coding: utf-8 -*-
# !/usr/bin/env python

import os
import time
from datetime import datetime
from multiprocessing import Pool as ProcessPool, cpu_count
from multiprocessing.dummy import Pool as ThreadPool

import pymysql
from SweetSpiders.config import MYSQL_CONF, DB_SWEET_SPIDERS, TABLE_PID


class RegisterTask:
    def __init__(self, class_name, method_name, threads=1):
        self.class_name = class_name
        self.method_name = method_name
        self.threads = threads
        self.pid = os.getpid()

        self.db = DB_SWEET_SPIDERS
        self.table = TABLE_PID

        self.connection = pymysql.connect(**MYSQL_CONF)

    def __enter__(self):
        self.insert_into()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.drop_from()
        self.connection.close()

    def create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_create_table)
            self.connection.commit()

    def insert_into(self):
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_insert_into)
            self.connection.commit()

    def drop_from(self, pid=None):
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_drop_from(pid=pid))
            self.connection.commit()

    def select_all(self):
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_select_all)
            self.connection.commit()

            results = cursor.fetchall()
            for item in results:
                item['elapsed'] = f'{time.time() - item["created"]}s'
                item['created'] = datetime.fromtimestamp(item['created']).strftime('%Y-%m-%d %H:%M:%S.%f')

            return results

    def select_tasks(self, pid):
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_select_task(pid=pid))
            self.connection.commit()
            return [item['pid'] for item in cursor.fetchall()]

    @property
    def sql_create_table(self):
        return f'''
            create database if not exists {self.db} charset utf8mb4;
            
            create table if not exists {self.table} (
                pid int not null,
                class varchar(255) not null,
                method varchar(255) not null,
                threads int not null,
                created double not null
            );
            
            create unique index if not exists index_pid on {self.table}(pid)
        '''

    @property
    def sql_insert_into(self):
        return f'''
            insert into {self.table}
            (pid, class, method, threads, created)
            values
            ({self.pid}, "{self.class_name}", "{self.method_name}", {self.threads}, {time.time()})
        '''

    def sql_drop_from(self, pid=None):
        if not pid:
            pid = self.pid
        return f'''
            delete from {self.table} where pid={pid}
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


class _PoolSubmit:
    """进程|进程池 map"""

    def __init__(self, func, iterable, pool_type, concurrency, action):
        """
        初始化
        :param func: 要提交的函数
        :param iterable: list, 函数参数列表
        :param pool_type: ThreadPool|ProcessPool
        :param concurrency: 线程|进程数
        :param action: map|startmap
        """

        self.func = func
        self.iterable = iterable
        self.pool_type = pool_type
        self.concurrency = concurrency
        self.action = action
        self.pool = None

    def __enter__(self):
        self.pool = self.pool_type(processes=self.concurrency or (2 * cpu_count() // 3))
        return getattr(self.pool, self.action)(func=self.func, iterable=self.iterable)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.close()
        self.pool.join()


class ThreadPoolSubmit(_PoolSubmit):
    """提交任务到线程池运行"""

    def __init__(self, func, iterable, concurrency=None, action='map'):
        """初始化"""
        super(ThreadPoolSubmit, self).__init__(
            func=func, iterable=iterable, pool_type=ThreadPool, concurrency=concurrency, action=action)


class ProcessPoolSubmit(_PoolSubmit):
    """提交任务到进程池运行"""

    def __init__(self, func, iterable, concurrency=None, action='map'):
        """初始化"""
        super(ProcessPoolSubmit, self).__init__(
            func=func, iterable=iterable, pool_type=ProcessPool, concurrency=concurrency, action=action)
