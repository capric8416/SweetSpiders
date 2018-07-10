# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class GrensonCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.grenson.com/uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(GrensonCrawler, self).__init__()

        # 商品店铺
        self.store = "Grenson"

        # 商品品牌
        self.brand = "Grenson"

        # 店铺ID
        self.store_id = 710

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 116

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('.only-menu .nav-container #nav li:eq(0)')
        cat1_name = top('a').text().strip()
        cat1_url = self.INDEX_URL
        cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}
        child = pq('.only-menu .megamenu .shop ul li.level0')
        for child_node in child.items():
            cat2_name = child_node('a.level-top').text().strip()
            if cat2_name == 'Projects':
                break
            cat2_url = child_node('a.level-top').attr('href')
            cat2 = {
                'name': cat2_name, 'url': cat2_url, 'children': [],
                'uuid': self.cu.get_or_create(cat1_name, cat2_name)
            }
            cat3_nodes = child_node('ul.level0 li.level1')
            for cat3_node in cat3_nodes.items():
                cat3_name = cat3_node('a span').text().strip()
                if 'Fragrances' in cat3_name:
                    continue
                if 'All' in cat3_name:
                    break
                cat3_url = cat3_node('a').attr('href')

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
                url=url, headers=headers, cookies=cookies,
                rollback=self.push_category_info, meta=meta)
            if not resp:
                return
            pq = PyQuery(resp.text)
            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url, path=pq('link[rel="next"]').attr('href'))
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.category-products .small-block-grid-2 .item')

        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.product-spec .product-name a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""
        _ = self
        pq = PyQuery(resp.text)
        if "Something's gone missing" in pq('.std .not-found .page-title h1').text().strip():
            return

        # 商品图片
        images = []
        for img in pq('.product-shop .product-img-box .gallery div').items():
            img_url = img('img').attr('src')
            images.append(img_url)

        # 商品名称
        name = pq('.product-section-right .product-right-inner .product-name h1').text().strip()

        # 商品价格
        was_price = pq('.product-right-inner .price-box .old-price').text().strip()

        now_price = pq('.product-right-inner .price-box .special-price').text().strip()
        if not (was_price and now_price):
            now_price = pq('.product-right-inner .product-section .price-box .regular-price').text().strip()

        # 商品介绍
        introduction = pq('.product-section .product-attr span').text().strip()

        # 商品尺码
        sizes = []
        resp = self._request(url=url, method='post', headers=extra['headers'], cookies=extra['cookies'],
                             data={'amfpc_ajax_blocks': 'product.info.options.wrapper'})

        text = resp.text
        pq = PyQuery(text)
        if pq('ul.category-quickview-options'):
            for size_node in pq('ul.category-quickview-options li.no-stock').items():
                size = size_node.text().strip() + '-' + 'no-stock'
                sizes.append(size)
            for size_node in pq('ul.category-quickview-options li[class!="no-stock"]').items():
                size = size_node.text().strip()
                sizes.append(size)
        else:
            sizes = sizes

        # 商品描述
        p1 = pq('.product-tabs .tabs-content #details .std').text().strip()
        description1 = 'Overview' + p1
        p2 = pq('.tabs-content #care .std').text().strip()
        description2 = 'Care' + p2
        description = description1 + ';' + description2

        # 商品尺寸对应表
        if pq('.tabs-content #sizefit'):
            size_guide_title = pq('.tabs-content #sizefit .std .product-table h5:eq(0)').text().strip()
            size_guide_1 = []
            size_fit = pq('.tabs-content #sizefit .std .product-table .rwd-table:eq(0) tbody tr')
            for standard in size_fit.items():
                fit = standard.text().strip()
                size_guide_1.append(fit)
            size_guide_title_2 = pq('.tabs-content #sizefit .std .product-table h5:eq(1)').text().strip()
            size_guide_2 = []
            size_fit_2 = pq('.tabs-content #sizefit .std .product-table .rwd-table:eq(1) tbody tr')
            for stands in size_fit_2.items():
                fits = stands.text().strip()
                size_guide_2.append(fits)
            guide_text = pq('.fitting-guide p').text().strip()
            size_guide = {'size_guide_title': size_guide_title, 'size_guide_1': size_guide_1,
                          'size_guide_title_2': size_guide_title_2,
                          'size_guide_2': size_guide_2, 'guide_text': guide_text}
        else:
            size_guide = {}

        # 商品库存
        stock_text = pq('.out-of-stock p').text().strip()
        if stock_text:
            stock = 0
        else:
            stock = 999

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
            'sizes': sizes, 'description': description, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id, 'size_guide': size_guide,
            'stock': stock
        }
