# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import time
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery

from scripts.google_translate import GoogleTranslate


class HarrodsCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.harrods.com/en-gb'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    COOKIES = {'ctry': 'GB', 'curr': 'GBP'}

    def __init__(self):
        super(HarrodsCrawler, self).__init__()

        # 商品店铺
        self.store = "Harrods"

        # 商品品牌
        self.brand = "Harrods"

        # 店铺ID
        self.store_id = 1606

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 445

    def _parse_index(self, resp):
        """首页解析器"""
        g = GoogleTranslate()
        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('.nav .nav_container .nav_item')
        for cat1_node in top.items():
            cat1_name = cat1_node('.nav_link .nav_item-title').text().strip()
            if cat1_name in ('Designers', 'Sale'):
                continue
            if cat1_name == 'Gifts':
                break
            cat1_url = cat1_node('.nav_link').attr('href')

            cat1 = {'name': cat1_name, 'name_cn': g.query(source=cat1_name), 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            child = cat1_node('.nav_sub-menu-wrapper .nav_sub-menu-container ul.nav_sub-menu .nav_sub-menu-group')
            for cat2_node in child.items():
                cat2_name = cat2_node('.nav_sub-menu-title').text().strip()
                if cat2_name in ('Featured Brands',):
                    continue
                if cat2_name in ('Inspiration & Trends', 'Wine & Spirits', 'SALE', 'Style Edits'):
                    break
                cat2_url = cat1_url
                cat2 = {
                    'name': cat2_name, 'name_cn': g.query(source=cat2_name), 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }
                for cat3_node in cat2_node('.nav_sub-menu-list .nav_sub-menu-item').items():
                    cat3_name = cat3_node('.nav_sub-menu-link').text().strip()
                    if cat3_name == 'Just In':
                        continue
                    if 'All' in cat3_name:
                        continue
                    if 'Perfume' in cat3_name:
                        continue
                    if cat3_name in ("Men's Fragrance", "Men's Gift Sets", "Salon De Parfums"):
                        continue
                    if cat3_name in ('Diffusers', 'Harrods of London'):
                        break
                    cat3_url = cat3_node('.nav_sub-menu-link').attr('href')

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat2['children'].append({
                        'name': cat3_name, 'name_cn': g.query(source=cat3_name), 'url': cat3_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                    })

                    cookies = resp.cookies.get_dict()
                    cookies.update(self.cookies)
                    results.append([
                        cat3_url, headers, cookies,
                        {'categories': [(cat1_name, g.query(source=cat1_name), cat1_url),
                                        (cat2_name, g.query(source=cat2_name), cat2_url),
                                        (cat3_name, g.query(source=cat3_name), cat3_url)]}
                    ])

                cat1['children'].append(cat2)

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

            text = pq('.control_viewtypes .control_paging-list a.control_paging-item:last span').text().strip()
            if text == 'Next':
                next_page = self._full_url(url_from=resp.url, path=pq(
                    '.control_viewtypes .control_paging-list a.control_paging-item:last').attr('href'))

            else:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.grid .product-grid .product-grid_list .product-grid_item')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail('.product-card .product-card_info a.product-card_link').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1]
            cookies = resp.cookies.get_dict()
            cookies.update(self.cookies)
            yield url, headers, cookies, meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img in pq('.grid .pdp_images .pdp_images-container ul.pdp_images-list .pdp_images-item').items():
            img_url = self._full_url(url_from=resp.url, path=img('.pdp_images-image').attr('src'))
            images.append(img_url)
        images = list(set(images))

        # 商品标题
        title = pq(
            '.pdp_buying-controls .buying-controls .js-pdp-add-to-bag .buying-controls_details .buying-controls_brand span').text().strip()

        # 商品名称
        name = pq(
            '.pdp_buying-controls .buying-controls .js-pdp-add-to-bag .buying-controls_details .buying-controls_name').text().strip()

        # 商品价格
        was_price = pq(
            '.pdp_main .pdp_buying-controls .js-pdp-add-to-bag .buying-controls_price .price_group--was .price').text().strip()

        now_price = pq(
            '.pdp_main .pdp_buying-controls .js-pdp-add-to-bag .buying-controls_price .price_group--now .price').text().strip()

        if not (was_price and now_price):
            now_price = pq(
                '.pdp_main .pdp_buying-controls .js-pdp-add-to-bag .buying-controls_price .price').text().strip()

        # 商品默认颜色
        colors = []
        default_color = pq('.js-default-colour').attr('value')
        if default_color:
            colors.append(default_color)

        # 商品介绍
        details = [li.text().strip() for li in pq(
            '.pdp_details .product-info .product-info_section-1 .product-info_list li.product-info_item').items()]
        details = 'Details' + ':' + ''.join(details)
        overview = pq('.pdp_details .product-info_section-2 .product-info_content p').text().strip()
        overview = 'Overview' + ':' + overview
        introduction = details + ';' + overview

        # 商品库存
        stock = 999

        # 尺寸指导
        table1_name = pq('#international-sizing h2.tab_title').text().strip()
        table1 = []

        for size_tr in pq('#international-sizing .tab_content tr').items():
            size_each = size_tr.text().strip()
            table1.append(size_each)

        table2_name = pq('#uk-sizing').children('h2.tab_title').text().strip()
        inches_unit = 'Inches'
        inches_sizes = []

        for inches_tr in pq('#uk-sizing .tab_element:eq(0) tr').items():
            inches_size = inches_tr.text().strip()
            inches_sizes.append(inches_size)

        cm_unit = 'Centimetres'
        cm_sizes = []

        for size_tr in pq('#uk-sizing .tab_element:eq(1) tr').items():
            cm_size = size_tr.text().strip()
            cm_sizes.append(cm_size)

        size_guide = {
            'table1': {'table1_name': table1_name, 'table1': table1},
            'table2': {'table2_name': table2_name, 'inches_unit': inches_unit, 'inches_sizes': inches_sizes,
                       'cm_unit': cm_unit, 'cm_sizes': cm_sizes}
        }

        # 商品颜色和尺码
        sizes = []
        unique_code = urlparse(url).path.split('/')[-1].split('-')[-1]
        query = urlparse(url).query
        if query and ('colour' in query):
            size_url = 'https://www.harrods.com/en-gb/product/buyingcontrols/' + unique_code + '&' + query
        else:
            size_url = 'https://www.harrods.com/en-gb/product/buyingcontrols/' + unique_code
        params = {'_': int(time.time() * 1000), 'colour': default_color}
        resp = self._request(url=size_url, headers=extra['headers'], cookies=extra['cookies'], params=params)
        pq = PyQuery(resp.text)
        if pq('select.buying-controls_select--size option'):
            for size_node in pq('select.buying-controls_select--size option').items():
                size = size_node.text().strip()
                if size:
                    sizes.append(size)
        else:
            size = pq('.js-buying-controls_value--size').text().strip()
            sizes.append(size)
        if pq('select.buying-controls_select--colour option'):
            colors = []
            for color_node in pq('select.buying-controls_select--colour option').items():
                color = color_node.text().strip()
                if color:
                    colors.append(color)
        else:
            colors = []
            color = pq('.js-buying-controls_value--colour').text().strip()
            colors.append(color)

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'title': title, 'name': name, 'was_price': was_price, 'now_price': now_price, 'colors': colors,
            'introduction': introduction, 'sizes': sizes, 'stock': stock, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id, 'size_guide': size_guide
        }
