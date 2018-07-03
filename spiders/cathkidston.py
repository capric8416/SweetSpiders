# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class CathkidstonCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.cathkidston.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(CathkidstonCrawler, self).__init__()

        # 商品店铺
        self.store = "Cath Kidston"

        # 商品品牌
        self.brand = "Cath Kidston"

        # 店铺ID
        self.store_id = 1218

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 357

    def _parse_index(self, resp):
        """首页解析器"""

        size_guide = self.get_size_guide()

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('#navigation ul.level_1 li.level_1')
        for cat1_node in top.items():
            cat1_name = cat1_node('a.level_1').text().strip()
            if cat1_name in ('New In', 'Disney', 'Collections'):
                continue
            if cat1_name == 'Blog':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node('a.level_1').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            child = cat1_node('div.level_2 > ul.level_2 > li.level_2')
            for cat2_node in child.items():
                cat2_name = cat2_node('a.level_2').text().strip()
                if 'View All' in cat2_name:
                    continue
                if cat2_name == 'Gift Wrap Service':
                    break
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node('a.level_2').attr('href'))
                if not cat2_node('div.level_3'):
                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat1['children'].append({
                        'name': cat2_name, 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.append([
                        cat2_url, headers, resp.cookies.get_dict(),
                        {
                            'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url)],
                            'size_guide': size_guide
                        }
                    ])

                else:
                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }
                    for cat3_node in cat2_node('div.level_3 > ul.level_3 > li.level_3').items():
                        cat3_name = cat3_node('a').text().strip()
                        if 'View All' in cat3_name:
                            continue
                        cat3_url = self._full_url(url_from=resp.url, path=cat3_node('a').attr('href'))

                        headers = copy.copy(self.headers)
                        headers['Referer'] = resp.url

                        cat2['children'].append({
                            'name': cat3_name, 'url': cat3_url,
                            'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                        })

                        results.append([
                            cat3_url, headers, resp.cookies.get_dict(),
                            {
                                'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url), (cat3_name, cat3_url)],
                                'size_guide': size_guide
                            }
                        ])

                    cat1['children'].append(cat2)

            categories.append(cat1)
        return categories, results

    # 尺寸指导
    def get_size_guide(self):
        size_guide = self.INDEX_URL + '/sizing-guide/content/fcp-content'
        resp = self._request(url=size_guide, headers=self.headers)
        pq = PyQuery(resp.text)

        areas, women_clothings = [], []
        size_guide_url = self._full_url(url_from=resp.url, path=pq('.pm_aside a.link').attr('href'))
        for women_clothing in pq('table.ck-size-guide-table:eq(0) thead > tr th').items():
            each_area = women_clothing.text().strip()

            areas.append(each_area)
        for each_size in pq('table.ck-size-guide-table:eq(0) tbody > tr').items():
            size_each = [each.text().strip() for each in each_size('td').items()]
        women_clothings.extend([areas, size_each])

        second_clothing = []
        areas = [area.text().strip() for area in pq('table.ck-size-guide-table:eq(1) thead > th').items()]
        for size_node in pq('table.ck-size-guide-table:eq(1) tr').items():
            size_each = [each.text().strip() for each in size_node('td').items()]
        second_clothing.extend([areas, size_each])

        women_shoes = []
        areas = [area.text().strip() for area in pq('table.ck-size-guide-table:eq(2) thead > tr th').items()]
        for each_size in pq('table.ck-size-guide-table:eq(2) > tr').items():
            size_each = [each.text().strip() for each in size_each('td').items()]
        women_shoes.extend([areas, size_each])

        baby_clothing = []
        areas = [area.text().strip() for area in pq('table.ck-size-guide-table:eq(3) thead > tr th').items()]
        for each_size in pq('table.ck-size-guide-table:eq(3) > tr').items():
            size_each = [each.text().strip() for each in each_size('td').items()]
        baby_clothing.extend([areas, size_each])

        baby_shoes = []
        areas = [area.text().strip() for area in pq('table.ck-size-guide-table:eq(4) thead > tr th').items()]
        for each_size in pq('table.ck-size-guide-table:eq(4) > tr').items():
            size_each = [each.text().strip() for each in each_size('td').items()]
        baby_shoes.extend([areas, size_each])

        kids_clothing = []
        areas = [area.text().strip() for area in pq('table.ck-size-guide-table:eq(5) thead > tr th').items()]
        for each_size in pq('table.ck-size-guide-table:eq(5) > tr').items():
            size_each = [each.text().strip() for each in each_size('td').items()]
        kids_clothing.extend([areas, size_each])

        kids_shoes = []
        areas = [area.text().strip() for area in pq('table.ck-size-guide-table:eq(6) thead > tr th').items()]
        for each_size in pq('table.ck-size-guide-table:eq(6) > tr').items():
            size_each = [each.text().strip() for each in each_size('td').items()]
        kids_shoes.extend([areas, size_each])

        return {
            'women_clothins': women_clothings, 'second_clothing': second_clothing,
            'women_shoes': women_shoes, 'baby_clothing': baby_clothing, 'baby_shoes': baby_shoes,
            'kids_clothing': kids_clothing, 'kids_shoes': kids_shoes
        }

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
                                       path=pq('#results .summary_and_sort .pagination:eq(0) .page-next').attr('href'))
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#results .product_list li.product')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.product_info .product_title').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        headers = copy.copy(extra['headers'])
        headers['Referer'] = resp.url
        img_url = self._full_url(url_from=resp.url,
                                 path=pq('#main_image_container #main_image').attr('src').replace('xlarge', 'zoom'))
        images.append(img_url)
        count = 1
        while True:
            new_img = img_url.replace('.jpg', '_%s.jpg') % count
            resp = self._request(method='head', url=new_img, headers=headers, cookies=resp.cookies.get_dict())
            if resp.status_code == 403:
                break
            count += 1

            images.append(new_img)

        # 商品名称
        name = pq('#info > h1').text().strip()

        # 商品价格
        was_price = pq('#info p[itemprop="offerDetails"]').text()
        if 'Was' in was_price:
            now_price = was_price.partition('Now')[-1].strip()
            was_price = was_price.partition('Was')[-1].partition('Now')[0].strip()

        else:
            now_price = was_price
            was_price = ''

        # 商品尺寸
        sizes = []
        for size_node in pq('.matrix_table tr th').items():
            size = size_node.text().strip()
            if size:
                sizes.append(size)

        # 商品介绍
        introduction = pq('#product_info_tabs #tabs-1 p').text().strip()

        # 商品描述
        details = pq('#tabs-2').text().strip()

        # 商品库存
        stock_text = pq('.stock-status-message').text().strip()
        if stock_text == 'Sorry this item is out of stock':
            stock = 0
        else:
            stock = 999

        return {
            'url': url, 'catgories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'sizes': sizes, 'introduction': introduction,
            'details': details, 'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id, 'women_clothing': women_clothings, 'second_clothing':
                second_clothing, 'women_shoes': women_shoes, 'baby_clothing': baby_clothing, 'baby_shoes': baby_shoes,
            'kids_cloting': kids_clothing, 'kids_shoes': kids_shoes
        }
