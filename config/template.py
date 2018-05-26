# -*- coding: utf-8 -*-
# !/usr/bin/env python

TEMPLATE = '''
# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler


class {class_name}(IndexListDetailCrawler):
    """
    {comment}
    """

    INDEX_URL = '{index_url}'  # 首页链接

    WAIT = {wait}  # 动态休眠区间

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

'''
