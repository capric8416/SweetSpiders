# -*- coding: utf-8 -*-
# !/usr/bin/env python
import base64
import copy
import hashlib
import json
import time
from urllib.parse import urlparse, parse_qsl

import execjs
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
        self.store_id = 1607

        # 货币ID
        self.coin_id = 4

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
        # list: 2级分类url
        self.key_category_urls = f'{self.spider}:category_urls'
        # list: 商品花色详情url
        self.key_product_urls = f'{self.spider}:product_urls'
        '''
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
        node = pq('#nav li.nav-2')
        top_category = node('a:eq(0) span').text().strip()
        child_node = node('.nav-panel--dropdown .menu-mobile-desktop .nav-submenu .classic')
        for child in child_node.items():
            child_category = child('a span').text()
            child_url = child('a').attr('href')
            categories = (top_category, child_category)
            url_categories.append((child_url, categories))
        node2 = pq('#nav li.nav-3')
        top2_category = node2('a:eq(0) span').text().strip()
        child2_node = node2('.nav-panel--dropdown .nav-block--center .nav-submenu--mega li')
        for child in child2_node.items():
            child2_category = child('a span').text().strip()
            child2_url = child('a').attr('href')
            categories2 = (top2_category, child2_category)
            url_categories.append((child2_url, categories2))
        node3 = pq('#nav li.nav-4')
        top3_category = node3('a:eq(0) span').text().strip()
        child3_node = node3('.nav-panel--dropdown .nav-block--center .nav-submenu--mega li')
        for child in child3_node.items():
            child3_category = child('a span').text().strip()
            child3_url = child('a').attr('href')
            categories3 = (top3_category, child3_category)
            url_categories.append((child3_url, categories3))
        node4 = pq('#nav li.nav-5')
        top4_category = node4('a:eq(0) span').text().strip()
        child4_node = node4('.nav-panel--dropdown .nav-block--center .nav-submenu--mega li')
        for child in child4_node.items():
            child4_category = child('a span').text().strip()
            child4_url = child('a').attr('href')
            categories4 = (top4_category, child4_category)
            url_categories.append((child4_url, categories4))
        node5 = pq('#nav li.nav-6')
        top5_category = node5('a:eq(0) span').text().strip()
        child5_node = node5('.nav-panel--dropdown .nav-block ul')
        for child in child5_node.items():
            for a in child('li a').items():
                child5_category = a('span').text().strip()
                child5_url = a.attr('href')
                categories5 = (top5_category, child5_category)
                url_categories.append((child5_url, categories5))
        node6 = pq('#nav li.nav-7')
        top6_category = node6('a:eq(0) span').text().strip()
        child6_node = node6('.nav-panel--dropdown .nav-block--center .nav-submenu--mega li')
        for child in child6_node.items():
            child6_category = child('a span').text().strip()
            child6_url = child('a').attr('href')
            categories6 = (top6_category, child6_category)
            url_categories.append((child6_url, categories6))
        return url_categories

    def get_product_list(self):
        url_categories = self.get_index()
        print(len(url_categories))
        return self._get_product_list(url_categories=url_categories)

    def _get_product_list(self, url_categories):
        detail_urls = []
        for category in url_categories:
            list_url, categories = category
            resp = self.session.get(url=list_url, headers=self.headers)
            print('正在爬取列表页', list_url)
            time.sleep(2)
            pq = PyQuery(resp.text)
            category_node = pq('.category-products .product-image-wrapper')
            for div in category_node.items():
                detail_url = div('.product-image').attr('href')
                detail_urls.append(detail_url)
            if len(category_node) < 16:
                continue
            script = pq("script:contains('_ajaxCatalog')").text().strip()
            if not script:
                continue

            script = script.partition('AWAjaxCatalog')[-1].strip().strip('();')
            script = script.replace('buttonType', '"scroll"')
            res = execjs.eval('(function(){ var value=' + script + ';return value; })()')
            if not res:
                continue
            params = res.get('params')
            params['p'] = res.get('next_page')
            count = int(params['p'])

            while True:
                params['p'] = count
                next_url = res.get('next_url').format('').format(
                    page=base64.b64encode(json.dumps(params).encode()).decode())
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

        detail_urls = list(set(detail_urls))
        print(len(detail_urls))
        return detail_urls

    def get_product_detail(self):
        detail_urls = self.get_product_list()
        self._get_product_detail(detail_urls=detail_urls)

    def _get_product_detail(self, detail_urls):
        for detail_url in detail_urls:
            resp = self.session.get(url=detail_url, headers=self.headers)
            print('正在爬取详情页', detail_url)
            time.sleep(2)
            if not resp:
                return
            pq = PyQuery(resp.text)
            # 商品图片
            imgs = []
            img_node = pq('.more-images .wrap-slider .slides li')
            for img in img_node.items():
                img_url = img('a').attr('href')
                imgs.append(img_url)

            # 商品源地址
            product_source_url = detail_url

            # 商品名
            name = pq('.product-shop .product-name h1').text().strip()

            # 原价
            was_price = pq('.product-type-data .price-box .old-price #old-price-8402').text().strip()
            # 现价
            now_price = pq('.product-type-data .price-box .special-price #product-price-8402').text().strip()
            if not (was_price and now_price):
                now_price = pq('.product-type-data .price-box #product-price-9500 .price').text().strip()

            # 商品特征描述
            p1 = pq('.tabs-panels .panel .std').text().strip()
            p2 = pq('.tabs-panels .panel:eq(0) p').text().strip()
            features = p1 + '\n' + p2

            # 商品介绍
            description = pq('.short-description').text().strip()

            # 商品ID
            product_id = urlparse(product_source_url).path[1:]

            # 商品尺寸
            size = ''

            info = {'source': product_source_url, 'img': imgs, 'was_price': was_price,
                    'now_price': now_price, 'features': features, 'description': description, 'size': size,
                    'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id,
                    'product_id': product_id, 'name': name,
                    }

            self.mongo[self.spider]['products'].insert_one(info)
            print('成功插入一条数据')

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
