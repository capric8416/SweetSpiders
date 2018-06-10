# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class CrabtreeCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'http://www.crabtree-evelyn.com/uk/en'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(CrabtreeCrawler, self).__init__()

        # 商品店铺
        self.store = "Crabtree & Evelyn"

        # 商品品牌
        self.brand = "Crabtree & Evelyn"

        # 店铺ID
        self.store_id = 541

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 270

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('.accordion-topmenu:eq(1) .sub-level .menu-vertical .accordion-submenus')
        for top_node in top.items():
            cat1_name = top_node('a.accordion-submenu-toggle').text().strip()
            if cat1_name == 'Fragrance':
                continue
            elif cat1_name == 'Collection Rituals':
                break
            elif cat1_name in ('Hair Care', "Men's", 'Gifts'):
                cat1_url = top_node('a.accordion-submenu-toggle').attr('href').strip()

                cat1 = {'name': cat1_name, 'url': cat1_url, 'uuid': self.cu.get_or_create(cat1_name)}

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                cookies = resp.cookies.get_dict()

                results.append([
                    cat1_url, headers, cookies,
                    {'categories': [(cat1_name, cat1_url)]}
                ])

                categories.append(cat1)

            else:
                cat1_url = top_node('a.accordion-submenu-toggle').attr('href').strip()
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}
                child = top_node('ul.level-3 .accordion-childmenu-label')
                for child_node in child.items():
                    cat2_name = child_node('a.sliding-u-click').text().strip()
                    cat2_url = child_node('a.sliding-u-click').attr('href').strip()

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url
                    cookies = resp.cookies.get_dict()

                    cat1['children'].append({
                        'name': cat2_name, 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.extend([
                        [
                            cat1_url, headers, cookies,
                            {'categories': [(cat1_name, cat1_url)]}
                        ],
                        [
                            cat2_url, headers, cookies,
                            {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url)]}
                        ]
                    ])

                categories.append(cat1)

        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""
        # http://www.crabtree-evelyn.com/uk/en/body-care/bath-soaks/?sz=12&start=0&format=page-element
        start = 0
        sz = 12
        format = 'page-element'
        params = {'sz': sz, 'start': start, 'format': format}
        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies, params=params,
                rollback=self.push_category_info, meta=meta
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            if not pq('.infinite-scroll-placeholder').attr('data-grid-url'):
                break

            start += 12
            params.update({'start': start})

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.product-tile-wrapper')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail(
                '.product-info .product-list-item .product-name .name-link').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        imgs = []
        for img in pq('.product-primary-image .pdp-image-slides > div img').items():
            img_url = img.attr('src')
            imgs.append(img_url)
        imgs = imgs[:-1]

        # 商品名称
        name = pq('.cols .product-detail .product-name').text().strip()

        # 商品原价
        was_price = pq('.product-content .product-price-amount .price-standard').text().strip()

        # 商品现价
        now_price = pq('.product-content .product-price .price-sales-pinned').text().strip()
        if not (was_price and now_price):
            now_price = pq('.product-content .product-price .price-sales').text().strip()

        # 商品介绍
        introduction = pq('.product-content .short-description p').text().strip()

        # 商品描述
        p1 = pq('.cae__container .cae__explore-further-content .cae__h2').text().strip()
        p2 = pq('.cae__container .cae__explore-further-content .cae__content').text().strip()
        p3 = pq('.cae__hidden-mobile .cae__h4').text().strip()
        p4 = pq('.cae__container .cae__hidden-mobile .cae__explore-further-usage .cae__content').text().strip()
        description = p1 + p2 + p3 + p4

        # 商品尺寸
        size = pq('.product-variations .attribute .value .selection .select2-selection .select2-selection__rendered').text().strip()
        if not size:
            size = pq('.product-variations .attribute .value input').attr('value')

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': imgs,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
            'description': description, 'size': size, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
