# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class KokontozaiCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.kokontozai.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(KokontozaiCrawler, self).__init__()

        # 商品店铺
        self.store = "Kokon to Zai"

        # 商品品牌
        self.brand = "Kokon to Zai"

        # 店铺ID
        self.store_id = 1120

        # 品牌ID
        self.brand_id = 408

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        results = []
        categories = []

        node1 = pq('ul.elementor-nav-menu:eq(0) li.menu-item')
        for cat1_node in node1.items():
            cat1_name = cat1_node('a.elementor-item').text().strip()
            if cat1_name in ('HOME', 'LOOKBOOK'):
                continue
            elif cat1_name == 'ACCESSORIES':
                break
            elif cat1_name == 'SHOP':
                cat1_url = cat1_node('a.elementor-item').attr('href')

                cat1 = {'name': cat1_name, 'url': cat1_url,
                        'children': [],
                        'uuid': self.cu.get_or_create(cat1_name)}
                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                resp = self._request(url=cat1_url, headers=headers)
                pq = PyQuery(resp.text)
                cat2_nodes = pq('section.elementor-element div.elementor-widget-button div.elementor-button-wrapper')
                for cat2_node in cat2_nodes.items():
                    cat2_name = cat2_node.children('a').text().strip()
                    if cat2_name == 'SS18':
                        continue
                    cat2_url = cat2_node.children('a').attr('href')

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat1['children'].append({
                        'name': cat2_name, 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.append([
                        cat2_url, headers, resp.cookies.get_dict(),
                        {'categories': [(cat1_name, cat1_url),
                                        (cat2_name, cat2_url)]}
                    ])

                categories.append(cat1)
            else:
                cat1_url = cat1_node('a.elementor-item').attr('href')

                cat1 = {'name': cat1_name, 'url': cat1_url,
                        'uuid': self.cu.get_or_create(cat1_name)}

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                cookies = resp.cookies.get_dict()

                results.append([
                    cat1_url, headers, cookies,
                    {'categories': [(cat1_name, cat1_url)]}
                ])

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

            next_page = pq('.next').attr('href')
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('div.elementor-widget-container ul.products li.product')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail.children('a.woocommerce-LoopProduct-link').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.strip('/').split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#main .woocommerce-product-gallery__image').items():
            img_url = self._full_url(url_from=resp.url, path=img_node('img').attr('src'))
            if img_url:
                images.append(img_url)

        # 商品名称
        name = pq('div.summary h1.product_title').text().strip()

        # 商品价格
        was_price = pq('div.summary .cart_price').children('del .woocommerce-Price-amount').text().strip()

        now_price = pq('div.summary .cart_price').children('ins .woocommerce-Price-amount').text().strip()

        # 商品尺寸
        sizes = []
        for size_node in pq('#pa_size option').items():
            size = size_node.text().strip()
            if size != 'Choose an option':
                sizes.append(size)

        # 商品库存
        stock = 999

        # 商品介绍
        description = pq('div.summary .woocommerce-product-details__short-description p').text().strip()

        link = 'http://kokontozai.com/wp-admin/admin-ajax.php'
        data_id = pq('.woo_discount_rules_variant_table').attr('data-id')
        data = {'action': 'loadWooDiscountedDiscountTable', 'id': data_id}
        resp = self._request(url=link, method='post', headers=extra['headers'], cookies=extra['cookies'], data=data)
        pq = PyQuery(resp.text)
        details = pq('table tbody td:first').text().strip()

        introduction = description + ' ' + details

        # 商品折扣
        discount = pq('table tbody td:last').text().strip()

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
            'discount': discount, 'sizes': sizes, 'stock': stock, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
