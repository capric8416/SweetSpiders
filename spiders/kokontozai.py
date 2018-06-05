# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy


class KokontozaiCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.kokontozai.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(KokontozaiCrawler, self).__init__()

        # 商品店铺
        self.store = "Kokon to Zai"

        # 商品品牌
        self.brand = "Kokon to Zai"

        # 店铺ID
        self.store_id = 1120

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        node1 = pq('.container .main-navigation .top-navigation li.nav-1')
        top_category = node1('a').text().strip()
        url = node1('a').attr('href')
        categories = (top_category,)
        headers = copy.copy(self.headers)
        headers['Referer'] = resp.url
        yield url, headers, resp.cookies.get_dict(), {'categories': categories}
        node2 = pq('.container .main-navigation .top-navigation li.nav-2')
        top_category = node2('a.level-top').text().strip()
        child_node = node2('.menu-wrapper .level1 li')
        for child in child_node.items():
            child_category = child('a').text().strip()
            url = child('a').attr('href')
            categories = (top_category, child_category)
            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url
            yield url, headers, resp.cookies.get_dict(), {'categories': categories}
        node3 = pq('.container .main-navigation .top-navigation li.nav-3')
        top_category = node3('a.level-top').text().strip()
        child_node = node3('.menu-wrapper .level1 li')
        for child in child_node.items():
            child_category = child('a').text().strip()
            url = child('a').attr('href')
            categories = (top_category, child_category)
            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url
            yield url, headers, resp.cookies.get_dict(), {'categories': categories}

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        raise NotImplementedError

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        raise NotImplementedError

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        raise NotImplementedError
