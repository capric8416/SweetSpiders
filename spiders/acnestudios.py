# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class AcnestudiosCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.acnestudios.com/hk/en/home'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(AcnestudiosCrawler, self).__init__()

        # 商品店铺
        self.store = "Acne Studios"

        # 商品品牌
        self.brand = "Acne Studios"

        # 店铺ID
        self.store_id = 205

        # 品牌ID
        self.brand_id = '暂无'

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('#navigation ul.header__menu > li.header__menu-item')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name == 'Blå Konst Denim':
                break
            cat1_url = cat1_node.children('a').attr('href')
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('div.header__submenu-container > ul > li.header__submenu-item')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('a .catname:eq(0)').text().strip()
                if not cat2_name:
                    continue
                cat2_url = cat2_node.children('a').attr('href')
                if not cat2_node.children('ul.level-3'):
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


                else:
                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }

                    cat3_nodes = cat2_node.children('ul.level-3 > li.header__submenu-item')
                    for cat3_node in cat3_nodes.items():
                        cat3_name = cat3_node.children('a .catname:eq(0)').text().strip()
                        cat3_url = cat3_node.children('a').attr('href')

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

            next_page = self._full_url(url_from=resp.url,
                                       path=pq('li.infinite-scroll-placeholder').attr('data-grid-url'))
            if (not next_page) or (next_page == resp.url):
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('li.product-list__item-tile')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.product-tile .product-info .product-name a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.partition('.')[0].split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('.pdp-item-wrapper .product-item__gallery-container .image-container').items():
            img_url = self._full_url(url_from=resp.url, path=img_node('img').attr('data-zoom-src'))
            if img_url:
                images.append(img_url)

        # 商品名称
        name = pq('#product-content .product-info-wrapper .product-name').text().strip()

        # 商品价格
        now_price = pq('#product-content .product-info-wrapper .product-price').text().strip()

        # 商品副标题
        caption = pq('.product-item__core-information .product-item__detail-info-description').text().strip()

        # 商品颜色，商品颜色是样式写的图片
        colors = []
        for color_style in pq('.color:eq(0) a .swatch-hex').items():
            color = color_style.attr('style')
            if color:
                colors.append(color)

        # 商品尺寸
        sizes = []
        for size_node in pq('#va-size option').items():
            size = size_node.text().strip()
            if 'size' not in size:
                if '\xa0\xa0' in size:
                    size = size.replace('\xa0\xa0', '--')
                    sizes.append(size)
                else:
                    sizes.append(size)

        # 商品介绍
        introduction = pq('.product-item__detail-info-description .hide-for-small').text().strip()

        # 商品库存
        stock = 999

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'now_price': now_price, 'caption': caption, 'colors': colors, 'sizes': sizes,
            'introduction': introduction, 'stock': stock, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
