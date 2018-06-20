# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy
from urllib.parse import urlparse


class AstleyclarkeCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.astleyclarke.com/uk'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(AstleyclarkeCrawler, self).__init__()

        # 商品店铺
        self.store = "Astley Clarke"

        # 商品品牌
        self.brand = "Astley Clarke"

        # 店铺ID
        self.store_id = 1637

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 309

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('#header_main_wrapper #pronav li.parent:gt(1)')
        for cat1_node in top.items():
            cat1_name = cat1_node('a:eq(0)').text().strip()
            if cat1_name == 'SALE':
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node('a:eq(0)').attr('href'))
                cat1 = {'name': cat1_name, 'url': cat1_url, 'uuid': self.cu.get_or_create(cat1_name)}
                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url

                results.append([
                    cat1_url, headers, resp.cookies.get_dict(),
                    {'categories': [(cat1_name, cat1_url)]}
                ])

                categories.append(cat1)
            elif cat1_name == 'New In':
                continue
            elif cat1_name == 'Explore':
                break
            else:
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node('a:eq(0)').attr('href'))
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

                child = cat1_node('.sub .pronav-reskin > ul > li')
                for cat2_node in child.items():
                    cat2_name = cat2_node('a:eq(0)').text().strip()
                    if cat2_name in ('See All Jewellery', 'Gift Wrap'):
                        break
                    if cat2_name in ('Gift Cards', 'Gift Finder', ''):
                        continue
                    cat2_url = self._full_url(url_from=resp.url, path=cat2_node('a:eq(0)').attr('href'))

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat1['children'].append({
                        'name': cat2_name, 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.append([
                        cat2_url, headers, resp.cookies.get_dict(),
                        {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url)]}
                    ])

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
            if len(pq('.category-products ul.products-grid li.item')) < 48:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.category-products ul.products-grid li.item')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.product-name a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#main-image-wrapper .slick-list .slick-track li.slick-slide').items():
            img_url = self._full_url(url_from=resp.url, path=img_node('a').attr('href'))
            images.append(img_url)
        images = list(set(images))

        # 商品名称
        name = pq('.product-right .name-and-sku h1').text().strip()

        # 商品价格
        was_price = pq('.product-right .price .price-box .old-price span').text().strip()

        now_price = pq('.product-right .price .price-box .special-price span').text().strip()

        if not (was_price and now_price):
            now_price = pq('.product-right .price .price-box .regular-price span.price').text().strip()

        # 商品介绍
        introduction1 = pq('.product-right .description .std .prodcopy p').text().strip()
        introduction2 = [li.text().strip() for li in pq('.product-right .description .std .prodcopy .bullets li').items()]

        introduction = introduction1 + ';' + ''.join(introduction2)

        # 商品尺码
        sizes = []
        # 获取售罄尺码
        if pq('.product-right #product-options-wrapper #option-buttons-container div'):
            for size_out in pq('.product-right #product-options-wrapper #option-buttons-container div').items():
                sizes_out = size_out.text().strip() + 'Out of Stock'
                sizes.append(sizes_out)
        # 获取有库存尺码
        if pq('.product-right #product-options-wrapper #option-buttons-container a'):
            for size_in in pq('.product-right #product-options-wrapper #option-buttons-container a').items():
                sizes_in = size_in.text().strip() + 'In Stock'
                sizes.append(sizes_in)

        # 商品颜色
        colors = []
        for color_node in pq('.product-right .product-swatches > li').items():
            color = color_node('a').text().strip()
            colors.append(color)

        # 商品描述
        details = pq('.product-bottom #product-attribute-specs-table tbody').text().strip()

        # 尺寸指导
        size_guide

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
            'sizes': sizes, 'colors': colors, 'details': details, 'size_guide': size_guide, 'store': self.store,
            'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }



