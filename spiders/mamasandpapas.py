# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class MamasandpapasCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.mamasandpapas.com/en-gb/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(MamasandpapasCrawler, self).__init__()

        # 商品店铺
        self.store = "Mamas & Papas"

        # 商品品牌
        self.brand = "Mamas & Papas"

        # 店铺ID
        self.store_id = 1327

        # 品牌ID
        self.brand_id = 339

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('#js-header .col-xs-4:eq(0) a')
        for cat1_node in tops.items():
            cat1_name = cat1_node.text().strip()
            if cat1_name == 'Discover':
                break
            cat1_url = self.INDEX_URL
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = pq('ul.nav_group:eq(0) li.yCmsComponent a')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node.attr('href'))

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                if cat2_name:
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

            next_page = self._full_url(url_from=resp.url, path=pq('.pagination:eq(0) li.next a').attr('href'))
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#grid .productLister .col-xs-6')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.productCard .productCard_title > a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        # img_link = 'https://recommend.qubitproducts.com/vc/recommend/2.0/mamasandpapas?strategy=pp1&id=1532073143207.499353&n=12'
        # resp = self._request(url=img_link, method='POST', data={'h': [urlparse(url).path.split(' / ')[-1]]})
        # data = resp.json()['result']['items']
        for img_node in pq('#js-desktopImageContainer img').items():
            img = img_node.attr('src')
            if img:
                images.append(img)

        # 商品名称
        name = pq('.productDetail h1.productDetail_title').text().strip()

        # 商品价格
        now_price = pq('.productDetail_price .price-block strong').text().strip()

        # 商品颜色
        colors = []
        pass

        # 商品介绍
        introduction = pq('.mb-2').text().strip()

        # 商品库存,该网站有些商品显示预购
        stock = 0
        stock_text = pq('#inStock').text().strip()
        if 'in' in stock_text:
            stock = 999

        # 商品详情
        details = pq('.productDetail_panelContent .details-product-mobile').text().strip()

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'now_price': now_price, 'colors': colors, 'introduction': introduction, 'details': details,
            'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
