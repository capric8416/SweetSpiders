# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class LaportegnaCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.laportegna.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(LaportegnaCrawler, self).__init__()

        # 商品店铺
        self.store = "La Portegna"

        # 商品品牌
        self.brand = "La Portegna"

        # 店铺ID
        self.store_id = 1016

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        node = pq('.site-header .wrapper .nav-bar .site-nav li.has-dropdown')
        for top in node.items():
            top_category = top('a:eq(0)').text().strip()
            if top_category == 'New In':
                child_node = top('.dropdown li')
                for child in child_node.items():
                    child_category = child('a').text().strip()
                    child_url = self._full_url(url_from=resp.url, path=child('a').attr('href'))
                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url
                    categories = (top_category, child_category)
                    yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}
            else:
                child_node = top('.dropdown .has-sub-dropdown')
                for child in child_node.items():
                    child_category = child('a:eq(0)').text().strip()
                    for url in child('.sub-dropdown .sub-dropdown-item  a').items():
                        child_url = self._full_url(url_from=resp.url, path=url.attr('href'))
                        categories = (top_category, child_category)
                        headers = copy.copy(self.headers)
                        headers['Referer'] = resp.url
                        yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies,
                rollback=self.push_category_info, meta=meta
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url,
                                       path=pq('.collection-footer .pagination li:last a').attr('href'))
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""
        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.collection-container .products .box')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.product-title a').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        imgs = []
        for img in pq('.thumbnails #ProductThumbs-product-template li').items():
            img_url = self._full_url(url_from=resp.url, path=img('a').attr('href'))
            imgs.append(img_url)

        name = pq('.product-aside .purchase-box #AddToCartForm .product-title h1').text().strip()

        price = pq('#AddToCartForm #ProductPrice-product-template').text().strip()

        sizes = []
        for size_node in pq('.single-option-selector option').items():
            size = size_node.text().strip()
            sizes.append(size)

        features = [li.text().strip() for li in pq('.description ul li').items()]

        description = [p.text().strip() for p in pq('.description p').items()]

        # add to cart表示有库存, sold out表示售罄
        in_stock = pq('.selection-wrapper .button-wrapper #AddToCartText-product-template').text().strip()

        return {
            'url': url, 'product_id': meta['product_id'], 'imgs': imgs, 'name': name, 'price': price,
            'sizes': sizes, 'features': features, 'description': description, 'in_stock': in_stock, ''
                                                                                                    'store': self.store,
            'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id
        }
