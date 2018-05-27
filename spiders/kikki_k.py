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

    def _parse_index(self, resp):
        """首页解析器"""
        if not resp:
            return
        headers = copy.copy(self.headers)
        headers['referer'] = resp.url
        pq = PyQuery(resp.text)
        node = pq('#nav li.nav-2')
        top_category = node('a:eq(0) span').text().strip()
        child_node = node('.nav-panel--dropdown .menu-mobile-desktop .nav-submenu .classic')
        for child in child_node.items():
            child_category = child('a span').text()
            child_url = child('a').attr('href')
            categories = (top_category, child_category)
            yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

        node2 = pq('#nav li.nav-3')
        top2_category = node2('a:eq(0) span').text().strip()
        child2_node = node2('.nav-panel--dropdown .nav-block--center .nav-submenu--mega li')
        for child in child2_node.items():
            child_category = child('a span').text().strip()
            child_url = child('a').attr('href')
            categories = (top2_category, child_category)
            yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

        node3 = pq('#nav li.nav-4')
        top3_category = node3('a:eq(0) span').text().strip()
        child3_node = node3('.nav-panel--dropdown .nav-block--center .nav-submenu--mega li')
        for child in child3_node.items():
            child3_category = child('a span').text().strip()
            child_url = child('a').attr('href')
            categories = (top3_category, child3_category)
            yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

        node4 = pq('#nav li.nav-5')
        top4_category = node4('a:eq(0) span').text().strip()
        child4_node = node4('.nav-panel--dropdown .nav-block--center .nav-submenu--mega li')
        for child in child4_node.items():
            child4_category = child('a span').text().strip()
            child_url = child('a').attr('href')
            categories = (top4_category, child4_category)
            yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

        node5 = pq('#nav li.nav-6')
        top5_category = node5('a:eq(0) span').text().strip()
        child5_node = node5('.nav-panel--dropdown .nav-block ul')
        for child in child5_node.items():
            for a in child('li a').items():
                child5_category = a('span').text().strip()
                child_url = a.attr('href')
                categories = (top5_category, child5_category)
                yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

        node6 = pq('#nav li.nav-7')
        top6_category = node6('a:eq(0) span').text().strip()
        child6_node = node6('.nav-panel--dropdown .nav-block--center .nav-submenu--mega li')
        for child in child6_node.items():
            child6_category = child('a span').text().strip()
            child_url = child('a').attr('href')
            categories = (top6_category, child6_category)
            yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

    def _get_product_list(self, url, headers, cookies, meta):
        resp = self._request(url=url, headers=headers, cookies=cookies, rollback=self.push_category_info, meta=meta)
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

    def _parse_product_detail(self, resp, url, meta):
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

        return {'url': url, 'img': imgs, 'was_price': was_price, 'categories': meta['categories'],
                'now_price': now_price, 'features': features, 'description': description,
                'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id,
                'product_id': meta['product_id'], 'name': name,
                }
