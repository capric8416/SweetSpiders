# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class TedbakerCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'http://www.tedbaker.com/uk'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(TedbakerCrawler, self).__init__()

        # 商品店铺
        self.store = "TED BAKER"

        # 商品品牌
        self.brand = "TED BAKER"

        # 店铺ID
        self.store_id = 514

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 405

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('#categories_nav li.js-root-category')
        for cat1_node in top.items():
            cat1_name = cat1_node('.categories_main .nav_header').text().strip()
            if cat1_name == 'Sale':
                continue
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node('.categories_main').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            child = cat1_node('.nav .nav_inner .nav_column .nav_header .js-menu-state')
            for child_node in child.items():
                cat2_name = child_node.text().strip()
                if cat2_name == 'New Arrivals':
                    continue
                if cat2_name == 'Gift Cards':
                    break
                if cat2_name == 'Home & Gifts':
                    cat2_url = self._full_url(url_from=resp.url,
                                              path=child_node.attr('href'))
                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }
                    resp = self._request(url=cat2_url, headers=self.headers)
                    pq = PyQuery(resp.text)
                    for cat3_node in pq('div.html_component:eq(2) .landing .inner .copy-pnl > div').items():
                        cat3_name = cat3_node('a.ul-cta').text().strip()
                        cat3_url = self._full_url(url_from=resp.url, path=cat3_node('a.ul-cta').attr('href'))

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

                else:
                    cat2_url = self._full_url(url_from=resp.url, path=child_node.attr('href'))

                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }
                    for cat3_node in cat1_node('.nav .nav_inner .nav_column > ul.nav_list > li.nav_item').items():
                        cat3_name = cat3_node('a.nav_link').text().strip()
                        if ('All' in cat3_name) or ('Home' in cat3_name):
                            continue
                        cat3_url = self._full_url(url_from=resp.url, path=cat3_node('a.nav_link').attr('href'))

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

            next_page = self._full_url(url_from=resp.url,
                                       path=pq('.foot .pagination .page_select .next a').attr('href'))
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.product_list_area .product_list .product-wrap')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail(
                'article.product div.selection .name a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        # 数量多了一倍
        images = []
        for img in pq('#product_images .carousel .viewport .slider div.image').items():
            img_url = img('a.image img').attr('src')
            images.append(img_url)

        # 商品名称
        title = pq('#product_head hgroup .name').text().strip()
        summary = pq('#product_head hgroup .summary').text().strip()
        name = title + summary

        # 商品价格
        was_price = pq('#product_head ul.pricing .previous del').text().strip()
        now_price = pq('#product_head ul.pricing .unit').text().strip()
        if not (was_price and now_price):
            now_price = pq('#product_head ul.pricing .price').text().strip()

        # 商品颜色
        colors = []
        for color_node in pq('#pdp_colour_swatch .value .colour_picker .colours li').items():
            color = color_node('a').text().strip()
            colors.append(color)

        # 商品尺寸
        # 没有获取到
        sizes = []
        if pq('.product_attr_selection .size .value #product_select_size option'):
            for size_node in pq('.product_attr_selection .size .value #product_select_size option').items():
                size = size_node.text().strip()
                sizes.append(size)
                sizes = sizes[1:]
        else:
            sizes = []

        # 商品介绍
        introduction = pq('#product_more .description').text().strip()

        # 商品描述
        details = pq('#product_details').text().strip()

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'colors': colors, 'sizes': sizes,
            'introduction': introduction, 'details': details, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
