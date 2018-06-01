# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy
from urllib.parse import urlparse


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
        pq = PyQuery(resp.text)
        results = []
        categories = []

        node = pq('.wrapper #mainMenu .main-menu .has-child')
        for top in node.items():
            top_category = top('a:eq(0)').text().strip()
            for child in top('.sub-menu-mob li').items():
                child_category = child('a').text().strip()
                child_url = child('a').attr('href')
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

            next_page = pq('.pagination a.i-next').attr('href')
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.main-wrapper .wrapper .category-products .grid-list .ditem')
        for detail in node.items():
            url = detail('a').attr('href')
            meta['product_id'] = urlparse(url).path.split('/')[-1]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta):
        """详情页解析器"""
        _ = self
        pq = PyQuery(resp.text)
        imgs = []
        node = pq('.img-side .MagicToolboxContainer a')
        if len(node) == 1:
            imgs.append(pq('.MagicToolboxContainer .MagicToolboxMainContainer .MagicZoom').attr('href'))
        else:
            for img in pq('.img-side .MagicToolboxContainer .mz-thumb').items():
                img_url = img.attr('href')
                imgs.append(img_url)

        name = pq('.product-side .desk-only h1.ptitle').text().strip()

        in_stock = pq('.product-view .product-side .desk-only .availability span').text().strip()

        short_desc = pq('.product-side .product .short-desc').text().strip()

        price = pq('.add-to-box .price-qty .price').text().strip()

        description = [p.text().strip() for p in pq('.description-bottom #content1').items()]

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'img': imgs,
            'name': name, 'in_stock': in_stock, 'short_desc': short_desc, 'price': price, 'description': description,
            'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id
        }
