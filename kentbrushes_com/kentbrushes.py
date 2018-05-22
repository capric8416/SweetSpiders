# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import hashlib
import inspect
import json
import logging
from urllib.parse import urlparse, parse_qsl

import redis
import requests
import urllib3
from fire import Fire
from pymongo import *
from pyquery import PyQuery
import time

urllib3.disable_warnings()


class EttingerCrawler(object):
    """

    """

    def __init__(self, timeout=10):
        # 爬虫名字与类名相同
        self.spider = self.__class__.__name__

        # 日志记录器
        self.logger = self.get_logger(name=self.spider)

        # 起始链接
        self.start_url = 'https://kentbrushes_com/'

        # 代理
        # self.proxyMeta = 'http://HUM073044244ZN3D:E4A60516DD135BCF@http-dyn.abuyun.com:9020'
        # self.proxies = {
        #     "http": self.proxyMeta,
        #     "https": self.proxyMeta,
        # }

        # 默认headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        }

        # requests配置
        self.session = requests.session()
        self.session.verify = False
        self.session.timeout = timeout

        '''
        # redis客服端
        self.redis = redis.from_url('redis://127.0.0.1:6379')
        # set: url去重
        self.key_duplicated = f'{self.spider}:duplicated'
        # list: 3级分类url
        self.key_category_urls = f'{self.spider}:category_urls'
        # list: 商品花色详情url
        self.key_product_urls = f'{self.spider}:product_urls'

        # mongo客户端
        self.mongo = MongoClient('127.0.0.1', 27017)
        '''

    def get_index(self):
        """首页爬虫"""
        '''
        self.logger.info(f'[RUN] spider: {self.spider}.{inspect.currentframe().f_code.co_name}')

        resp = self.request(url=self.start_url, headers=self.headers)
        for info in self.parse_index(resp=resp):
            self.push_category_info(info)
        '''
        resp = self.session.get(url=self.start_url, headers=self.headers)
        self.parse_index(resp=resp)


    def parse_index(self, resp):
        """首页解析器"""
        if not resp:
            return
        pq = PyQuery(resp.text)
        cat1_node = pq('.wrapper .clearfix .main-menu .has-child')
        for cat1 in cat1_node.items():
            pass


    def get_product_list(self):
        self.logger.info(f'[RUN] spider: {self.spider}.{inspect.currentframe().f_code.co_name}')

        while True:
            info = self.pop_category_info()
            self._get_product_list(*json.loads(info))

    def _get_product_list(self, url, headers, categories):
        """列表页面爬虫"""

        page, params = 1, None
        while True:
            resp = self.request(url=url, headers=headers, params=params)
            time.sleep(5)
            pq = PyQuery(resp.text)

            for info in self.parse_product_list(pq=pq, resp=resp, headers=headers, categories=categories):
                self.push_product_info(info)

            if not pq('.container .col-sm-2 a').text().strip():
                break

            page += 1
            params = {'page': page}

    def parse_product_list(self, pq, resp, headers, categories):
        """列表页解析器"""
        if not resp:
            return
        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        for product_card in pq('.category .container .category__grid .product-card').items():
            product_id = product_card('.product-color-swatches a:eq(0)').attr('href').strip('/').split('/')[-2]
            for url in [
                self.full_it(resp_url=resp.url, path=a.attr('href'))
                for a in product_card('.product-color-swatches a').items()
            ]:
                yield url, headers, product_id, categories

    def get_product_detail(self):
        self.logger.info(f'[RUN] spider: {self.spider}.{inspect.currentframe().f_code.co_name}')

        while True:
            info = self.pop_product_info()
            info = self._get_product_detail(*json.loads(info))
            self.push_product_detail(info=info)

    def _get_product_detail(self, url, headers, product_id, categories):
        """详情页爬虫"""

        resp = self.request(url=url, headers=headers)
        time.sleep(5)
        return self.parse_product_detail(resp=resp, url=url, product_id=product_id, categories=categories)

    def parse_product_detail(self, resp, url, product_id, categories):
        """详情页解析器"""

        _ = self
        if not resp:
            return
        pq = PyQuery(resp.text)

        images = []
        thumbnails = []

        title = pq('.product-full__title .spaced-letters-sm')
        style = title('span:eq(0)').text()
        name = title('span:eq(1)').text()
        price = pq('.product-full__price .attribute-price').text()
        color = pq('.product-full__color p').text()
        item_code = pq('.product-full__item-code .ezstring-field').text()
        description = pq('.product-full__description .ezxmltext-field p').text()

        big_picture_node = pq('.gallery .carousel .item picture')
        for big_picture_url in big_picture_node.items():
            big_picture_link = big_picture_url('img').attr('src')
            images.append(big_picture_link)

        small_picture_node = pq('.carousel .carousel-indicators li')
        for small_picture in small_picture_node.items():
            small_picture_link = small_picture('img').attr('src')
            thumbnails.append(small_picture_link)

        return {
            'url': url, 'product_id': product_id, 'categories': categories,
            'title': title.text(), 'style': style, 'name': name, 'price': price,
            'color': color, 'item_code': item_code, 'description': description,
            'thumbnails': thumbnails, 'images': images
            }

    def request(self, method='get', **kwargs):
        try:
            url = kwargs['url']
            resp = getattr(self.session, method)(**kwargs)
            self.logger.info(f'[{resp.status_code} {resp.reason}] {method.upper()}: {url}')
            return resp
        except Exception as e:
            self.logger.warning(e)
            time.sleep(1)
            return None

    def get_logger(self, name, level='INFO'):
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

    def push_category_info(self, *info):
        """
        添加一个或者多个三级分类信息
        :param info: tuple, ((url, headers, categories),)
        :return: None
        """

        self._push_info(self.key_category_urls, *info)

    def push_product_info(self, *info):
        """
        添加一个或者多个商品花色详情信息
        :param info: tuple, ((url, headers, product_id, categories),)
        :return: None
        """

        self._push_info(self.key_product_urls, *info)

    def pop_category_info(self):
        """获取一个三级分类链接，如果没有，则一直等待"""

        info = self.redis.blpop(self.key_category_urls)[-1]
        return info.decode() if info else None

    def pop_product_info(self):
        """获取一个商品花色详情链接，如果没有，则一直等待"""

        info = self.redis.blpop(self.key_product_urls)[-1]
        return info.decode() if info else None

    def push_product_detail(self, info):
        """
        商品详情信息存储到MongoDB
        :param info: dict, 商品详情
        :return: None
        """

        self.mongo[self.spider]['products'].insert_one(info)

    def _push_info(self, name, *info):
        """
        添加url到对应的redis list
        :param name: str, redis key
        :param info: tuple, 链接及信息
        :return: None
        """

        for item in info:
            self._parse_info(name=name, item=item)

    def _parse_info(self, name, item):
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
            self.logger.info(f'[PUSH]: {url}')
            self.redis.rpush(name, json.dumps(item))
        else:
            self.logger.info(f'[SKIP]: {url}')

    def full_it(self, resp_url, path):
        _ = self

        if not path:
            return ''

        p = urlparse(resp_url)
        if '://' in path:
            return path
        if path.startswith('//'):
            return f'{p.scheme}:{path}'
        return f'{p.scheme}://{p.netloc}{path}'


if __name__ == '__main__':
    Fire(EttingerCrawler)
