# -*- coding: utf-8 -*-
# !/usr/bin/env python
import base64
import copy
import hashlib
import json
import time
from urllib.parse import urlparse, parse_qsl

import execjs
import redis
import requests
import urllib3
from pymongo import *
from pyquery import PyQuery

urllib3.disable_warnings()


class KikkiKCrawler(object):
    """

    """

    def __init__(self, timeout=10):
        # 爬虫名字与类名相同
        self.spider = self.__class__.__name__

        # 日志记录器
        # self.logger = self.get_logger(name=self.spider)

        # 起始链接
        self.start_url = 'https://www.kikki-k.com/'

        # 商品店铺
        self.store = "kikki-k"

        # 商品品牌
        self.brand = "kikki-k"

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

        # redis客服端
        self.redis = redis.from_url('redis://127.0.0.1:6379')
        # set: url去重
        self.key_duplicated = f'{self.spider}:duplicated'
        # list: 2级分类url
        self.key_category_urls = f'{self.spider}:category_urls'
        # list: 商品花色详情url
        self.key_product_urls = f'{self.spider}:product_urls'

        # mongo客户端
        self.mongo = MongoClient('127.0.0.1', 27017)

    def get_index(self):
        """首页爬虫"""
        print('正在爬取首页', self.start_url)
        resp = self.session.get(url=self.start_url, headers=self.headers)
        return self.parse_index(resp=resp)

    def parse_index(self, resp):
        """首页解析器"""
        if not resp:
            return

        headers = copy.copy(self.headers)
        headers['referer'] = resp.url
        pq = PyQuery(resp.text)
        url_categories = []
        node = pq('#nav .nav-item .level-top')
        for span in node.items():
            top_category = span.text().strip()
            if top_category == 'Shop By':
                continue
            elif top_category == ('Diaries & Calendars' or 'Notebooks & Journals' or 'Stationery' or 'Bags & Travel' or 'Organising' or 'Wedding'):
                child_category_node = pq('.menu-mobile-desktop ul.nav-submenu')
                for child in child_category_node.items():
                    child_category = [a.text().strip() for a in child('a').items()]
                    child_url = [a.attr('href') for a in child('a').items()]
                    url_categories.append(zip(child_category, child_url))

            # elif top_category == ('Notebooks & Journals' or 'Stationery' or 'Bags & Travel' or 'Organising' or 'Wedding'):
            #     child_category_node = pq('.nav-panel--dropdown .nav-panel-inner .nav-block--center .nav-item')
            #     for child in child_category_node.items():
            #         child_category = [span.text() for span in child('a').items()]
            #         child_url = [a.attr('href') for a in child('a').items()]
            elif top_category == 'Home':
                break

                pass

        '''
        node = pq('#header-nav .nav-item')
        for nav_item in node.items():
            top_category = nav_item('a.level-top span').text().strip()
            if top_category == 'Diaries & Calendars':
                start = True
            elif top_category == 'Wedding':
                end = True

            if start:
                for a in nav_item('.nav-submenu .nav-item a').items():
                    child_category = a.text().strip()
                    if child_category in ('All Diaries & Calendars' or 'All Planners & Accessories'):
                        continue
                    # url_categories.append((a.attr('href'), (top_category, child_category)))
                    url_categories.append(a.attr('href'))
            if end:
                break
        '''
        return url_categories

    def get_product_list(self):
        url_categories = self.get_index()
        self._get_product_list(url_categories=url_categories)

    def _get_product_list(self, url_categories):
        detail_urls = []
        for category_url in url_categories:
            resp = self.session.get(url=category_url, headers=self.headers)
            print('正在爬取列表页', category_url)
            time.sleep(2)
            pq = PyQuery(resp.text)
            category_node = pq('.category-products .product-image-wrapper')
            for div in category_node.items():
                detail_url = div('.product-image').attr('href')
                detail_urls.append(detail_url)
            script = pq("script:contains('_ajaxCatalog')").text().strip()
            script = script.partition('AWAjaxCatalog')[-1].strip().strip('();')
            script = script.replace('buttonType', '"scroll"')
            res = execjs.eval('(function(){ var value=' + script + ';return value; })()')
            params = res.get('params')
            params['p'] = res.get('next_page')
            count = int(params['p'])
            while True:
                params['p'] = count
                next_url = res.get('next_url').format('').format(page=base64.b64encode(json.dumps(params).encode()).decode())
                resp = self.session.get(url=next_url, headers=self.headers)
                pq = PyQuery(resp.text)
                node = pq('a')
                for a in node.items():
                    detail_url = self.start_url + a.attr('href').split('/')[3].strip('\\"')
                    detail_urls.append(detail_url)
                count += 1
                params['p'] = count
                if len(node) < 32:
                    break

        detail_urls = set(detail_urls)
        print(detail_urls)



    def get_product_detail(self):
        while True:
            info = self.pop_product_info()
            info = self._get_product_detail(*json.loads(info))
            self.push_product_detail(info=info)

    def _get_product_detail(self, detail_url, headers, categories):
        resp = self.session.get(url=detail_url, headers=headers)
        print('正在爬取详情页', detail_url)
        time.sleep(3)
        if not resp:
            return
        pq = PyQuery(resp.text)
        # 商品图片
        b_img_url = self.full_it(resp_url=resp.url, path=pq('.product-left-box #productImages .slides a').attr('href'))

        # 商品源地址
        product_source_url = detail_url

        # 商品名
        name = pq('.product-right-box .product-name').text().strip()

        # 原价
        was_price = pq('.product-right-box .price-box .priceWas').text()
        # 现价
        now_price = pq('.product-right-box .price-box .priceNow').text()
        if not (was_price and now_price):
            now_price = pq('.product-right-box .price-box .price').text()

        # 商品详情描述
        description = pq('.product-right-box .product-desc').text().strip()

        # 商品ID
        product_id = urlparse(product_source_url).path[:-5]

        # 商品尺寸
        size_list = []
        size_node = pq('#ctl00_PageContentPlaceHolder_OptionsList [selected!="selected"]')
        for size in size_node.items():
            size = size.text().strip()
            size_list.append(size)

        info = {'source': product_source_url, 'categories': categories, 'img': b_img_url, 'was_price': was_price,
                'now_price': now_price, 'description': description, 'size': size_list, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id, 'product_id': product_id,
                'name': name,
                }

        return info

    def push_category_info(self, *info):
        """
        添加一个或者多个二级分类信息
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
        """获取一个二级分类链接，如果没有，则一直等待"""

        info = self.redis.blpop(self.key_category_urls)[-1]
        return json.loads(info.decode()) if info else None

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
            print('集合添加{}'.format(url))
            self.redis.rpush(name, json.dumps(item))
            print('列表添加{}'.format(url))
        else:
            print('该链接{}已爬取过'.format(url))

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
    # Fire(KikkiCrawler
    k = KikkiKCrawler()
    url_categories = k.get_index()
    # k.get_product_list()
