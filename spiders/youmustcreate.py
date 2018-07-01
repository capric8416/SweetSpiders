# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class YoumustcreateCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.youmustcreate.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(YoumustcreateCrawler, self).__init__()

        # 商品店铺
        self.store = "You Must Create"

        # 商品品牌
        self.brand = "You Must Create"

        # 店铺ID
        self.store_id = 1018

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 436

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('#secondary-navigation #main > li.menu-item')
        for cat1_node in top.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name == 'Featured':
                continue
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            child = cat1_node('ul.sub-menu > li.menu-item')
            for cat2_node in child.items():
                cat2_name = cat2_node.children('a').text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node.children('a').attr('href'))
                if 'ALL' in cat2_name:
                    continue
                if cat2_name in ('Menswear', 'Womenswear'):
                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }
                    resp = self._request(url=cat2_url, headers=self.headers, cookies=resp.cookies.get_dict())
                    pq = PyQuery(resp.text)
                    third_node = pq('#categories li.product')
                    for cat3_node in third_node.items():
                        cat3_name = cat3_node('a.wpsc_category_grid_item').text().strip()
                        cat3_url = self._full_url(url_from=resp.url,
                                                  path=cat3_node('a.wpsc_category_grid_item').attr('href'))

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
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.product-previews > li.product-preview')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('a.wpsc_product_title').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.strip('/').split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""
        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('.product-images-block .lazy-img-placeholder').items():
            img_url = self._full_url(url_from=resp.url, path=img_node('img').attr('src'))
            images.append(img_url)

        # 商品名称
        name = pq('.product-content .product-content-inner .product-title').text().strip()

        # 商品价格
        was_price = pq('.product-content-inner .product-price .oldprice').text().strip()

        now_price = pq('.product-content-inner .product-price .currentprice').text().strip()

        # 商品介绍
        introduction = pq('#ymc-tab-details .product-details').text().strip()

        # 商品尺寸
        sizes = []
        for size_node in pq('.wpsc_variation_forms option').items():
            size = size_node.text().strip()
            sizes.append(size)

        # 尺寸指导
        size_fit = []
        for each_size in pq('#ymc-tab-size .size-tables .size-table tbody tr').items():
            each_node = each_size('td').text().strip()
            size_fit.append(each_node)

        # 商品库存
        stock_text = pq('.product_form p.soldout').text().strip()
        if stock_text:
            stock = 0
        else:
            stock = 999

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
            'sizes': sizes, 'sizefit': size_fit, 'stock': stock, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
