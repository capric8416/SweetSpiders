# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import json
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery

from scripts.google_translate import GoogleTranslate


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
        g = GoogleTranslate()
        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('#categories_nav li.js-root-category')
        for cat1_node in top.items():
            cat1_name = cat1_node('.categories_main .nav_header').text().strip()
            if cat1_name == 'Sale':
                continue
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node('.categories_main').attr('href'))
            cat1 = {'name': cat1_name, 'name_cn': g.query(source=cat1_name), 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            child = cat1_node('.nav .nav_inner .nav_column')
            for child_node in child.items():
                for cat2_node in child_node('span.nav_header').items():
                    cat2_name = cat2_node('a').text().strip()

                    if cat2_name == 'New Arrivals':
                        continue
                    if cat2_name in ('Home & Gifts', 'Edited: Baker by Ted Baker'):
                        break
                    else:
                        cat2_url = self._full_url(url_from=resp.url, path=cat2_node('a').attr('href'))

                        cat2 = {
                            'name': cat2_name, 'name_cn': g.query(source=cat2_name), 'url': cat2_url, 'children': [],
                            'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                        }

                    cat3_nodes = cat2_node.next('ul.nav_list')
                    for cat3_node in cat3_nodes('li.nav_item').items():
                        cat3_name = cat3_node('a.nav_link').text().strip()
                        if ('All' in cat3_name) or ('Home' in cat3_name):
                            continue
                        cat3_url = self._full_url(url_from=resp.url, path=cat3_node('a.nav_link').attr('href'))

                        headers = copy.copy(self.headers)
                        headers['Referer'] = resp.url

                        cat2['children'].append({
                            'name': cat3_name, 'name_cn': g.query(source=cat3_name), 'url': cat3_url,
                            'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                        })

                        results.append([
                            cat3_url, headers, resp.cookies.get_dict(),
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
                rollback=self.push_category_info, meta=meta)
            if not resp:
                return
            pq = PyQuery(resp.text)
            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url,
                                       path=pq('.foot .pagination .page_select li.next a').attr('href'))
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
        images = []
        for img in pq('#product_images .carousel .viewport .slider div.image').items():
            img_url = img('a.image img').attr('ng-src')
            if img_url.startswith('https://images'):
                images.append(img_url.replace("{{imageFormat[view.imgSizes]['pdp_primary']}}", "w=564%26h=705%26q=85"))

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
        # 格式如下——size:stock,每个尺寸及对应库存
        sizes = []
        text = pq('script:contains("var utag_data")').text().strip()
        json_data = text[text.index('var utag_data = ') + len('var utag_data = '):text.index(
            'utag_data.error_count')].strip().strip(';')
        data = json.loads(json_data)
        size_node = data['product_sizes_available'][0].split('|')
        for size in size_node:
            if size:
                sizes.append(size)

        # 商品介绍
        introduction = pq('#product_more .description').text().strip()

        # 商品描述
        details = pq('#product_details').text().strip()

        # 尺寸指导
        size_guide = {}
        size_guide_node = pq('div.size_guide span.check_ted a').attr('ng-click')
        if not size_guide_node:
            size_guide = size_guide
        else:
            size_guide_url = 'https://www.tedbaker.com' + size_guide_node.split(',')[0].partition('(')[-1].strip("'")
            if size_guide_url == 'https://www.tedbaker.com/uk/womens-size-guide':
                resp = self._request(url=size_guide_url, headers=extra['headers'], cookies=extra['cookies'])
                pq = PyQuery(resp.text)

                guide_table_title = pq('div.info h3').text().strip()
                how_to_see = pq('div.info p').text().strip()

                table_name = pq('#international_conversion h4').text().strip()
                table1 = []
                table_1 = pq('#international_conversion div.chart table tr')
                for tr in table_1.items():
                    each_size = tr.text().strip()
                    table1.append(each_size.replace('\n', ','))

                cm_table = []
                for tr in pq('#mens_measurements .chart .cm tr').items():
                    each_size = tr.text().strip()
                    cm_table.append(each_size.replace('\n', ','))
                cm_unit = 'cm'

                inches_table = []
                for tr in pq('#mens_measurements .chart .inches tr').items():
                    each_size = tr.text().strip()
                    inches_table.append(each_size.replace('\n', ','))
                inches_unit = 'inches'

                size_guide = {'guide_table_title': guide_table_title, 'how_to_see': how_to_see,
                              'table_name': table_name,
                              'table1': table1, 'cm': {'cm_unit': cm_unit, 'cm_table': cm_table},
                              'inches': {'inches_unit': inches_unit, 'inches_table': inches_table}}

            if size_guide_url == 'https://www.tedbaker.com/uk/mens-shoe-size-guide':
                resp = self._request(url=size_guide_url, headers=extra['headers'], cookies=extra['cookies'])
                pq = PyQuery(resp.text)
                guide_table_title = pq('div.info h3').text().strip()
                how_to_see = pq('div.info p').text().strip()

                table_name = pq('#international_conversion h4').text().strip()
                table = []
                for tr in pq('#international_conversion .chart div.html_component').prev('div table tr').items():
                    each_size = tr.text().strip()
                    table.append(each_size.replace('\n', ','))

                size_guide = {'guide_table_title': guide_table_title, 'how_to_see': how_to_see,
                              'table_name': table_name, 'table': table}

            if size_guide_url == 'https://www.tedbaker.com/uk/mens-shirt-size-guide':
                resp = self._request(url=size_guide_url, headers=extra['headers'], cookies=extra['cookies'])
                pq = PyQuery(resp.text)
                guide_table_title = pq('.info:first h3').text().strip()
                how_to_see = pq('.info:first h3').next('p').text().strip()

                table_1_name = pq('.info:first h3').next('p').next('p').text().strip()

                cm_table_1 = []
                for tr in pq('.info:first #shirt_measurement .chart .cm tr').items():
                    each_size = tr.text().strip()
                    if each_size:
                        cm_table_1.append(each_size.replace('\n', ','))

                inches_table_1 = []
                for tr in pq('.info:first #shirt_measurement .chart .inches tr').items():
                    each_size = tr.text().strip()
                    if each_size:
                        inches_table_1.append(each_size.replace('\n', ','))

                table_2_name = pq('.info:first #international_conversion h4').text().strip()

                cm_table_2 = []
                for tr in pq('.info:first #international_conversion .chart .cm tr').items():
                    each_size = tr.text().strip()
                    cm_table_2.append(each_size.replace('\n', ','))

                inches_table_2 = []
                for tr in pq('.info:first #international_conversion .chart .inches tr').items():
                    each_size = tr.text().strip()
                    inches_table_2.append(each_size.replace('\n', ','))

                table_3_name = pq('.info:last h3').text().strip()
                cm_table_3 = []
                for tr in pq('.info:last #shirt_measurement .chart .cm tr').items():
                    each_size = tr.text().strip()
                    cm_table_3.append(each_size.replace('\n', ','))
                cm_unit = 'cm'

                inches_table_3 = []
                for tr in pq('.info:last #shirt_measurement .chart .inches tr').items():
                    each_size = tr.text().strip()
                    inches_table_3.append(each_size.replace('\n', ','))
                inches_unit = 'inches'

                size_guide = {'guide_table_title': guide_table_title, 'how_to_see': how_to_see,
                              'table1': {'table_1_name': table_1_name, 'cm_table_1': cm_table_1, 'cm_unit': cm_unit,
                                         'inches_table_1': inches_table_1, 'inches_unit': inches_unit},
                              'table2': {'table_2_name': table_2_name, 'cm_table_2': cm_table_2, 'cm_unit': cm_unit,
                                         'inches_table_2': inches_table_2, 'inches_unit': inches_unit},
                              'table3': {'table_3_name': table_3_name, 'cm_table_3': cm_table_3, 'cm_unit': cm_unit,
                                         'inches_table_3': inches_table_3, 'inches_unit': inches_unit}
                              }

            if size_guide_url == 'https://www.tedbaker.com/uk/mens-size-guide':
                resp = self._request(url=size_guide_url, headers=extra['headers'], cookies=extra['cookies'])
                pq = PyQuery(resp.text)
                guide_table_title = pq('.info h3').text().strip()
                how_to_see = pq('.info h3').next('p').text().strip()

                table_1_name = pq('#international_conversion h4').text().strip()
                table1 = []
                for tr in pq('#international_conversion .chart tr').items():
                    each_size = tr.text().strip()
                    table1.append(each_size.replace('\n', ','))

                table_2_name = pq('#mens_measurements h4').text().strip()
                cm_table = []
                for tr in pq('#mens_measurements .chart .cm tr').items():
                    each_size = tr.text().strip()
                    cm_table.append(each_size.replace('\n', ','))
                cm_unit = 'cm'

                inches_table = []
                for tr in pq('#mens_measurements .chart .inches tr').items():
                    each_size = tr.text().strip()
                    inches_table.append(each_size.replace('\n', ','))
                inches_unit = 'inches'

                size_guide = {'guide_table_title': guide_table_title, 'how_to_see': how_to_see,
                              'table_1': {'table_1_name': table_1_name, 'table1': table1}, 'table_2_name': table_2_name,
                              'cm_table': {'cm_table': cm_table, 'cm_unit': cm_unit},
                              'inches_table': {'inches_table': inches_table, 'inches_unit': inches_unit}
                              }

            if size_guide_url in (
                    'https://www.tedbaker.com/uk/Kids/Baby_Size_Guide',
                    'https://www.tedbaker.com/uk/Kids/Boys_Size_Guide',
                    'https://www.tedbaker.com/uk/Kids/Girls_Size_Guide'):
                resp = self._request(url=size_guide_url, headers=extra['headers'], cookies=extra['cookies'])
                pq = PyQuery(resp.text)
                guide_table_title = pq('.info h3').text().strip()
                how_to_see = pq('.info p').text().strip()
                cm_table = []
                for tr in pq('#kids_measurements .chart .cm tr').items():
                    each_size = tr.text().strip()
                    cm_table.append(each_size.replace('\n', ','))
                cm_unit = 'cm'

                inches_table = []
                for tr in pq('#kids_measurements .chart .inches tr').items():
                    each_size = tr.text().strip()
                    inches_table.append(each_size.replace('\n', ','))
                inches_unit = 'inches'

                size_guide = {'guide_table_title': guide_table_title, 'how_to_see': how_to_see,
                              'cm': {'cm_table': cm_table, 'cm_unit': cm_unit},
                              'inches': {'inches_table': inches_table, 'inches_unit': inches_unit}}

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'colors': colors, 'sizes': sizes,
            'introduction': introduction, 'details': details, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id, 'size_guide': size_guide
        }
