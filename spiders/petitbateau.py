# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class PetitbateauCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.petit-bateau.co.uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(PetitbateauCrawler, self).__init__()

        # 商品店铺
        self.store = "Petit Bateau"

        # 商品品牌
        self.brand = "Petit Bateau"

        # 店铺ID
        self.store_id = 1343

        # 品牌ID
        self.brand_id = 419

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('#nav .navigation .clearfix > li.nav-li')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name in ('Newborn', 'Looks'):
                continue
            if cat1_name == 'Accessories':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('div.sous-nav .page-center .content-center .top-univers a.title-univers')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node.attr('href'))
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                if cat2_name in ('Baby Girl', 'Girl', 'Women', 'new'):
                    cat3_nodes = cat1_node.children(
                        'div.sous-nav .page-center .content-center .link-nav-univers:first .link-nav-univers-content ul li')
                    for cat3_node in cat3_nodes.items():
                        cat3_name = cat3_node.children('a').text().strip()
                        if not cat3_name:
                            continue
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
                else:
                    cat3_nodes = cat1_node.children(
                        'div.sous-nav .page-center .content-center .link-nav-univers:last .link-nav-univers-content ul li')
                    for cat3_node in cat3_nodes.items():
                        cat3_name = cat3_node.children('a').text().strip()
                        if not cat3_name:
                            continue
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

        page = 1
        nbResultsPerPage = 18
        params = {}
        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies, params=params
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            total_pages = pq('.product-list').attr('data-page-max')
            if (not total_pages) or (int(total_pages) == 1):
                break
            params_data = pq('.product-list').attr('data-page-next')
            page += 1
            sorting = params_data.split('&')[-2].partition('=')[-1]
            constraints = params_data.split('&')[-1].partition('=')[-1]
            params.update(
                {'page': page, 'nbResultsPerPage': nbResultsPerPage, 'sorting': sorting, 'constraints': constraints})
            if page > int(total_pages):
                break

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#content .page-list-center .product-list .product')
        if node:
            for detail in node.items():
                url = self._full_url(url_from=resp.url,
                                     path=detail.children('.product-content a.product-page-link').attr('href'))
                if url:
                    meta['product_id'] = urlparse(url).path.split('/')[-1].partition('.')[0]
                    yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('.visual-product .thumb-product img').items():
            img_url = img_node.attr('data-zoom')
            if img_url:
                images.append(img_url)

        # 商品名称
        name = pq('#base-presentation .title-product').text().strip()

        # 商品价格
        now_price = pq('.right-options .section-price .price').text().strip()

        # 商品颜色文字
        colors = []
        for color_node in pq('.list-colors li a img').items():
            color = color_node.attr('alt')
            if color:
                colors.append(color)

        # 商品颜色链接
        color_links = []
        for color_node in pq('.list-colors li a img').items():
            color_link = color_node.attr('src')
            if color_link:
                color_links.append(color_link)

        # 商品尺寸
        sizes = []
        for size_node in pq('div.list-size button.disabled').items():
            size = size_node.text().strip() + '--out of stock'
            sizes.append(size)
        for size_node in pq('div.list-size button[class!=" disabled"]').items():
            size = size_node.text().strip()
            sizes.append(size)

        # 商品介绍
        introduction = pq('.text-description').text().strip()

        # 商品详情
        details = pq('.reference-product').text().strip()

        # 商品库存
        stock = 0
        stock_text = pq('.buy').text().strip()
        if stock_text == 'ADD TO BASKET':
            stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'now_price': now_price, 'colors': colors, 'color_links': color_links, 'sizes': sizes,
                'introduction': introduction, 'details': details, 'stock': stock, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
