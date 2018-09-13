# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import json
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class TowerlondonCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.tower-london.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(TowerlondonCrawler, self).__init__()

        # 商品店铺
        self.store = "Tower london"

        # 商品品牌
        self.brand = "Tower london"

        # 店铺ID
        self.store_id = 1716

        # 品牌ID
        self.brand_id = 425

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('#nav > li.nav-item')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a.level-top').text().strip()
            if not cat1_name:
                continue
            if cat1_name == 'Brands':
                continue
            if cat1_name == '| BLOG':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a.level-top').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('div.nav-panel .nav-block--center > ul.nav-submenu > li.nav-item')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('a').text().strip()
                if cat2_name in ('View All Womens Shoes', 'View All Mens Shoes', 'SHOP THE TREND', 'SHOP BY PRICE'):
                    break
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node.children('a').attr('href'))
                if not cat2_url:
                    cat2_url = self.INDEX_URL
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                cat3_nodes = cat2_node.children('ul.nav-submenu > li.nav-item')
                for cat3_node in cat3_nodes.items():
                    cat3_name = cat3_node.children('a').text().strip()
                    cat3_url = self._full_url(url_from=resp.url, path=cat3_node.children('a').attr('href'))

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat2['children'].append({
                        'name': cat3_name, 'url': cat3_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                    })

                    results.append([
                        cat3_url, headers, resp.cookies.get_dict(),
                        {'categories': [(cat1_name, cat1_url),
                                        (cat2_name, cat2_url),
                                        (cat3_name, cat3_url)]}
                    ])

                cat1['children'].append(cat2)

            categories.append(cat1)
        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url, path=pq('li.next:last a.next').attr('href'))
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.category-products > ul.products-grid > li.item')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.product-name a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#itemslider-zoom div.item').items():
            img_url = self._full_url(url_from=resp.url, path=img_node.children('a').attr('href'))
            if img_url:
                images.append(img_url)

        # 商品名称
        name = pq('.product-primary-column .product-name').text().strip()

        # 商品价格
        was_price = pq('.product-type-data .price-box .old-price .price').text().strip()
        now_price = pq('.product-type-data .price-box .special-price .price').text().strip()
        if not (was_price and now_price):
            now_price = pq('.product-type-data .price-box .price').text().strip()

        # 商品介绍
        introduction = pq('.short-description .std').text().strip()

        # 商品尺寸
        sizes = []
        if pq('script:contains("var spConfig")'):
            json_data = pq('script:contains("var spConfig")').text().strip().partition('(')[-1].partition(')')[0]
            data = json.loads(json_data)
            size_nodes = data['attributes']['500']['options']
            for size_node in size_nodes:
                size = size_node['label']
                if size:
                    sizes.append(size)

        # 商品详情
        details = pq('#product-tabs .tabs-panels .panel:first .data-table tbody').text().strip()

        # 商品库存
        stock = 0
        stock_text = pq('.availability span').text().strip()
        if 'In' in stock_text:
            stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
                'sizes': sizes, 'details': details, 'stock': stock, 'store': self.store, 'brand': self.brand,
                'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
