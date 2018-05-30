# -*- coding: utf-8 -*-
# !/usr/bin/env python
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery
import copy
from urllib.parse import urlparse


class LanvinCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.lanvin.com/GB/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(LanvinCrawler, self).__init__()

        # 商品店铺
        self.store = "LANVIN"

        # 商品品牌
        self.brand = "LANVIN"

        # 店铺ID
        self.store_id = 202

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        top_category_1 = pq('.mainNav .level-0 #women .text').text().strip()
        child_category = pq('.menuContainer .level-1 #women_column1_new_arrivals .text').text().strip()
        if child_category == 'New arrivals':
            child_url = pq('.menuContainer .level-1:eq(0) #women_column1_new_arrivals a').attr('href')
            categories = (top_category_1, child_category)
            headers = copy.copy(self.headers)
            headers['Referer'] = resp.url
            yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}
        child_node = pq('.menuContainer .level-1:eq(0) ul li.hasChildren:gt(0)')
        for child in child_node.items():
            child2 = child('a:eq(0) .text').text().strip()
            for child3_node in child('.level-2 li.menuItem').items():
                child3 = child3_node('a .text').text().strip()
                if child3 == 'All':
                    continue
                if not child3:
                    continue
                child_url = child3_node('a').attr('href')

                categories = (top_category_1, child2, child3)
                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

        top_category_2 = pq('.mainNav .level-0 #men .text').text().strip()
        child_node = pq('.menuContainer .level-1:eq(1) ul li.hasChildren:gt(0)')
        for child in child_node.items():
            child2 = child('a:eq(0) .text').text().strip()
            for child3_node in child('.level-2 li.menuItem').items():
                child3 = child3_node('a .text').text().strip()
                if child3 == 'All':
                    continue
                if not child3:
                    continue
                child_url = child3_node('a').attr('href')

                categories = (top_category_2, child2, child3)
                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

        top_category_3 = pq('.mainNav .level-0 #enfant .text').text().strip()
        child_node = pq('.menuContainer .level-1:eq(2) ul li.hasChildren')
        for child in child_node.items():
            child2 = child('a:eq(0) .text').text().strip()
            for child3_node in child('.level-2 li.menuItem').items():
                child3 = child3_node('a .text').text().strip()
                child_url = child3_node('a').attr('href')

                categories = (top_category_3, child2, child3)
                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                yield child_url, headers, resp.cookies.get_dict(), {'categories': categories}

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

            next_page = self._full_url(url_from=resp.url, path=pq('link:[rel="next"]').attr('href'))
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.products  .item')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.wrapper').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)
        imgs = []
        for img in pq('.productImages .alternativeImages li.loaded').items():
            img_url = img('img').attr('src')
            imgs.append(img_url)

        name = pq('.productInfoBox .productName .modelName').text().strip()

        price = pq('.priceUpdater .price .currency').text().strip() + pq('.priceUpdater .price .value').text().strip()

        sizes = []
        for size_node in pq('.sizesWrap .selectSize ul li:[class!="disabled"]').items():
            size = size_node('.sizeValue').text().strip()
            sizes.append(size)

        colors = []

        description = pq('#tabs .accordionMenu:eq(0) .accordionWrapper .value').text().strip()

        features = pq('.accordionMenu:eq(1) .accordionWrapper .attributesUpdater .value').text().strip()

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'imgs': imgs,
            'name': name, 'price': price, 'sizes': sizes, 'color': colors, 'description': description,
            'features': features, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'coin_id': self.coin_id
        }
