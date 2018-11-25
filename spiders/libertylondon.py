# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class LibertylondonCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.libertylondon.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(LibertylondonCrawler, self).__init__()

        # 商品店铺
        self.store = "Liberty London"

        # 商品品牌
        self.brand = "Liberty London"

        # 店铺ID
        self.store_id = '暂无'

        # 品牌ID
        self.brand_id = '暂无'

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('.main-nav .has-sub')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if (not cat1_name) or cat1_name in ('Department', 'Liberty Collections'):
                continue
            if cat1_name == 'Brands':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('.has-banner > .mega-nav .depts-list > ul > li')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('a').text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node.children('a').attr('href'))
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                cat3_nodes = cat2_node.children('.dept-detail > .dept-links > .meganav-column > ul > li')
                for cat3_node in cat3_nodes.items():
                    cat3_name = cat3_node.children('a').text().strip()
                    if 'All' in cat3_name:
                        break
                    cat3_url = self._full_url(url_from=resp.url, path=cat3_node.children('a').attr('href'))

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat2['children'].append({
                        'name': cat3_name, 'url': cat3_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                    })

                    results.append([
                        cat3_url, headers, resp.cookies.get_dict(),
                        {'categories': [(cat1_name, cat1_url),
                                        (cat2_name, cat2_url),
                                        (cat3_name, cat3_url)]}
                    ])

                cat1['children'].append(cat2)

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

            next_page = self._full_url(url_from=resp.url,
                                       path=pq('#primary .bottom-controls .plp-paging a.load-more').attr('href'))
            if (not next_page) or len(pq('#search-result-items > li')) < 60:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#search-result-items > li')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.product .product-name .name-link').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1].partition('.')[0]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        if pq('#product-thumbnails .product-image-tile img'):
            for img_url in pq('#product-thumbnails .product-image-tile img').items():
                img = self._full_url(url_from=resp.url, path=img_url.attr('src').replace('small', 'large'))
                if img:
                    images.append(img)
        else:
            for img_node in pq('.product-image-container .product-image-tile a img').items():
                img_url = self._full_url(url_from=resp.url, path=img_node.attr('src'))
                if img_url:
                    images.append(img_url)

        # 商品名称
        brand_name = pq('#pdpMain .product-details-wrapper .product-details-container .center-vertical > h2').text()
        product_name = pq('#pdpMain .product-details-wrapper .product-details-container .center-vertical h1').text()
        name = brand_name + ':' + product_name

        # 商品价格
        now_price = pq('#product-content .price-rating-wrapper .product-price .price-sales').text()

        # 商品颜色文字
        colors = []
        for color_node in pq('.attribute .value ul.color li').items():
            color = color_node.children('a').attr('title')
            if color:
                colors.append(color)

        # 商品颜色链接
        color_links = []
        for color_link_node in pq('.attribute .value ul.color li').items():
            color_link = color_link_node('img').attr('src')
            if color_link:
                color_links.append(color_link)

        # 商品尺寸
        sizes = []
        for size_node in pq('#va-size option').items():
            size = size_node.text().strip()
            if size:
                sizes.append(size)

        # 商品介绍
        introduction = pq('.tab-content:eq(1)').text().strip()

        # 商品详情
        details = pq('.tab-content:first').text().strip()

        # 商品库存
        stock = 0
        if pq('#addToCartDisabled'):
            stock_text = pq('#addToCartDisabled').text().strip()
            if stock_text == 'Add to bag':
                stock = 999
        if pq('#addToCart'):
            stock_text = pq('#addToCart').text().strip()
            if stock_text == 'Add to bag':
                stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'name': name,
                'now_price': now_price, 'colors': colors, 'color_links': color_links, 'sizes': sizes, 'images': images,
                'introduction': introduction, 'details': details, 'stock': stock, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id

                }
