# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import hashlib
import json
import time
from urllib.parse import urlparse, parse_qsl
import requests
import urllib3
from pyquery import PyQuery

urllib3.disable_warnings()


class KikoCrawler(object):
    """

    """

    def __init__(self, timeout=10):
        # 爬虫名字与类名相同
        self.spider = self.__class__.__name__

        # 起始链接
        self.start_url = 'https://www.kikocosmetics.com/en-gb/'

        # 商品店铺
        self.store = "KIKO_Milano"

        # 商品品牌
        self.brand = "KIKO_Milano"

        # 店铺ID
        self.store_id = 412

        # 货币ID
        self.coin_id = 1

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

    def get_index(self):
        """首页爬虫"""
        print('正在爬取首页', self.start_url)
        resp = self.session.get(url=self.start_url, headers=self.headers)
        self.parse_index(resp=resp)

    def parse_index(self, resp):
        """首页解析器"""
        if not resp:
            return
        headers = copy.copy(self.headers)
        headers['referer'] = resp.url
        pq = PyQuery(resp.text)
        url_categories = []
        node = pq('.nav .nav1 .nav1-item .nav1-link')
        for top_category in node.items():
            top_category_name = top_category.text()
            if top_category_name not in ('MakeUp' or 'Skin Care' or 'Accessories'):
                continue
            child_category = pq('.nav1-item .nav2-wrapper .nav2 .nav3 .nav3-item .nav3-link')
            for child in child_category.items():
                child_name = child('a').text()
                child_url = child.attr('href')
                categories = (child_name, top_category)
                url_categories.append(child_url)

            return url_categories, headers, categories
            pass




    def get_product_list(self, url_categories, headers, categories):
        detail_urls = []
        for list_url in url_categories:
            resp = self.session.get(url=list_url, headers=headers)


        pass






    def full_it(self, resp_url, path):
        _ = self

        if not path:
            return ''

        p = urlparse(resp_url)
        if '#' in path:
            return ''
        if '://' in path:
            return path
        if path.startswith('//'):
            return f'{p.scheme}:{path}'
        return f'{p.scheme}://{p.netloc}{path}'


if __name__ == '__main__':
    # Fire(KikkiCrawler)
    k = KikoCrawler()
    k.get_index()
    # k._get_product_list()


