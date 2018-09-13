# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class AmiparisCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.amiparis.com'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(AmiparisCrawler, self).__init__()

        # 商品店铺
        self.store = "AMI"

        # 商品品牌
        self.brand = "AMI"

        # 店铺ID
        self.store_id = 1805

        # 品牌ID
        self.brand_id = '暂无'

        # 货币ID
        self.coin_id = 3

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('#headerSideNavigation ul.nav-ul li.nav-li')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name == 'Fall Winter 18':
                continue
            if cat1_name == 'Stories':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))

            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('ul.navSub-ul li.navSub-li')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('a.navSub-a').text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node.children('a.navSub-a').attr('href'))

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url

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

            next_page = self._full_url(url_from=resp.url, path=pq('.next').attr('href'))
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#listingProductsWall .js-listing-wall-container .card-product-container')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.js-shopping-item .shopping-item__title a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_url in pq('.swiper-wrapper .productImage-thumbnails__list--item img').items():
            img = img_url.attr('data-src').replace('_170', '_1000')
            if img:
                images.append(img)

        # 商品名称
        name = pq('.product-right .product-description .product-title').text().strip()

        # 商品价格
        if pq('.product-right .js-product-price .product-price'):
            now_price = pq('.product-right .js-product-price .product-price').text().strip().split()[0]
        else:
            now_price = None

        # 商品颜色
        colors = []
        for color_node in pq('.color__wrapper .color__list .color__link img').items():
            color = color_node.attr('alt')
            if color:
                colors.append(color)

        # 商品颜色链接
        color_links = []
        for color_link in pq('.color__wrapper .color__list .color__link img').items():
            color_url = color_link.attr('data-src')
            if color_url:
                color_links.append(color_url)

        # 商品尺寸
        sizes = []
        if pq('.size__wrapper .size__list a'):
            for size_node in pq('.size__wrapper .size__list a').items():
                size = size_node.text().strip()
                if size:
                    sizes.append(size)
        else:
            size = pq('h6.one-size').text().strip()
            if size:
                sizes.append(size)

        # 商品介绍
        introduction = pq('#product_information_Advices').text().strip()

        # 商品细节
        description1 = pq('#product_information_SizeFit').text().strip()

        description2 = pq('#product_information_CareGuide').text().strip()

        description = description1 + ';' + description2

        # 商品库存
        out_stock = pq('.product-description .mt-40').text().strip()
        stock_text = pq('.product-description .outOfStock__detail').text().strip()
        if out_stock and stock_text:
            stock = 0
        else:
            stock = 999

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'now_price': now_price, 'colors': colors, 'color_links': color_links, 'sizes': sizes,
            'introduction': introduction, 'description': description, 'stock': stock, 'store': self.store,
            'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }

