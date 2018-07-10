# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from SweetSpiders.scripts.google_translate import GoogleTranslate
from pyquery import PyQuery


class LasciviousCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'http://www.lascivious.co.uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(LasciviousCrawler, self).__init__()

        # 商品店铺
        self.store = "Lascivious"

        # 商品品牌
        self.brand = "Lascivious"

        # 店铺ID
        self.store_id = 923

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 152

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        results = []
        categories = []
        g = GoogleTranslate()
        top_node = pq('#navWrap #nav li.nav-item')
        for top in top_node.items():
            cat1_name = top('.nav-item-link').text().strip()
            if cat1_name == 'About':
                continue
            cat1_url = self._full_url(url_from=resp.url, path=top('.nav-item-link').attr('href'))

            cat1 = {'name': cat1_name, 'name_cn': g.query(source=cat1_name), 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            for cat2 in top('.sub-nav .sub-nav-item').items():
                cat2_name = cat2('a').text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=cat2('a').attr('href'))

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url

                cat1['children'].append({
                    'name': cat2_name, 'name_cn': g.query(source=cat2_name), 'url': cat2_url,
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                })

                results.append([
                    cat2_url, headers, resp.cookies.get_dict(),
                    {'categories': [(cat1_name, g.query(source=cat1_name), cat1_url),
                                    (cat2_name, g.query(source=cat2_name), cat2_url)]}
                ])

            categories.append(cat1)
        return categories, results

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

            next_page = pq('.next').attr('href')
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#coll-product-list .grid-item')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.coll-image-wrap a').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)
        images = []
        for img in pq('#product-photo-thumbs li').items():
            img_url = self._full_url(url_from=resp.url, path=img('a').attr('href'))
            images.append(img_url)

        name = pq('.grid-item h1').text().strip()

        description = pq('#product-description #full_description').text().strip()

        was_price = pq('#product-price .product-compare-price').text().strip()

        now_price = pq('#product-price .on-sale').text().strip()
        if not (was_price and now_price):
            now_price = pq('#product-price .product-price').text().strip()

        sizes = []
        for size_node in pq('option').items():
            size = size_node.text().strip()
            sizes.append(size)

        stock_text = pq('[itemprop="availability"]').attr('href')
        stock = 999 if 'InStock' in stock_text else 0

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'description': description, 'was_price': was_price, 'now_price': now_price,
            'size': sizes, 'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
