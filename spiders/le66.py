# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class Le66Crawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.le66.fr/fr/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(Le66Crawler, self).__init__()

        # 商品店铺
        self.store = "Le66"

        # 商品品牌
        self.brand = "Le66"

        # 店铺ID
        self.store_id = 1866

        # 品牌ID
        self.brand_id = '暂无'

        # 货币ID
        self.coin_id = 3

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []
        cat1_name = pq('li:contains("FEMME")').children('a').text().strip()
        cat1_url = pq('li:contains("FEMME")').children('a').attr('href')

        cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

        cat2_nodes = pq('li:contains("FEMME")').children('ul.test li a')
        for cat2_node in cat2_nodes.items():
            cat2_name = cat2_node.text().strip()
            cat2_url = cat2_node.attr('href')

            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url

            if cat2_name:
                cat1['children'].append({
                    'name': cat2_name, 'url': cat2_url,
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                })

                results.append([
                    cat2_url, headers, resp.cookies.get_dict(),
                    {'categories': [(cat1_name, cat1_url),
                                    (cat2_name, cat2_url)]}
                ])

        categories.append(cat1)

        cat1_name = pq('li:contains("HOMME")').children('a').text().strip().split()[0]
        cat1_url = pq('li:contains("HOMME")').children('a').attr('href')

        cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

        cat2_nodes = pq('li:contains("HOMME")').children('ul.test li a')
        for cat2_node in cat2_nodes.items():
            cat2_name = cat2_node.text().strip()
            cat2_url = cat2_node.attr('href')

            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url
            if cat2_name:
                cat1['children'].append({
                    'name': cat2_name, 'url': cat2_url,
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                })

                results.append([
                    cat2_url, headers, resp.cookies.get_dict(),
                    {'categories': [(cat1_name, cat1_url),
                                    (cat2_name, cat2_url)]}
                ])

        categories.append(cat1)

        cat1_name = pq('li:contains("DRUGSTORE")').children('a').text().strip()
        cat1_url = pq('li:contains("DRUGSTORE")').children('a').attr('href')

        cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

        cat2_nodes = pq('li:contains("DRUGSTORE")').children('ul.test li a')
        for cat2_node in cat2_nodes.items():
            cat2_name = cat2_node.text().strip()
            cat2_url = cat2_node.attr('href')

            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url

            if cat2_name:
                cat1['children'].append({
                    'name': cat2_name, 'url': cat2_url,
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                })

                results.append([
                    cat2_url, headers, resp.cookies.get_dict(),
                    {'categories': [(cat1_name, cat1_url),
                                    (cat2_name, cat2_url)]}
                ])

        categories.append(cat1)

        cat1_name = PyQuery(pq('a:contains("Designers")')[2]).text().strip()
        cat1_url = self._full_url(url_from=resp.url, path=PyQuery(pq('a:contains("Designers")')[2]).attr('href'))

        cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

        cat2_nodes = pq('a:contains("Designers")').next('ul li a')
        for cat2_node in cat2_nodes.items():
            cat2_name = cat2_node.text().strip()
            cat2_url = cat2_node.attr('href')

            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url
            if cat2_name:
                cat1['children'].append({
                    'name': cat2_name, 'url': cat2_url,
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                })

                results.append([
                    cat2_url, headers, resp.cookies.get_dict(),
                    {'categories': [(cat1_name, cat1_url),
                                    (cat2_name, cat2_url)]}
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

            next_page = self._full_url(url_from=resp.url, path=pq('#pagination_next a').attr('href'))
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#center_column ul.product_list li.ajax_block_product')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.product-container .right-block .product-name').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.partition('.')[0].split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        if resp.status_code != 200:
            resp = self._request(url=url, headers=extra['headers'], cookies=extra['cookies'])
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#center_column .primary_block img').items():
            img_url = img_node.attr('src')
            if 'large_default' in img_url:
                images.append(img_url.replace('large_default', 'thickbox_default'))

        # 商品名称
        name = pq('#center_column .pb-center-column .manufacturer-name').text().strip()
        brand_name = pq('#center_column .pb-center-column .product-brand').text().strip()
        name = name + ': ' + brand_name

        # 商品副标题
        caption = pq('#center_column .pb-center-column .reference').text().strip()

        # 商品价格
        was_price = pq('#old_price_display .price').text().strip()
        now_price = pq('#our_price_display').text().strip()

        # 商品折扣
        discount = pq('#reduction_percent_display').text().strip()

        # 商品颜色
        colors = []
        for color_node in pq('ul.cross-couleur li.cross-couleur-item img').items():
            color_url = color_node.attr('src')
            if color_url:
                colors.append(color_url)

        # 商品介绍
        introduction_title = pq('#center_column h1').text().strip()
        introduction_content = pq('#description_content').text().strip()
        introduction = introduction_title + introduction_content

        # 商品尺寸
        sizes = []
        for size_node in pq('#group_1 option').items():
            size = size_node.text().strip()
            if size != 'Choisissez votre taille':
                sizes.append(size)

        # 商品库存
        stock = 999
        if sizes:
            value = [each.endswith('Epuisé') for each in sizes]
            if all(value):
                stock = 0
            else:
                stock = 999

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'caption': caption, 'was_price': was_price, 'now_price': now_price, 'discount': discount,
            'colors': colors, 'introduction': introduction, 'sizes': sizes, 'stock': stock, 'store': self.store,
            'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
