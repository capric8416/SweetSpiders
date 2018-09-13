# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class WildswansCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'http://shop.wild-swans.com/clothing'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(WildswansCrawler, self).__init__()

        # 商品店铺
        self.store = "Wild Swans"

        # 商品品牌
        self.brand = "Wild Swans"

        # 店铺ID
        self.store_id = 1005

        # 品牌ID
        self.brand_id = 435

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('#shop-c1-nav h2')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name in ('Beauty', 'Books', 'Gift Voucher'):
                continue
            if cat1_name == 'DESIGNERS':
                break
            if cat1_name == 'CLOTHING':
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

                cat2_nodes = cat1_node.next('hr').next('#shop-navlist li a')
                for cat2_node in cat2_nodes.items():
                    cat2_name = cat2_node.text().strip()
                    cat2_url = self._full_url(url_from=resp.url, path=cat2_node.attr('href'))

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
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))

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

            next_page = self._full_url(url_from=resp.url, path=pq('.pagenav:last a:last').attr('href'))
            page_text = pq('.pagenav:last a:last').text().strip()
            if (not next_page) or (page_text == 'PREVIOUS'):
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""
        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('ul.product-list li')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail.children('a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-2]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""
        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#views .v1 a').items():
            img_url = self._full_url(url_from=resp.url, path=img_node.attr('href'))
            if img_url:
                images.append(img_url)

        # 商品名称
        name = pq('#shop-c2-right').children('div h1').text().strip() + pq('#shop-c2-right').children(
            'div h2').text().strip()

        # 商品价格
        if len(pq('#shop-c2-right').children('div h3')) == 2:
            was_price = pq('#shop-c2-right').children('div h3:first').text().strip()
            now_price = pq('#shop-c2-right').children('div h3:last').text().strip()
        else:
            was_price = None
            now_price = pq('#shop-c2-right').children('div h3').text().strip()

        # 商品介绍
        introduction = pq('#shop-c2-right').children('div p').text().strip()

        # 商品尺寸
        sizes = []
        for size_node in pq('select[name="sizecolour"] option').items():
            size = size_node.text().strip()
            if size:
                sizes.append(size)

        # 商品库存
        stock = 999

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction, 'sizes': sizes,
            'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id,
            'coin_id': self.coin_id

        }
