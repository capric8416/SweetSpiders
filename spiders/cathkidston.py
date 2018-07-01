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
                        {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url)]}
                    ])

                    categories.append(cat1)
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

            next_page = self._full_url(url_from=resp.url, path=pq('#results .summary_and_sort .pagination:eq(0) .page-next').attr('href'))
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
        for img_node in pq('#images .flexslider .flex-viewport .alternatives li').items():
            img_url = self._full_url(url_from=resp.url, path=img_node('img').attr('src').replace('xsmall', 'zoom'))
            images.append(img_url)

        # 商品名称
        name = pq('#info > h1').text().strip()

        # 商品价格
        was_price = pq('#info p meta:eq(1)').text().strip().split()[-1]

        now_price = pq('#info p span.mark').text().strip().split()[-1]

        if not (was_price and now_price):
            now_price = pq('#info p span').text().strip()

        # 商品尺寸
        sizes = []
        for size_node in pq('#add_to_bag .element select option').items():
            size = size_node.text().strip()
            sizes.append(size)

        # 商品介绍
        introduction = pq('#product_info_tabs #tabs-1 p').text().strip()

        # 商品描述
        details = pq('#tabs-2').text().strip()

        # 商品库存
        stock_text = pq('#stock_status').text().strip()
        if ('More than' in stock_text) or ('in stock' in stock_text):
            stock = 999
        else:
            stock = 0

        return {
            'url': url, 'catgories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'sizes': sizes, 'introduction': introduction,
            'details': details, 'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id
        }


