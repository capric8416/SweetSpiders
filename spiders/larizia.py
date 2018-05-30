# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy


class LariziaCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'http://www.larizia.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(LariziaCrawler, self).__init__()

        # 商品店铺
        self.store = "Larizia"

        # 商品品牌
        self.brand = "Larizia"

        # 店铺ID
        self.store_id = 1717

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        node = pq('.container #site-header__nav__21 li')
        for top in node.items():
            top_category = top('a').text().strip()
            if top_category == 'New Arrivals ':
                url = self._full_url(url_from=resp.url, path=top('a').attr('href'))
                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                categories = (top_category,)
                yield url, headers, resp.cookies.get_dict(), {'categories': categories}
            elif top_category == 'Designers':
                continue
            else:
                child_node = top('.drop-down__menu__block  ul.drop-down__menu__categories li:gt(0)')
                for child in child_node.items():
                    child_category = child('a span').text().strip()
                    if child_category == ('View All Bags' or 'View All Shoes' or 'View All Accessories'):
                        continue
                    child_url = self._full_url(url_from=resp.url, path=child('a').attr('href'))
                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url
                    categories = (top_category, child_category)
                    yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        raise NotImplementedError

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        raise NotImplementedError

    def _parse_product_detail(self, url, resp, meta):
        """详情页解析器"""

        raise NotImplementedError
