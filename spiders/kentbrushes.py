# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler


class KentbrushesCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://kentbrushes.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(KentbrushesCrawler, self).__init__()

        # 商品店铺
        self.store = "Kent Brushes"

        # 商品品牌
        self.brand = "Kent Brushes"

        # 店铺ID
        self.store_id = 884

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        raise NotImplementedError

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        raise NotImplementedError

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        raise NotImplementedError

    def _parse_product_detail(self, url, resp, meta):
        """详情页解析器"""

        raise NotImplementedError
