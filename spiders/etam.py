# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery

from common.translate import GoogleTranslate


class EtamCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.etam.com/accueil'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(EtamCrawler, self).__init__()

        # 商品店铺
        self.store = "Etam"

        # 商品品牌
        self.brand = "Etam"

        # 店铺ID
        self.store_id = 173

        # 货币ID
        self.coin_id = 3

        # 品牌ID
        self.brand_id = '品牌建立中'

    def _parse_index(self, resp):
        """首页解析器"""
        g = GoogleTranslate()
        pq = PyQuery(resp.text)
        results = []
        categories = []

        cat1_nodes = pq('#navigation ul.menu-category li.mainItem')
        for cat1_node in cat1_nodes.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name == 'NEW':
                continue
            cat1_url = cat1_node.children('a').attr('href')

            cat1 = {'name': cat1_name, 'name_cn': g.query(source=cat1_name, sl='fr'), 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('.menu-wrapper .colMenu ul.wrapItemMenu li.titleCat')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('a.expandMenu').text().strip().partition(' ')[-1]
                cat2_url = cat2_node.children('a.expandMenu').attr('href')

                cat2 = {
                    'name': cat2_name, 'name_cn': g.query(source=cat2_name, sl='fr'), 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                cat3_nodes = cat2_node.children('div.subMenuCat ul li.itemMenu')
                for cat3_node in cat3_nodes.items():
                    cat3_name = cat3_node.children('a').text().strip().partition(' ')[-1]
                    if ('Tout' in cat3_name) or ('Tous' in cat3_name):
                        continue
                    cat3_url = cat3_node.children('a').attr('href')

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat2['children'].append({
                        'name': cat3_name, 'name_cn': g.query(source=cat3_name, sl='fr'), 'url': cat3_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                    })

                    results.append([
                        cat3_url, headers, resp.cookies.get_dict(),
                        {'categories': [(cat1_name, g.query(source=cat1_name, sl='fr'), cat1_url),
                                        (cat2_name, g.query(source=cat2_name, sl='fr'), cat2_url),
                                        (cat3_name, g.query(source=cat3_name, sl='fr'), cat3_url)]}
                    ])

                cat1['children'].append(cat2)

            categories.append(cat1)
        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""
        params = {}
        start = 0
        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies, params=params,
                rollback=self.push_category_info, meta=meta)
            if not resp:
                return
            pq = PyQuery(resp.text)
            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = 'https://www.etam.com/maillots-de-bain/toutlebain'
            if len(pq('#search-result-items li.grid-tile')) < 48:
                break
            start += 48
            params.update({'start': start, 'amp;sz': 48})
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#search-result-items li.grid-tile')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.product-tile .product-informations a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.partition('.')[0].split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#pdpMain .swiper-container .swiper-wrapper .swiper-slide a.eazyZLink').items():
            img_url = img_node.attr('href')
            if img_url:
                images.append(img_url)

        images = list(set(images))

        # 商品名称
        name = pq('.product-detail .topDetails p.product-name').text().strip()

        # 商品价格
        was_price = pq('.product-detail .product-price-wrap span.price-standard').text().strip()

        now_price = pq('.product-detail .product-price-wrap span.price-sales').text().strip()

        # 商品折扣
        discount = pq('.product-detail .product-price-wrap span.percentage').text().strip()

        # 商品颜色
        colors, color_urls = [], []
        for color_node in pq('.colors ul li').items():
            color = color_node.attr('data-colorname')
            if color:
                colors.append(color)

            color_link = color_node.children('a').attr('style').split('(')[-1].strip(')')
            if color_link:
                color_urls.append(color_link)

        # 商品尺码
        sizes = []
        for size_node in pq('ul.product-size li[class!="unselectable"] a').items():
            in_stock_size = size_node.text().strip()
            if in_stock_size:
                sizes.append(in_stock_size)

        for out_of_size in pq('ul.product-size li.unselectable a').items():
            out_size = out_of_size.text().strip() + ' - out of stock'
            if out_size:
                sizes.append(out_size)

        # 商品介绍
        introduction, details = None, None
        for text in pq('.product-tabs ul.tabs-menu li').items():
            tab = text('a.tab').text().strip()
            if tab == 'Voir tous les avis':
                continue
            elif tab == 'Description':
                introduction = text('.container').text().strip()
            elif tab == 'Matières & Conseils':
                details = text('.container').text().strip()
            else:
                break

        # 商品库存
        stock = 999

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'discount': discount, 'colors': colors,
            'color_urls': color_urls, 'sizes': sizes, 'introduction': introduction, 'details': details, 'stock': stock,
            'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id,
            'coin_id': self.coin_id

        }
