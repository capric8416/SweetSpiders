# -*- coding: utf-8 -*-
# !/usr/bin/env python
import functools
import hashlib
import inspect
import json
import logging
import random
import time
from urllib.parse import urlparse, parse_qsl

import redis
import requests
import urllib3
from pymongo import *

urllib3.disable_warnings()


class IndexListDetailCrawler:
    """
    首页-列表页-详情页爬虫框架
    """

    # 首页链接
    INDEX_URL = ''

    # Request conf
    TIMEOUT = 10
    WAIT = None
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    }

    # Redis url
    REDIS_URL = 'redis://127.0.0.1:6379'

    # 去重key
    DUPLICATED_POSTFIX = 'duplicated'

    # MongoDB url
    MONGODB_URL = 'mongodb://localhost:27017'

    # MongoDB collection
    MONGODB_COLLECTION = 'products'

    def __init__(self):
        # 爬虫名字与类名相同
        self.spider = self.__class__.__name__

        # 日志记录器
        self.logger = self._get_logger(name=self.spider)

        # 首页链接
        self.index_url = self.INDEX_URL

        # Headers
        self.headers = self.HEADERS

        self.timeout = self.TIMEOUT

        # redis客服端
        self.redis = redis.from_url(self.REDIS_URL)

        # set: url去重
        self.key_duplicated = f'{self.spider}:{self.DUPLICATED_POSTFIX}'

        # MongoDB客户端
        self.mongo = MongoClient(self.MONGODB_URL)

        # 集合名
        self.collection = self.MONGODB_COLLECTION

        # 爬取等待
        self.wait = self.WAIT

    def get_index(self):
        """首页爬虫"""

        self.logger.info(f'[RUN] {self.spider}.{inspect.currentframe().f_code.co_name}')

        while True:
            try:
                resp = self._request(url=self.index_url, headers=self.headers)
            except Exception as e:
                _ = e
                self.logger.warning(f'[RETRY] {e}, {self.index_url}')
            else:
                for info in self._parse_index(resp=resp):
                    self.push_category_info(info)

                break

    def _parse_index(self, resp):
        """
        首页解析器，提取分类信息
        yield url, headers, cookies, meta
        """

        raise NotImplementedError

    def get_product_list(self):
        self.logger.info(f'[RUN] {self.spider}.{inspect.currentframe().f_code.co_name}')

        while True:
            info = self.pop_category_info()[-1]
            try:
                self._get_product_list(*json.loads(info.decode()))
            except Exception as e:
                print(info, e)
                raise e

    def _get_product_list(self, url, headers, cookies, meta):
        """
        列表页面爬虫，实现翻页请求，拿到详情链接
        """

        raise NotImplementedError

    def _parse_product_list(self, pq, resp, headers, meta):
        """
        列表页解析器，提取详情链接
        yield url, headers, meta
        """

        raise NotImplementedError

    def get_product_detail(self):
        self.logger.info(f'[RUN] {self.spider}.{inspect.currentframe().f_code.co_name}')

        while True:
            info = self.pop_product_info()[-1]
            info = self._get_product_detail(*json.loads(info.decode()))
            self._push_product_detail(info=info)

    def _get_product_detail(self, url, headers, cookies, meta):
        """详情页爬虫"""

        resp = self._request(url=url, headers=headers, cookies=cookies, meta=meta, rollback=self.push_product_info)
        if not resp:
            return

        return self._parse_product_detail(url=url, resp=resp, meta=meta)

    def _parse_product_detail(self, url, resp, meta):
        """
        详情页解析器，提取详情页信息
        """

        raise NotImplementedError

    def _request(self, method='get', rollback=None, **kwargs):
        self._sleep()

        kwargs = dict(kwargs)
        kwargs.update({'verify': False, 'timeout': self.timeout})

        url = kwargs['url']
        headers = kwargs['headers']

        # 附加信息
        meta = kwargs.pop('meta', {})

        try:
            resp = requests.request(method=method, **kwargs)
            self.logger.info(f'[{resp.status_code} {resp.reason}] {method.upper()}: {url}')
            return resp
        except Exception as e:
            # 如果提供了异常回滚方法，则回滚，否则抛出异常
            if not rollback:
                raise e
            self._rollback(func=rollback, url=url, headers=headers, cookies=kwargs.get('cookies', {}), meta=meta)
            self.logger.warning(e)

    def _rollback(self, func, url, headers, cookies, meta):
        """异常爬取回滚"""

        _ = self
        func((url, headers, cookies, meta), force=True)

    def _get_logger(self, name, level='INFO'):
        _ = self

        level = getattr(logging, level)

        logger = logging.getLogger(name=name)
        logger.setLevel(level)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s'))
        logger.addHandler(stream_handler)

        return logger

    def __getattribute__(self, item):
        """
        根据函数名生成push, pop方法
        :param item: 函数名
        :return: function
        """

        if item.endswith('_info'):
            prefix, _, name = item.partition('_')
            name, _, postfix = name.rpartition('_')
            key = f'{self.spider}:{name}_{postfix}'
            if key:
                if item.startswith('pop_'):
                    return functools.partial(self.redis.blpop, key)
                elif item.startswith('push_'):
                    return functools.partial(getattr(self, f'_{prefix}_{postfix}'), key)

        return super().__getattribute__(item)

    def _push_product_detail(self, info):
        """
        商品详情信息存储到MongoDB
        :param info: dict, 商品详情
        :return: None
        """
        if not info:
            return

        info['created'] = time.time()
        self.mongo[self.spider][self.collection].insert_one(info)

    def _push_info(self, name, *info, force=False):
        """
        添加url到对应的redis list
        :param name: str, redis key
        :param info: tuple, 链接及信息
        :param force, bool, 跳过去重检查
        :return: None
        """

        for item in info:
            self._parse_info(name=name, item=item, force=force)

    def _parse_info(self, name, item, force=False):
        if force:
            return self.redis.rpush(name, json.dumps(item))

        # 链接
        url = item[0]
        # 解析
        parsed = urlparse(url)
        # 查询参数排序
        query = json.dumps(list(sorted(parse_qsl(parsed.query), key=lambda x: x[0])))
        # 拼接处理后的url
        text = '\n'.join([parsed.scheme, parsed.netloc, parsed.path, query])
        # 计算sha1值
        sha1 = hashlib.sha1(text.encode()).hexdigest()
        # 如果不在已经爬取过的set里面，就将其放到list里面
        if self.redis.sadd(self.key_duplicated, sha1):
            self.logger.info(f'[PUSH] {url}')
            self.redis.rpush(name, json.dumps(item))
        else:
            self.logger.info(f'[SKIP] {url}')

    def _full_url(self, url_from, path):
        """补全链接"""

        _ = self

        if not path or path == '#':
            return ''

        p = urlparse(url_from)
        if '://' in path:
            return path
        elif path.startswith('//'):
            return f'{p.scheme}:{path}'
        elif path.startswith('/'):
            return f'{p.scheme}://{p.netloc}{path}'
        else:
            return f'{p.scheme}://{p.netloc}{p.path.rpartition("/")[0]}/{path}'

    def _sleep(self):
        """爬取等待"""

        # 如果配置的是准确的秒数，则等待指定秒数
        if isinstance(self.wait, (int, float)):
            seconds = self.wait
        # 如果配置的是区间，则等待指定区间内的随机数
        elif isinstance(self.wait, (tuple, list)):
            seconds = random.randrange(*self.wait[:2])
        else:
            seconds = 0

        self.logger.info(f'[SLEEP] {seconds}s')

        time.sleep(seconds)

    def monitor(self):
        wait = self.wait[-1] if isinstance(self.wait, (tuple, list)) else self.wait

        names = []

        def scan_names():
            nonlocal names
            for n in self.redis.keys(f'{self.spider}:*'):
                n = n.decode()
                if n not in names:
                    names.append(n)

        def redis_count():
            scan_names()

            msgs = []
            for name in names:
                t = self.redis.type(name).decode()

                length = 'n/a'
                if t == 'list':
                    length = self.redis.llen(name)
                elif t == 'set':
                    length = self.redis.scard(name)
                elif t == 'hash':
                    length = self.redis.hlen(name)

                msgs.append(f'\t{length}: {name}')

            return f'===== Redis ==== \n' + '\n'.join(msgs)

        def mongo_count():
            return f'===== MongoDB =====\n' + \
                   f'\t{self.mongo[self.spider][self.collection].count()}: {self.spider}.{self.collection}'

        while True:
            self.logger.info('\n'.join(['', redis_count(), mongo_count(), '']))
            time.sleep(wait)

    def reset(self):
        names = self.redis.keys(f'{self.spider}:*')
        if names:
            self.redis.delete(*names)

        self.mongo[self.spider][self.collection].remove({})
