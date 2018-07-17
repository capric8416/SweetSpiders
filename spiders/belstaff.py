# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class BelstaffCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.belstaff.co.uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(BelstaffCrawler, self).__init__()

        # 商品店铺
        self.store = "Belstaff"

        # 商品品牌
        self.brand = "Belstaff"

        # 店铺ID
        self.store_id = 353

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 328

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        cat1_node = pq('.navigation-wrapper .level-1-list li.level-1-item')
        for top in cat1_node.items():
            cat1_name = top('a.level-1-link').text().strip()
            if cat1_name == 'Pure Motorcycle':
                break
            elif cat1_name == 'Kids':
                cat1_url = self._full_url(url_from=resp.url, path=top('a.level-1-link').attr('href'))
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}
                cat2_name = 'clothing'
                cat2_url = cat1_url
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }
                cat3_name = 'casual'
                cat3_url = cat1_url

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
            else:
                cat1_url = self._full_url(url_from=resp.url, path=top('a.level-1-link').attr('href'))
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

                cat2_node = top('.level-2-wrapper .level-2-list > li.level-2-item:gt(1) .level-2-link')
                for cat_2 in cat2_node.items():
                    cat2_name = cat_2.text().strip()
                    if cat2_name in ('Bestsellers', 'New Arrivals'):
                        break
                    cat2_url = self._full_url(url_from=resp.url, path=cat_2.attr('href'))

                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }

                    cat3_node = cat_2.next('.level-3-wrapper .level-3-list .level-3-item:gt(1)')
                    if not cat3_node:
                        continue
                    else:
                        for cat_3 in cat3_node.items():
                            cat3_name = cat_3.children('a').text().strip()
                            if 'View All' in cat3_name:
                                break
                            cat3_url = self._full_url(url_from=resp.url, path=cat_3.children('a').attr('href'))

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
        params = {}
        count = 24
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

            next_page = pq('li.infinite-scroll-placeholder').attr('data-grid-url').split('?')[0]
            count += 24
            params.update({'psortd1': 1, 'amp;psortb1': 'bestMatch', 'amp;sz': 24, 'amp;start': count,
                           'amp;format': 'page-element'})
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#product-search-result-items li.js-grid-tile')
        if node:
            for detail in node.items():
                url = self._full_url(url_from=resp.url,
                                     path=detail('.js-product-image .js-producttile_link').attr('href'))
                if url:
                    meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
                    yield url, headers, resp.cookies.get_dict(), meta
        else:
            node = pq('.slick-list .slick-track .slick-slide')
            for detail in node.items():
                url = self._full_url(url_from=resp.url,
                                     path=detail('.js-product-image .js-producttile_link').attr('href'))
                if url:
                    meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
                    yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img in pq('#thumbnails .thumb').items():
            img_url = img('img').attr('src').replace('sw=158', 'sw=711').replace('sh=158', 'sh=907')
            images.append(img_url)

        # 商品名称
        name = pq('#product-content .product-name').text().strip()

        # 商品价格
        price = pq('.product-price .text-uppercase').text().strip().split()[-1]

        # 商品颜色
        color = pq('.product-variations .attribute-color .color-name').text().strip()

        # 商品尺码
        sizes = []
        for size_node in pq('.product-variations .attribute-size .size-select option').items():
            size = size_node.text().strip()
            sizes.append(size)
        sizes = sizes[1:]

        # 商品详情介绍
        introduction = [p.text().strip() for p in pq('.js-read-more-less-wrapper .js-full-content p').items()]

        # 商品说明
        description = pq('.js-panel-wrapper .js-panel #tab_details_and_care').text().strip()

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'price': price, 'color': color, 'sizes': sizes, 'introduction': introduction,
            'description': description, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
