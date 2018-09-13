# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy
from urllib.parse import urlparse


class LariziaCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'http://www.larizia.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(LariziaCrawler, self).__init__()

        # 商品店铺
        self.store = "Larizia"

        # 商品品牌
        self.brand = "Larizia"

        # 店铺ID
        self.store_id = 1717

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 151

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        node = pq('.container #site-header__nav__21 li')
        for top in node.items():
            top_category = top('a').text().strip()
            if top_category == 'New Arrivals ':
                url = self._full_url(url_from=resp.url, path=top('a').attr('href'))
                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                categories = (top_category,)
                yield url, headers, resp.cookies.get_dict(), {'categories': categories}
            elif top_category == 'Designers':
                continue
            else:
                child_node = top('.drop-down__menu__block  ul.drop-down__menu__categories li:gt(0)')
                for child in child_node.items():
                    child_category = child('a span').text().strip()
                    if child_category == ('View All Bags' or 'View All Shoes' or 'View All Accessories'):
                        continue
                    child_url = self._full_url(url_from=resp.url, path=child('a').attr('href'))
                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url
                    categories = (top_category, child_category)
                    yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies,
                 meta=meta)
            if not resp:
                return
            pq = PyQuery(resp.text)
            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url, path=pq('.text-align-right .pagination .next-page').attr('href'))
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#js-search-results-products__list li.col')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.product__image a').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        imgs = []
        for img in pq('.product__image__main .slick-list .slick-slide').items():
            img_url = self._full_url(url_from=resp.url, path=img('a').attr('href'))
            imgs.append(img_url)

        title = pq('.price-match-wrapper #js-product-content__title .product-content__title--brand').text().strip()

        name = pq('.price-match-wrapper #js-product-content__title #js-product-title').text().strip()

        was_price = pq('#js-product-was .GBP').text().strip()

        now_price = pq('#js-product-price .GBP').text().strip()
        if not (was_price and now_price):
            now_price = pq('#js-product-price .GBP').text().strip()

        features = [li.text().strip() for li in pq('.product-tabs__content__cms ul li').items()]

        description = pq('#product__description p').text().strip()

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': imgs,
            'title': title, 'name': name, 'was_price': was_price, 'now_price': now_price, 'features': features,
            'description': description, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id
        }

