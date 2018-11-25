# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import json
import time
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class DaisyjewelleryCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.daisyjewellery.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(DaisyjewelleryCrawler, self).__init__()

        # 商品店铺
        self.store = "Daisy"

        # 商品品牌
        self.brand = "Daisy"

        # 店铺ID
        self.store_id = 2220

        # 品牌ID
        self.brand_id = 719

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        results = []
        categories = []

        ts = int(time.time())

        material_link = f'https://www.daisyjewellery.com/js/init.js?t{ts}'
        material_data_resp = self._request(url=material_link, headers=self.headers)
        json_material = material_data_resp.text.partition('=')[-1]
        data = json.loads(json_material)
        materials = data['data']['attribute']
        default_material = {}
        for each in materials:
            if each['id'] == 220:
                default_material = {item['value']: item['label'] for item in each['options']}
        assert default_material, '材质未找到'

        menu = data['website']['meganav']
        for cat1_node in menu:
            cat1_name = cat1_node['text']
            if cat1_name in ('JEWELLERY', 'ESTÉE LALONDE', 'BESTSELLERS', 'GIFTS'):
                continue
            if cat1_name == 'INSPIRE':
                break
            cat1_link = self._full_url(url_from=resp.url, path=cat1_node['link'])
            cat1_url = 'https://www.daisyjewellery.com/api/category' + urlparse(cat1_link).path + '/verbosity/3'
            cat1 = {'name': cat1_name, 'url': cat1_url,
                    'uuid': self.cu.get_or_create(cat1_name)}

            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url
            cookies = resp.cookies.get_dict()

            results.append([
                cat1_url, headers, cookies,
                {'categories': [(cat1_name, cat1_url)], 'default_material': default_material}
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
            if pq('.next'):
                next_page = self._full_url(url_from=resp.url, path=pq('.next').attr('href'))
                if next_page:
                    url = next_page
            else:
                break

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        # list_link = 'https://www.daisyjewellery.com/api/category' + urlparse(resp.url).path + '/verbosity/3'
        # resp = self._request(url=list_link, headers=headers)
        data = resp.json()['product']
        for detail in data:
            detail_url = self._full_url(url_from=resp.url, path=detail.get('url'))
            if detail_url:
                meta['product_id'] = urlparse(detail_url).path.split('/')[-1]
                url = 'https://www.daisyjewellery.com/api/product' + urlparse(detail_url).path + '/verbosity/3'
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""
        json_data = resp.text
        datas = json.loads(json_data)['product']
        for each in datas:
            if 'children_listing' in each:
                data_lists = each['children_listing']
                ids = [each_id['product_id'] for each_id in data_lists]
                data = {'ids': ids, 'verbosity': '3'}

                post_url = 'https://www.daisyjewellery.com/api/product/'
                resp = self._request(url=post_url, method='post', data=data, headers=extra['headers'])
                print(resp.json())
            if 'parent' in each:
                ids = []
                ids.append(each['parent'])
                data = {'ids': ids, 'verbosity': '3'}

                post_url = 'https://www.daisyjewellery.com/api/product/'
                resp = self._request(url=post_url, method='post', data=data, headers=extra['headers'])
                print(resp.json())

    # 商品图片

    # 商品名称

    # 商品价格

    # 商品颜色

    # 商品介绍

    # 商品库存
