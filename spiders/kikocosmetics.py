# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy

import urllib3
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery

urllib3.disable_warnings()


class KikocosmeticsCrawler(IndexListDetailCrawler):
    """

    """

    INDEX_URL = 'https://www.kikocosmetics.com/en-gb/'
    WAIT = [1, 6]

    def __init__(self):
        super(KikocosmeticsCrawler, self).__init__()

        # 商品店铺
        self.store = "KIKO_Milano"

        # 商品品牌
        self.brand = "KIKO_Milano"

        # 店铺ID
        self.store_id = 1489

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""
        if not resp:
            return
        headers = copy.copy(self.headers)
        headers['referer'] = resp.url
        pq = PyQuery(resp.text)

        node = pq('#main-menu-nav-first-menu-panel .nav .nav1  .nav1-item')
        for top_category in node.items():
            top_category_name = top_category('.nav1-link').text().strip()
            if top_category_name == 'MakeUp' or top_category_name == 'Skin Care' or top_category_name == 'Accessories':
                child_category = top_category('.nav2-wrapper .nav2 .nav3 .nav3-item .nav3-link')
                for child in child_category.items():
                    child_name = child('a').text()
                    child_url = self._full_url(url_from=resp.url, path=child.attr('href'))
                    categories = (top_category_name, child_name)
                    yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}
            elif top_category_name == 'NEW':
                list_node = top_category('.nav2-wrapper .highlights .highlight-item')
                for list_url in list_node.items():
                    child_name = list_url('a').text()
                    list_link = self._full_url(url_from=resp.url, path=list_url('a').attr('href'))
                    categories = (top_category_name, child_name)
                    yield list_link, headers, resp.cookies.get_dict(), {'categories': categories}
            elif top_category_name == 'Best Seller':
                list_node = top_category('.nav2-wrapper .nav2 .nav2-item  ')
                for list_url in list_node.items():
                    list_link = self._full_url(url_from=resp.url, path=list_url('a').attr('href'))
                    child_name = list_url('a').text()
                    categories = (top_category_name, child_name)
                    yield list_link, headers, resp.cookies.get_dict(), {'categories': categories}

    def _get_product_list(self, url, headers, cookies, meta):
        while True:
            resp = self.request(url=url, headers=headers, cookies=cookies,
                                rollback=self.push_category_info, meta=meta)
            if not resp:
                return

            pq = PyQuery(resp.text)
            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url, path=pq('.next-pag').attr('href'))
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        pq = PyQuery(resp.text)
        detail_node = pq('.mod-listing-wrapper #content .item')
        for li in detail_node.items():
            url = self._full_url(url_from=resp.url, path=li('a').attr('href'))
            product_id = url.rpartition('/')[-1][2:]
            meta['product_id'] = product_id
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, resp, url, meta):
        pq = PyQuery(resp.text)

        # 商品图片
        imgs = []
        for img in pq('.pics .js-pics-controls .owl-pagination .owl-page').items():
            img_url = self._full_url(url_from=resp.url, path=img('img').attr('src'))
            imgs.append(img_url)

        # 商品颜色图片
        color_imgs = []
        for color in pq('#colors-preview #set1 .icon').items():
            color_img = self._full_url(url_from=resp.url, path=color('img').attr('src'))
            color_imgs.append(color_img)

        # 商品名称
        name = pq('#dettaglio-prodotto .desc .title').text().strip()

        # 商品源地址
        product_source_url = url

        # 商品介绍
        description = [p.text().strip() for p in pq('.grid_8 #product-detail-tabs #info-item0 p').items()]

        # 商品价格
        # 原价
        was_price = pq('.actions .form-default .quantity #js-price .original-price ').text().strip()
        # 现价
        now_price = pq('.actions .form-default .quantity #js-price .current-price  ').text().strip()
        if not (was_price and now_price):
            now_price = pq('.actions .form-default .quantity #js-price .current-price ').text().strip()

        # 商品ID
        product_id = meta['product_id']

        # 商品分类
        categories = meta['categories']

        return {
            'url': product_source_url, 'imgs': imgs, 'color': color_imgs, 'name': name, 'description': description,
            'was_price': was_price, 'now_price': now_price, 'product_id': product_id, 'categories': categories,
            'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id
        }
