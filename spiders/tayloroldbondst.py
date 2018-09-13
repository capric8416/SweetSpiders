# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy
from urllib.parse import urlparse


class TayloroldbondstCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.tayloroldbondst.co.uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(TayloroldbondstCrawler, self).__init__()

        # 商品店铺
        self.store = "Taylor of Old Bond Street"

        # 商品品牌
        self.brand = "Taylor of Old Bond Street"

        # 店铺ID
        self.store_id = 1544

        # 品牌ID
        self.brand_id = 388

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('#hmenu > .mitext')
        for cat1_node in top.items():
            cat1_name = cat1_node.children('a.menu').text().strip()
            if cat1_name in ('Home', 'Gifts'):
                continue
            if cat1_name in ('Shaving', 'Face & Body', 'Hair & Scalp'):
                cat1_url = self.INDEX_URL
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

                cat2_nodes = cat1_node.children('div ul.submenu li > a')
                for cat2_node in cat2_nodes.items():
                    cat2_name = cat2_node.text().strip()
                    if cat2_name in ('Fragrances', 'Colognes'):
                        continue
                    cat2_url = self._full_url(url_from=resp.url, path=cat2_node.attr('href'))

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat1['children'].append({
                        'name': cat2_name, 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.append([
                        cat2_url, headers, resp.cookies.get_dict(),
                        {'categories': [(cat1_name, cat1_url),
                                        (cat2_name, cat2_url)]}
                    ])

                categories.append(cat1)
            else:
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a.menu').attr('href'))

                cat1 = {'name': cat1_name, 'url': cat1_url,
                        'uuid': self.cu.get_or_create(cat1_name)}

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                cookies = resp.cookies.get_dict()

                results.append([
                    cat1_url, headers, cookies,
                    {'categories': [(cat1_name, cat1_url)]}
                ])

                categories.append(cat1)
        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url, path=pq('.next').attr('href'))
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.viewItemList .viewItemList__row .oxcell')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.PBItemImg a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        if pq('.c-ox-imgzoom__thumbs-list-inner li a'):
            for img_node in pq('.c-ox-imgzoom__thumbs-list-inner li a').items():
                img_url = self._full_url(url_from=resp.url, path=img_node.attr('href'))
                if img_url:
                    images.append(img_url)
        if pq('#imgmain > a'):
            for img_node in pq('#imgmain > a').items():
                img_url = self._full_url(url_from=resp.url, path=img_node.attr('href'))
                if img_url:
                    images.append(img_url)
        if pq('.imgmain'):
            for img_node in pq('.imgmain').items():
                img_url = self._full_url(url_from=resp.url, path=img_node.attr('src'))
                if img_url:
                    images.append(img_url)
        images = list(set(images))

        # 商品名称
        name = pq('.viewDetail__title .PBItemTitle').text().strip()

        # 商品价格
        now_price = pq('.PBItemPrice .PBCurrency .PBSalesPrice').text().strip()

        # 商品介绍
        introduction = pq('.PBItemDesc').text().strip()

        # 商品库存
        stock = 0
        if pq('.PBMsgOutOfStock'):
            stock_text = pq('.PBMsgOutOfStock').text().strip()
            if stock_text == 'OUT OF STOCK':
                stock = 0
        else:
            stock = 999

        # 商品编号
        code = pq('.PBItemSku .PBShortTxt').text().strip()

        # 商品详情
        details = pq('.PBItemDesc li').text().strip()

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'now_price': now_price, 'introduction': introduction, 'stock': stock, 'code': code,
            'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id,
            'coin_id': self.coin_id, 'details': details
        }
