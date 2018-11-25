# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class JohnlewisCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.johnlewis.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(JohnlewisCrawler, self).__init__()

        # 商品店铺
        self.store = "John Lewis"

        # 商品品牌
        self.brand = "John Lewis"

        # 店铺ID
        self.store_id = 2617

        # 品牌ID
        self.brand_id = 1235

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('ul.primary-link-list-list--b3ea2 > li.primary-link-list-item--23ac8')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text()
            if cat1_name in ('Furniture & Lights', 'Electricals'):
                continue
            if cat1_name == 'Gifts':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children(
                'div.category-list-container--62727 > ul.category-list-links--776a4 > li.category-nav-lrg-secondary-cat--5236a')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('.category-title--f2288').text().strip()
                if cat2_name in ('Cards, Wrap & Crafts', 'Cooking & Dining', "Don't Miss"):
                    break
                if cat2_name == 'Featured Brands':
                    if cat1_name == 'Beauty':
                        continue
                    else:
                        break
                cat2_url = cat1_url
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                cat3_nodes = cat2_node.children('div.category-nav-lrg-secondary-list-wrapper--7ada9 > ul > li')
                for cat3_node in cat3_nodes.items():
                    cat3_name = cat3_node.children('a').text()
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
        params = {}
        page = 1
        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies, params=params
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            page += 1
            params.update({'incremental': 'true', 'page': page})
            next_page = url
            if len(pq('.product-list-container > .product-card')) < 24:
                break

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.product-list-container > .product-card')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.product-card__info a:first').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []

        # 商品名称
        name = pq('.standard-product-column-right .product-header .product-header__title').text().strip()

        # 商品价格
        was_price = pq('.prices-container .price__previous:first .price__strikethrough').text().strip()
        now_price = pq('.prices-container .price__current').text().strip()
        if not (was_price and now_price):
            now_price = pq('.prices-container .price').text().strip()

        # 商品颜色文字
        colors = []
        for color_node in pq('ul.swatch-list li.swatch-list-item').items():
            color = color_node.children('a .swatch-text').text().strip()
            if color:
                colors.append(color)

        # 商品颜色链接
        color_links = []
        for color_link_node in pq('ul.swatch-list li.swatch-list-item').items():
            color_link = self._full_url(url_from=resp.url, path=color_link_node.children('a img').attr('src'))
            if color_link:
                color_links.append(color_link)

        # 商品尺寸
        sizes = []
        for size_node in pq('ul.size-list li').items():
            size = size_node.children('a').text().strip()
            if size:
                sizes.append(size)

        # 商品介绍
        introduction = pq()
