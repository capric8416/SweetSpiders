# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import re
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery

from common.translate import GoogleTranslate


class KabiriCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.kabiri.co.uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(KabiriCrawler, self).__init__()

        # 商品店铺
        self.store = "Kabiri"

        # 商品品牌
        self.brand = "Kabiri"

        # 店铺ID
        self.store_id = 13214

        # 品牌ID
        self.brand_id = 138

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        g = GoogleTranslate()
        results = []
        categories = []

        tops = pq('#nav li.level0')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name == 'Designers':
                continue
            if cat1_name == 'The Journal':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
            cat1 = {'name': cat1_name, 'name_cn': g.query(source=cat1_name), 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('div.level0 table ul > li.level1')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('a').text().strip()
                if cat2_name == 'View All':
                    continue
                if cat2_name == 'New In On The Journal':
                    break
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node.children('a').attr('href'))

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url

                cat1['children'].append({
                    'name': cat2_name, 'name_cn': g.query(source=cat2_name), 'url': cat2_url,
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                })

                results.append([
                    cat2_url, headers, resp.cookies.get_dict(),
                    {'categories': [(cat1_name, g.query(source=cat1_name), cat1_url),
                                    (cat2_name, g.query(source=cat2_name), cat2_url)]}
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

            next_page = self._full_url(url_from=resp.url, path=pq('.sub-pagenation .pages li.next a').attr('href'))
            if not next_page or (resp.url == next_page.replace('http', 'https')):
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.page .main .col-main .category-products .products-list .item')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail.children('a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1].partition('.')[0]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        if len(pq('#image-wrapper .more-views li a')) > 1:
            for img_node in pq('#image-wrapper .more-views li a').items():
                img_str = img_node.attr('rel')
                img_url = re.search(r'largeimage: \'(.*)\'', img_str.split(',')[-1]).group(1)
                if img_url:
                    images.append(img_url)
        elif not pq('#image-wrapper .more-views li a'):
            img = pq('#main-image .product-image-zoom').attr('href')
            images.append(img)
        else:
            img_str = pq('#image-wrapper .more-views li a').attr('rel')
            img_url = re.search(r'largeimage: \'(.*)\'', img_str.split(',')[-1]).group(1)
            img = pq('#main-image .product-image-zoom').attr('href')
            if img_url.split('/')[-1] == img.split('/')[-1]:
                images.append(img)
            else:
                images.append(img_url)
                images.append(img)

        # 商品名称
        name = pq('.product-view .product-essential .product-info h1').text().strip()

        # 商品价格
        now_price = pq('.product-view .product-essential .product-info .price-box .price').text().strip()

        # 商品介绍
        introduction = pq('.product-view .product-essential .product-info .tab-content .description').text().strip()

        # 商品详情
        details = pq('.product-view .product-essential .product-info .tab-content .designer-info').text().strip()

        # 商品库存
        stock = 0
        stock_text = pq('.product-view .product-info p.availability .in-stock').text().strip()
        if stock_text == 'In stock':
            stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'now_price': now_price, 'introduction': introduction, 'details': details, 'stock': stock,
                'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id,
                'coin_id': self.coin_id
                }
