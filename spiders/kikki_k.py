# -*- coding: utf-8 -*-
# !/usr/bin/env python
import base64
import copy
import json
from urllib.parse import urlparse

import execjs
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class KikkikCrawler(IndexListDetailCrawler):
    """

    """
    INDEX_URL = 'https://www.kikki-k.com/'

    WAIT = [1, 5]

    def __init__(self):
        super(KikkikCrawler, self).__init__()
        # 商品店铺
        self.store = "kikki-k"

        # 商品品牌
        self.brand = "kikki-k"

        # 店铺ID
        self.store_id = 1607

        # 货币ID
        self.coin_id = 4

        # 品牌ID
        self.brand_id = 144

    def _parse_index(self, resp):
        """首页解析器"""
        results = []
        categories = []
        pq = PyQuery(resp.text)

        node = pq('#nav li.nav-item--parent')
        for top in node.items():
            cat1_name = top('a.level-top span').text().strip()
            if cat1_name == 'Shop By':
                continue
            if cat1_name == 'Home':
                    break
            if cat1_name == 'Diaries & Calendars':
                cat1_url = top('a.level-top').attr('href')

                cat1 = {
                    'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)
                }
                child_node = top('.nav-panel--dropdown .nav-panel-inner .nav-block--center ul.nav-submenu li.level1 ul li.level2')
                for child in child_node.items():
                    cat2_name = child('a span').text().strip()
                    cat2_url = child('a').attr('href')

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat1['children'].append({
                        'name': cat2_name, 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.append([
                        cat2_url, headers, resp.cookies.get_dict(),
                        {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url)]}
                    ])

                categories.append(cat1)
            else:
                cat1_url = top('a.level-top').attr('href')
                cat1 = {
                    'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)
                }
                child_node = top('.nav-panel--dropdown .nav-panel-inner .nav-block--center ul.nav-submenu li.level1')
                for child in child_node.items():
                    cat2_name = child('a span').text().strip()
                    if cat2_name == 'View All':
                        continue
                    cat2_url = child('a').attr('href')

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat1['children'].append({
                        'name': cat2_name, 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.append([
                        cat2_url, headers, resp.cookies.get_dict(),
                        {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url)]}
                    ])

                categories.append(cat1)

        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        resp = self._request(url=url, headers=headers, cookies=cookies,  meta=meta)
        if not resp:
            return

        pq = PyQuery(resp.text)
        for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
            self.push_product_info(info)

        script = pq("script:contains('_ajaxCatalog')").text().strip()
        if not script:
            return

        script = script.partition('AWAjaxCatalog')[-1].strip().strip('();')
        script = script.replace('buttonType', '"scroll"')
        res = execjs.eval('(function(){ var value=' + script + ';return value; })()')
        params = res.get('params')
        params['p'] = res.get('next_page')
        while True:
            next_url = res.get('next_url').format('').format(
                page=base64.b64encode(json.dumps(params).encode()).decode())
            resp = self._request(url=next_url, headers=headers)
            data = resp.json()

            next_page = data.get('next_page')
            for info in self._parse_product_page_list(resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            if not next_page:
                break
            params['p'] = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        pq = PyQuery(resp.text)
        category_node = pq('.category-products .product-image-wrapper')
        for div in category_node.items():
            url = div('.product-image').attr('href')
            meta['product_id'] = urlparse(url).path[1:]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_page_list(self, resp, headers, meta):
        _ = self
        headers = copy.copy(headers)
        headers['Referer'] = resp.url
        data = resp.json()
        text = data['content']
        pq = PyQuery(text.replace('\\/', '/'))
        for a in pq('.category-products .products-grid .item .product-name').items():
            url = a('a').attr('href')
            meta['product'] = urlparse(url).path[1:]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        pq = PyQuery(resp.text)
        # 商品图片
        imgs = []
        img_node = pq('.more-images .wrap-slider .slides li')
        for img in img_node.items():
            img_url = img('a').attr('href')
            imgs.append(img_url)

        # 商品名
        name = pq('.product-shop .product-name h1').text().strip()

        # 原价
        was_price = pq('.product-type-data .price-box .old-price .price').text().strip()
        # 现价
        now_price = pq('.product-type-data .price-box .special-price .price').text().strip()
        if not (was_price and now_price):
            now_price = pq('.product-type-data .price-box .regular-price .price').text().strip()

        # 商品特征描述
        p1 = pq('.tabs-panels .panel .std').text().strip()
        p2 = pq('.tabs-panels .panel:eq(0) p').text().strip()
        features = p1 + '\n' + p2

        # 商品介绍
        description = pq('.short-description').text().strip()

        # 库存
        stock_text = pq('.product-type-data p').attr('class')
        stock = 999 if 'in-stock' in stock_text else 0

        return {'url': url, 'img': imgs, 'was_price': was_price, 'categories': meta['categories'],
                'now_price': now_price, 'features': features, 'description': description,
                'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id,
                'product_id': meta['product_id'], 'name': name, 'brand_id': self.brand_id, 'stock': stock
                }
