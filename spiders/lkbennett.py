# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy
from urllib.parse import urlparse
import execjs


class LkbennettCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.lkbennett.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(LkbennettCrawler, self).__init__()

        # 商品店铺
        self.store = "L.K. Bennett"

        # 商品品牌
        self.brand = "L.K. Bennett"

        # 店铺ID
        self.store_id = 454

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        node = pq('.main-navigation .nav-pills li.has-sub')
        for top in node.items():
            top_category = top('a:eq(0)').text().strip()
            if top_category == 'Collections':
                break
            for child in top('.nav-middle-container .links .sub-navigation-list li').items():
                child_category = child('a').text().strip()
                if child_category == 'VIEW ALL':
                    continue
                child_url = self._full_url(url_from=resp.url, path=child('a').attr('href'))
                categories = (top_category, child_category)

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""
        for count in range(1, result_count, 15):
            resp = self._request(
                url=url, headers=headers, cookies=cookies,
                rollback=self.push_category_info, meta=meta
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url, path=pq('.store-navigation-pager .next').attr('href'))
            result_count = res['listing']['result_count']
            if int(result_count) < 15:
                break


            pass

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        script = pq("script:contains('universal_variable')").text().strip()
        script = script.partition('=')[-1].strip(';')
        res = execjs.eval('(function(){ var value=' + script + ';return value; })()')
        data = res['listing']['items']

        for detail in data:
            url = self._full_url(url_from=resp.url, path=detail.get('url'))
            meta['product_id'] = detail.get('id')
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        imgs = []
        for img in pq('.amp-lkb-viewer .amp-main .amp-anim-container .amp-slide').items():
            img_url = img('.amp-image-container .amp-main-img').attr('src')
            imgs.append(img_url)

        name = pq('.text-center .product-details h1.name').text().strip()

        was_price = pq('.text-center .product-details .price .wasPrice strike').text().strip()

        now_price = pq('.text-center .product-details .price #jsProductPrice').attr('value')
        if not (was_price and now_price):
            now_price = pq('.product-details .price').text().strip()

        short_desc = pq('.text-center .product-details .description').text().strip()

        colors = []
        for color in pq('.variant-section .variant-selector .variant-list li').items():
            color_url = self._full_url(url_from=resp.url, path=color('a').attr('href'))
            colors.append(color_url)

        sizes = []
        for size_node in pq('.variant-selector .customSelectParent #Size option').items():
            size = size_node.text().strip()
            sizes.append(size)

        description = pq('.panel #collapse1 p:eq(0)').text().strip()

        features = pq('.panel #collapse2 p').text().strip()

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'imgs': imgs,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'short_desc': short_desc,
            'colors': colors, 'sizes': sizes, 'description': description, 'features': features, 'store': self.store,
            'brand': self.brand, 'store_id': self.store_id, 'coin_id': self.coin_id
        }


