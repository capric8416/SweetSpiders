# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class BrownsfashionCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.brownsfashion.com/uk/woman'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(BrownsfashionCrawler, self).__init__()

        # 商品店铺
        self.store = "Browns Fashion"

        # 商品品牌
        self.brand = "Browns Fashion"

        # 店铺ID
        self.store_id = 1006

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 258

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('ul[role="menubar"] > [role="menuitem"]')
        for cat1_node in top.items():
            cat1_name = cat1_node.children('a').text().strip()
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))

            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            for child in cat1_node.children('ul[role="menu"]').children('li[role="presentation"]').items():
                cat2_name = child('a:eq(0)').text().strip()
                if cat2_name in ('New In', 'Designers'):
                    continue
                if cat2_name == 'Features':
                    break
                cat2_url = self._full_url(url_from=resp.url, path=child('a:eq(0)').attr('href'))

                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                for child3 in child.children('ul[role="menu"]').children('li[role="menuitem"]').children(
                        'ul[role="menu"]').children('li[role="presentation"]').children('a').items():
                    cat3_name = child3.text().strip()
                    if cat3_name in ('Balenciaga', 'Adidas Originals'):
                        break
                    if cat2_name != 'Sale' and 'All' in cat3_name:
                        continue
                    cat3_url = self._full_url(url_from=resp.url, path=child3.attr('href'))

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

        node = pq('#listingProductsWall article')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('a.collection-item__link').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq(
                '.js-body-wrapper main .product__responsiveLayoutWrapper .product__responsiveLayout meta').items():
            img_url = img_node.attr('content')
            images.append(img_url)

        # 商品名称
        name = pq(
            '.js-body-wrapper main .product__responsiveLayoutWrapper .product__responsiveLayout .product__responsiveLayoutBox:eq(0) h1.product__title').text().strip()

        # 商品标题
        caption = pq(
            '.js-body-wrapper main .product__responsiveLayoutWrapper .product__responsiveLayout .product__responsiveLayoutBox:eq(0) h1.product__title span.product__name').text().strip()

        # 商品价格
        was_price = pq('.product__responsiveLayout .product__responsiveLayoutBox:eq(0) .product__priceAndLowStock .product__price--discount').text().strip()

        now_price = pq('.product__responsiveLayout .product__responsiveLayoutBox:eq(0) .product__priceAndLowStock .product__price--discount-new').text().strip().split()[0]

        if not (was_price and now_price):
            now_price = pq('.product__responsiveLayout .product__responsiveLayoutBox:eq(0) .product__priceAndLowStock .product__price').text().strip()

        # 商品介绍
        introduction = pq('#Description .product__descriptionValue p').text().strip()

        # 商品尺寸
        sizes = []
        current_size = pq('.product__responsiveLayoutBox:eq(1) .product__descriptionBoxContent #js-product-size').text().strip()
        for size_node in pq('.product__responsiveLayoutBox:eq(1) .product__descriptionBoxContent .form__field .dropdown .dropdown-menu li').items():
            size = size_node('a').text().strip()
            sizes.append(size)

        # 商品颜色
        colors = []
        for color_node in pq('.product__responsiveLayoutBox:eq(1) .product__colorWrapper .color-swatch .color-link').items():
            color_url = self._full_url(url_from=resp.url, path=color_node('img').attr('src'))
            colors.append(color_url)

        # 商品尺寸相关
        p_text = []
        for p in pq('#SizeFit .product__descriptionValue p').items():
            text = p.text().strip()
            p_text.append(text)
        size_and_fit = ';'.join(p_text)

        area_size = []
        for area_node in pq('.sizeGuideModal__table .pinned .sizeGuideModal__column .sizeGuideModal__cell').items():
            area = area_node.text().strip()
            area_size.append(area)

        size_guide, each_sizes = [], []
        for size in pq('.sizeGuideModal .sizeGuideModal__guide .sizeGuideModal__table .scrollable .scrollable-container .sizeGuideModal__column').items():
            for each_size in size('.sizeGuideModal__cell').items():
                size_each = each_size.text().strip()
                each_sizes.append(size_each)
            size_guide.append(each_sizes)

        # 商品描述
        detail = pq('#materials .product__descriptionValue p').text().strip()

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'caption': caption, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
            'sizes': sizes, 'colors': colors, 'sizefit': size_and_fit, 'areasize': area_size, 'sizeguide': size_guide,
            'detail': detail, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id,
            'coin_id': self.coin_id
        }

