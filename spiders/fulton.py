# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy
from urllib.parse import urlparse


class FultonCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.fultonumbrellas.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(FultonCrawler, self).__init__()

        # 商品店铺
        self.store = "Fulton"

        # 商品品牌
        self.brand = "Fulton"

        # 店铺ID
        self.store_id = 302

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 257

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []
        node = pq('#nav > li[class!="div"]')
        for top in node.items():
            cat1_name = top('.no-link').text().strip()
            if cat1_name == 'Popular':
                continue
            cat1_url = self.INDEX_URL
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}
            child_node = top('.submenu > li')
            for child in child_node.items():
                cat2_name = child('a').text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=child('a').attr('href'))
                if 'All' in cat2_name:
                    break
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

        node = pq('#search .thumb-wrapper')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('a.thumbbox').attr('href'))
            meta['product_id'] = urlparse(url).path.strip('/').split('/')[-1]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img in pq('#itemImages > a > img.itemThumb').items():
            img_url = self.INDEX_URL + img.attr('src').replace('-fixed-height-100', '-width-1000')
            images.append(img_url)

        # 商品名称
        name = pq('#content #item .mob-item-title').text().strip().partition('(')[0]

        # 商品价格
        was_price = pq('#item .price .rrp').text().strip()
        now_price = pq('#item .price .price-sale').text().strip().partition(':')[-1].strip()
        if not (was_price and now_price):
            now_price = pq('#item > h1 > .price').text().strip()

        # 商品介绍
        h2 = pq('#itemText h2:eq(1)').text().strip()
        p = [p.text().strip() for p in pq('#itemDesc p').items()]
        introduction = h2 + ':' + ''.join(p)

        # 商品库存
        stock_text = pq('#itemAddBox .bag-options p').text().strip()
        if not stock_text:
            stock = 999
        else:
            stock = 0

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'],
            'images': images, 'name': name, 'was_price': was_price, 'new_price': now_price,
            'introduction': introduction, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id, 'stock': stock
        }

