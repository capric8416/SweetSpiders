# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import re
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class RoyaldoultonCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.royaldoulton.co.uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(RoyaldoultonCrawler, self).__init__()

        # 商品店铺
        self.store = "Royal Doulton"

        # 商品品牌
        self.brand = "Royal Doulton"

        # 店铺ID
        self.store_id = 1326

        # 品牌ID
        self.brand_id = 444

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('.rd-header-navigation > ul > li.menu-item')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name == 'Gifts':
                break
            if cat1_name == 'NEW':
                cat1_url = cat1_node.children('a').attr('href')
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
            else:
                cat1_url = cat1_node.children('a').attr('href')
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

                cat2_nodes = pq('#megamenu-401 .container div.col-sm-2 h3')
                for cat2_node in cat2_nodes.items():
                    cat2_name = cat2_node.children('a').text().strip()
                    if not cat2_name:
                        continue
                    cat2_url = cat2_node.children('a').attr('href')

                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }

                    cat3_nodes = cat2_node.next('ul > li')
                    for cat3_node in cat3_nodes.items():
                        cat3_name = cat3_node.children('a').text().strip()
                        cat3_url = cat3_node.children('a').attr('href')

                        headers = copy.copy(self.headers)
                        headers['Referer'] = resp.url

                        cat2['children'].append({
                            'name': cat3_name, 'url': cat3_url,
                            'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                        })

                        results.append([
                            cat3_url, headers, resp.cookies.get_dict(),
                            {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url), (cat3_name, cat3_url)]}
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

            next_page_text = pq('.rd-btn:eq(3)').attr('data-module-args')
            if not next_page_text:
                break
            next_page = re.search(r'https:(.*)/', next_page_text).group()
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        if pq('#rd-product-list-category a.rd-product-list-item'):
            node = pq('#rd-product-list-category a.rd-product-list-item')
            for detail in node.items():
                url = self._full_url(url_from=resp.url, path=detail.attr('href'))
                if url:
                    meta['product_id'] = urlparse(url).path.split('/')[-1]
                    yield url, headers, resp.cookies.get_dict(), meta

        else:
            html = resp.json()['html']
            pq = PyQuery(html)
            for detail in pq('a').items():
                url = detail.attr('href')
                if url:
                    meta['product_id'] = urlparse(url).path.split('/')[-1]
                    yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        if resp.status_code == '200':
            pq = PyQuery(resp.text)

            # 商品图片
            images = []
            for img_node in pq('.rd-product-gallery-image a img').items():
                img_url = img_node.attr('src')
                if img_url:
                    images.append(img_url)
            images = list(set(images))

            # 商品名称
            name = pq('.rd-product-info .rd-product-info-name').text().strip()

            # 商品价格
            now_price = pq('.rd-product-info-price .regular-price').text().strip()

            # 商品介绍
            introduction = pq('#rd-product-details-collapse00 p').text().strip()

            # 商品详情
            details = pq('#rd-product-details-collapse3 table').text().strip()

            # 商品库存
            stock = 999

            # 商品编号
            code = pq('.rd-product-info .rd-product-info-meta').text().split()[-1]

            return {
                'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'now_price': now_price, 'introduction': introduction, 'details': details, 'stock': stock,
                'code': code, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
                'brand_id': self.brand_id,
                'coin_id': self.coin_id
            }
