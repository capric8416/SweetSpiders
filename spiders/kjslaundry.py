# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class KjslaundryCrawler(IndexListDetailCrawler):
    """

    """
    INDEX_URL = 'http://www.kjslaundry.com/'

    WAIT = [1, 5]

    def __init__(self):
        super(KjslaundryCrawler, self).__init__()

        # 商品店铺
        self.store = "Kj's Laundry"

        # 商品品牌
        self.brand = "Kj's Laundry"

        # 店铺ID
        self.store_id = 412

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        first_category_node = pq('#mainNav-menu .mainNav-dropdown a')
        first_category_name = first_category_node[0].text.strip()

        category_node = pq('#mainNav-menu .mainNav-dropdown ul li')
        for category in category_node.items():
            category_name = category('a').text().strip()
            if category_name == 'END OF LINE SALE':
                break
            category_url = self._full_url(url_from=resp.url, path=category('a').attr('href'))
            categories = (first_category_name, category_name)

            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url

            yield category_url, headers, resp.cookies.get_dict(), {'categories': categories}

    def _get_product_list(self, url, headers, cookies, meta):
        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies, rollback=self.push_category_info, meta=meta)
            pq = PyQuery(resp.text)
            next_url = pq('[rel="next"]').attr('href')

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            if not next_url:
                break
            else:
                url = next_url

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""
        headers = copy.copy(headers)
        headers['Referer'] = resp.url
        for img in pq('#ctl00_PageContentPlaceHolder_PTagBorder .list-item').items():
            url = self._full_url(url_from=resp.url, path=img('a').attr('href'))
            meta['product_id'] = url.split('/')[-1][:-5]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        pq = PyQuery(resp.text)
        # 商品图片
        img_urls = []
        img_node = pq('.product-left-box #productImages .slides a')
        for img in img_node.items():
            img_url = self._full_url(url_from=resp.url, path=img.attr('href'))
            img_urls.append(img_url)

        # 商品名
        name = pq('.product-right-box .product-name').text().strip()

        # 原价
        was_price = pq('.product-right-box .price-box .priceWas').text().split(' ')[-1]

        # 现价
        now_price = pq('.product-right-box .price-box .priceNow').text().split(' ')[-1]
        if not (was_price and now_price):
            now_price = pq('.product-right-box .price-box .price').text()

        # 商品详情描述
        description = pq('.product-right-box .product-desc').text().strip()

        # 商品ID
        product_id = meta['product_id']

        # 商品尺寸
        size_list = []
        size_node = pq('#ctl00_PageContentPlaceHolder_OptionsList [selected!="selected"]')
        for size in size_node.items():
            size = size.text().strip()
            size_list.append(size)

        return {'url': url, 'categories': meta['categories'], 'img': img_urls, 'was_price': was_price,
                'now_price': now_price, 'description': description, 'size': size_list, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id, 'product_id': product_id,
                'name': name,
                }
