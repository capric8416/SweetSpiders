# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class ArgosCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.argos.co.uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(ArgosCrawler, self).__init__()

        # 商品店铺
        self.store = "Argos"

        # 商品品牌
        self.brand = "Argos"

        # 店铺ID
        self.store_id = '暂无'

        # 品牌ID
        self.brand_id = '暂无'

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        results = []
        categories = []

        json_url = 'https://www.argos.co.uk/meganav.json'
        resp = self._request(url=json_url, headers=self.headers)
        json_data = resp.json()['body']['data']
        for cat1_node in json_data:
            cat1_name = cat1_node['title']
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node['link'])
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            for cat2_nodes in cat1_node['columns']:
                for cat2_node in cat2_nodes:
                    cat2_name = cat2_node.get('title')
                    cat2_url = self.INDEX_URL
                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }

                    for cat3_node in cat2_node['links']:
                        cat3_name = cat3_node.get('title')
                        cat3_url = self._full_url(url_from=resp.url, path=cat3_node.get('link'))

                        headers = copy.copy(self.headers)
                        headers['Referer'] = resp.url

                        cat2['children'].append({
                            'name': cat3_name, 'url': cat3_url,
                            'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                        })

                        results.append([
                            cat3_url, headers, resp.cookies.get_dict(),
                            {'categories': [(cat1_name, cat1_url),
                                            (cat2_name, cat2_url),
                                            (cat3_name, cat3_url)]}
                        ])

                    cat1['children'].append(cat2)

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
            if pq('li[data-el="pagination-next"] > a.pagination__link'):
                next_page = self._full_url(url_from=resp.url,
                                           path=pq('li[data-el="pagination-next"] > a.pagination__link').attr('href'))
                if next_page:
                    url = next_page
            else:
                break

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.product-list > .ac-product-card')
        if node.children('a.ac-product-card__details'):
            for detail in node.items():
                url = self._full_url(url_from=resp.url, path=detail.children('a.ac-product-card__details').attr('href'))
                if url:
                    meta['product_id'] = urlparse(url).path.split('/')[-1]
                    yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('ul.media-player-thumbnails-list > li img').items():
            img_url = self._full_url(url_from=resp.url,
                                     path=img_node.attr('src'))
            if 'TuClothingThumb80' in img_url:
                img_url = img_url.replace('TuClothingThumb80', 'ClothingPDP570')
            if 'DefaultThumb50' in img_url:
                img_url = img_url.replace('DefaultThumb50', 'DefaultPDP570')
            if 'Video' in img_url:
                continue
            if img_url:
                images.append(img_url)

        # 商品名称
        if pq('div.product-name h1.product-name-main .tuclothing-product-title'):
            name = pq('div.product-name h1.product-name-main .tuclothing-product-title').text().strip()
        else:
            name = pq('div.product-name h1.product-name-main .product-title').text().strip()

        # 商品价格
        was_price = pq('ul.product-price-wrap li.price-align .price-was').text().strip()
        now_price = pq('ul.product-price-wrap li.price').text().strip().strip('*')
        if not (was_price and now_price):
            now_price = pq('ul.product-price-wrap li.price').text().strip()

        # 商品描述
        introduction = pq('#product-description .product-description-content-text').text().replace('\n', '')

        # 商品尺寸
        sizes = []
        for size_node in pq('.tiled-size-picker__box > div > button').items():
            size = size_node.text().strip()
            if size:
                sizes.append(size)

        # 商品库存
        stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
                'sizes': sizes, 'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
                'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
