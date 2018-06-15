# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy
from urllib.parse import urlparse


class HarrodsCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.harrods.com/en-gb'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(HarrodsCrawler, self).__init__()

        # 商品店铺
        self.store = "Harrods"

        # 商品品牌
        self.brand = "Harrods"

        # 店铺ID
        self.store_id = 1606

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 445

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('.nav .nav_container .nav_item')
        for cat1_node in top.items():
            cat1_name = cat1_node('.nav_link .nav_item-title').text().strip()
            if cat1_name == 'Designers':
                continue
            if cat1_name == 'Gifts':
                break
            cat1_url = cat1_node('.nav_link').attr('href')

            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            child = cat1_node('.nav_sub-menu-wrapper .nav_sub-menu-container ul.nav_sub-menu')
            for cat2_node in child.items():
                cat2_name = child('.nav_sub-menu-group .nav_sub-menu-title').text().strip()
                if cat2_name == 'Featured Brands':
                    break
                cat2_url = cat1_url
                for cat3_node in cat2_node('.nav_sub-menu-group .nav_sub-menu-list .nav_sub-menu-item').items():
                    pass



    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        raise NotImplementedError

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        raise NotImplementedError

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        raise NotImplementedError
