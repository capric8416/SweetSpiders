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


class KjslaundryCrawler(object):
    """

    """

    def __init__(self, timeout=10):
        # 爬虫名字与类名相同
        # self.spider = self.__class__.__name__

        # 日志记录器
        # self.logger = self.get_logger(name=self.spider)

        # 起始链接
        self.start_url = 'http://www.kjslaundry.com/'

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
        # self.session.verify = False
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

        # self.logger.info(f'[RUN] spider: {self.spider}.{inspect.currentframe().f_code.co_name}')
        resp = self.session.get(url=self.start_url, headers=self.headers)
        return self.parse_index(resp=resp)
        # resp = self.request(url=self.start_url, headers=self.headers)
        # for info in self.parse_index(resp=resp):
        #     self.push_category_info(info)

    def parse_index(self, resp):
        """首页解析器"""
        if not resp:
            return
        c_urls = []
        pq = PyQuery(resp.text)
        for category in pq('#mainNav-menu .mainNav-dropdown li').items():
            c_name = category('a').text()
            c_url = self.full_it(resp_url=resp.url, path=category('a').attr('href'))
            c_urls.append(c_url)

        return c_urls


    def get_product_list(self):
        c_urls = self.get_index()
        detail_urls, m_img_urls = [], []
        for list_url in c_urls:
            count = 1
            list_url = 'http://www.kjslaundry.com/womens/end-of-line-sale/'
            list_urls = list_url + 'page-{}.aspx'.format(count)
            while True:
                resp = self.session.get(url=list_urls, headers=self.headers)
                if not resp:
                    break
                pq = PyQuery(resp.text)
                for img in pq('#ctl00_PageContentPlaceHolder_PTagBorder .list-item').items():
                    detail_url = self.full_it(resp_url=resp.url, path=img('a').attr('href'))
                    m_img_url = self.full_it(resp_url=resp.url, path=img('img:eq(1)').attr('src'))
                    detail_urls.append(detail_url)
                    m_img_urls.append(m_img_url)

                    pass
                count += 1
        return detail_urls,m_img_urls

    def get_product_detail(self):
        # detail_urls, m_img_urls = self.get_product_list()
        b_img_urls, s_img_urls = [], []
        # for detail_url in detail_urls:
        detail_url = 'http://www.kjslaundry.com/sessun/charles-harper-dress-blue-celeste.aspx'
        resp = self.session.get(url=detail_url, headers=self.headers)
        if not resp:
            return
        pq = PyQuery(resp.text)
        b_img_url = self.full_it(resp_url=resp.url, path=pq('.product-left-box #productImages .slides a').attr('href'))
        b_img_urls.append(b_img_url)
        for s_img in pq('.productImages .slideThumbs').items():
            s_img_url = self.full_it(resp_url=resp.url, path=s_img('a').attr('src'))
            s_img_urls.append(s_img_url)

        # 品牌名
        brand = pq('.product-right-box .product-brand').text()

        # 商品名
        name = pq('.product-right-box .product-name').text().strip()

        # 原价
        was_price = pq('.product-right-box .price-box .priceWas').text()
        if not was_price:
            was_price = ''
            now_price = pq('.product-right-box .price-box .price')

        # 现价
        now_price = pq('.product-right-box .price-box .priceNow').text()

        # 商品详情描述
        description = pq('.product-right-box .product-desc').text().strip()

        pass





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
    kj = KjslaundryCrawler()
    # kj.get_index()
    # kj.get_product_list()
    kj.get_product_detail()
