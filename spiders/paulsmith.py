# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse
import json
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class PaulsmithCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.paulsmith.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(PaulsmithCrawler, self).__init__()

        # 商品店铺
        self.store = "Paul Smith"

        # 商品品牌
        self.brand = "Paul Smith"

        # 店铺ID
        self.store_id = 347

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 411

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('.header-wrapper .mt-md-3 .shop-menu .shop-menu-item')
        for top_node in top.items():
            cat1_name = top_node('span').text().strip().partition('\n')[0]
            if cat1_name == 'New Arrivals':
                continue
            if cat1_name == 'Stories':
                break
            cat1_url = self.INDEX_URL
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}
            child = top_node('.shop-menu-dropdown .container .row .col-12')
            for child_node in child.items():
                cat2_name = child_node('.shop-menu-dropdown-title:eq(0)').text().strip()
                if child_node('.shop-menu-dropdown-image-wrapper'):
                    break
                cat2_url = cat1_url
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }
                child_3_node = child_node('.shop-menu-dropdown-wrapper:eq(0) a.shop-menu-dropdown-item')
                for cat3_node in child_3_node.items():
                    cat3_name = cat3_node.text().strip()
                    if 'All' in cat3_name:
                        continue
                    cat3_url = cat3_node('a.shop-menu-dropdown-item').attr('href')

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
        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies,
                rollback=self.push_category_info, meta=meta
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = pq('.bottom_toolbar .pages-item-next .page-link').attr('href')

            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.container .products .card')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.card-image-wrapper').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img in pq('.product-carousel img').items():
            img_url = self._full_url(url_from=resp.url, path=img.attr('src'))
            images.append(img_url)

        # 商品名称
        name = pq('.page-title-wrapper .page-title .base').text().strip()

        # 商品价格
        price = pq('.product-info-main .mb-4 .price-box .price-wrapper .price').text().strip()

        # 商品规格
        sizes = []
        data = json.loads(pq('script:contains("configurableQty")').text().strip())
        options = data['#product_addtocart_form']['configurable']['spConfig']['attributes']['250']['options']
        for option in options:
            size = option['label']
            oos = option['oos']
            if oos:
                size = size + '- Out of Stock'
            else:
                size = size
            sizes.append(size)


        # 商品颜色
        colors = []
        for color in pq('.product-info-main .products > .product-item .product-item-info').items():
            color_url = self._full_url(url_from=resp.url, path=color('img').attr('src'))
            colors.append(color_url)

        # 商品介绍
        p1 = pq('.bg-faded .cycle-tabs-content-wrapper .cycle-tabs-content:eq(0) .product .value').text().strip()
        p2 = pq('.bg-faded .detailed .cycle-tabs-content-wrapper .cycle-tabs-content:eq(0) .cycle-tabs-text').text().strip()
        introduction1 = 'Overview' + ':' + p1 + p2
        introduction2 = 'Info & Care' + ':' + pq(
            '.bg-faded .cycle-tabs-content-wrapper .cycle-tabs-content:eq(1) .value').text().strip()
        p3 = pq('.bg-faded .cycle-tabs-content-wrapper .cycle-tabs-content:eq(2) .value p').text().strip()
        if p3:
            introduction3 = 'Sizing' + ':' + p3
        else:
            introduction3 = ''
        introduction = introduction1 + introduction2 + introduction3

        # 商品库存
        stock_text = pq('#product-addtocart-button span').text().strip()
        if stock_text == 'Add to bag':
            stock = 999
        else:
            stock = 0

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'price': price, 'size': size, 'colors': colors, 'introduction': introduction,
            'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
