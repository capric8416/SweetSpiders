# -*- coding: utf-8 -*-
# !/usr/bin/env python

import hashlib
import inspect
import string

from SweetSpiders.manager import Manager
from SweetSpiders.spiders import *
from SweetSpiders.tasks.app import app


def get_spider_tasks(queues, threads_conf=None, task_template=None):
    if not threads_conf:
        threads_conf = {'get_index': 1, 'get_product_list': 10, 'get_product_detail': 20}

    if not task_template:
        task_template = '''
            @app.task
            def {task_name}():
                return Manager.start(crawler='{crawler}', method='{method}', threads={threads})
        '''

    task_template = [line for line in task_template.split('\n') if line.strip()]
    start_pos = task_template[0].index('@')
    task_template = '\n'.join([line[start_pos:] for line in task_template])

    for n, c in copy.copy(globals()).items():
        if n[0] in string.ascii_uppercase and c != IndexListDetailCrawler and issubclass(c, IndexListDetailCrawler):
            for attr in dir(c):
                if attr.startswith('get_') and inspect.isfunction(getattr(c, attr)):
                    crawler = n
                    method = attr
                    threads = threads_conf[attr]

                    queue = int(hashlib.md5(n.encode()).hexdigest(), 16) % queues

                    task_name = f'{crawler.lower()}_{method.lower()}'

                    g = copy.copy(globals())
                    code = task_template.format(task_name=task_name, crawler=crawler, method=method, threads=threads)
                    exec(code, g)

                    yield queue, g[task_name]


if __name__ == '__main__':
    _ = app
    _ = Manager
    for t in get_spider_tasks(queues=4):
        print(t)
