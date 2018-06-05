# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class LushCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'http://www.lush.co.uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(LushCrawler, self).__init__()

        # 商品店铺
        self.store = "Lush"

        # 商品品牌
        self.brand = "Lush"

        # 店铺ID
        self.store_id = 83

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 437

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        cat1_name = pq('ul.header-products-contents li.has-children a').text().strip()
        cat1_url = self._full_url(url_from=resp.url,
                                  path=pq('ul.header-products-contents li.has-children a').attr('href'))
        cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}
        child_node = pq('.container .container-padding ul.children li.header-menu-products-category-item')
        for cat2 in child_node.items():
            cat = cat2('p').text().strip()
            if cat == 'New':
                continue
            if cat == 'Fragrances':
                continue
            child_node = cat2('ul.children2nd li.leaf')
            for child in child_node.items():
                cat2_name = child('a').text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=child('a').attr('href'))

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
                rollback=self.push_category_info, meta=meta
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = pq('.next').attr('href')
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.container .search-results-wrapper div.node-add-to-basket')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.product-module-product-image a').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        img = pq('.whiteboard .whiteboard-table .flag__image .object-commerce-image-inner-inner img').attr('src')

        # 商品名称
        name = pq('.object-commerce-detail .whiteboard-table h1.product-title').text().strip()

        # 商品价格及规格
        price = pq('.object-commerce-product #edit-product-id--2 option').text().strip()

        # 商品描述
        introduction = [p.text().strip() for p in pq('#main_column .textformat p').items()]

        # 商品介绍
        description = []
        for p in pq('.object-ingredients-right-wrapper .normal li').items():
            p_text = p('a').text().strip()
            description.append(p_text)

        # 商品材料
        meterials = []
        meterial_node = pq('.object-ingredients .object-ingredients-left .break-2-grid-1 .object-ingredient-text ')
        for meterial in meterial_node.items():
            meterial_text_1 = meterial('.object-ingredient-title').text().strip()
            meterial_text_2 = meterial('.object-ingredient-description').text().strip()
            meterial_text = meterial_text_1 + ',' + meterial_text_2
            meterials.append(meterial_text)

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'img': img,
            'name': name, 'price': price, 'introduction': introduction, 'description': description,
            'meterials': meterials, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'coin_id': self.coin_id
        }
