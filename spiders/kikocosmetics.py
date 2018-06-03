# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class KikocosmeticsCrawler(IndexListDetailCrawler):
    """

    """

    INDEX_URL = 'https://www.kikocosmetics.com/en-gb/'
    WAIT = [1, 5]

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

        # 品牌ID
        self.brand_id = 145

    def _parse_index(self, resp):
        """首页解析器"""
        results = []
        categories = []
        pq = PyQuery(resp.text)

        node = pq('#main-menu-nav-first-menu-panel .nav .nav1  .nav1-item')
        for top_category in node.items():
            cat1_name = top_category('.nav1-link').text().strip()
            if cat1_name == 'MakeUp' or cat1_name == 'Skin Care' or cat1_name == 'Accessories':
                cat1_url = self._full_url(url_from=resp.url, path=top_category('.nav1-link').attr('href'))
                cat1 = {
                    'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)
                }
                child_category = top_category('.nav2-wrapper .nav2 .nav3 .nav3-item .nav3-link')
                for child in child_category.items():
                    cat2_name = child('a').text()
                    cat2_url = self._full_url(url_from=resp.url, path=child.attr('href'))

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
            elif cat1_name == 'NEW':
                cat1_url = self._full_url(url_from=resp.url, path=top_category('.nav1-link').attr('href'))
                cat1 = {
                    'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)
                }
                list_node = top_category('.nav2-wrapper .highlights .highlight-item')
                for list_url in list_node.items():
                    cat2_name = list_url('a').text()
                    cat2_url = self._full_url(url_from=resp.url, path=list_url('a').attr('href'))

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
            elif cat1_name == 'Best Seller':
                cat1_url = self._full_url(url_from=resp.url, path=top_category('.nav1-link').attr('href'))
                cat1 = {
                    'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)
                }
                list_node = top_category('.nav2-wrapper .nav2 .nav2-item  ')
                for list_url in list_node.items():
                    cat2_url = self._full_url(url_from=resp.url, path=list_url('a').attr('href'))
                    cat2_name = list_url('a').text()

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
        while True:
            resp = self._request(url=url, headers=headers, cookies=cookies, rollback=self.push_category_info, meta=meta)
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
            'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id,
            'brand_id': self.brand_id,
        }
