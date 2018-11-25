# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class SleekmakeupCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.sleekmakeup.com/uk'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    COOKIES = {'visid_incap_1697827': 'qGIQlZRMRtWw5qBLq5zfC3vJmVsAAAAAQUIPAAAAAAAXMw88EsAxN77FwskGg+xo',
               'incap_ses_434_1697827': 'QB7wDMLQ+EqrA+QITeEFBnzJmVsAAAAATp1NOfL496KfNoaIVVdjZw==',
               '_ga': 'GA1.2.1689547161.1536805246',
               '_gid': 'GA1.2.530294803.1536805247',
               '_gat_UA-32594438-3': '1',
               'BVBRANDID': '9f747e3f-4506-47b5-b512-731cb1344c8a',
               'BVBRANDSID': '630c7999-c4ed-498d-bed0-57169eb02c35',
               'sc.ASP.NET_SESSIONID': 'bvzaau53monnafmtp2skrxtj',
               '__olapicU': '1536805248833',
               'visits': '1'}

    def __init__(self):
        super(SleekmakeupCrawler, self).__init__()

        # 商品店铺
        self.store = "Sleek"

        # 商品品牌
        self.brand = "Sleek"

        # 店铺ID
        self.store_id = 1628

        # 品牌ID
        self.brand_id = 345

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('#block-mainnavigation .nav ul > li')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name == 'BESTSELLERS':
                continue
            if cat1_name == 'MY FACE. MY RULES.':
                break
            if cat1_name == 'NEW IN':
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
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
            else:
                cat1_url = cat1_node.children('a').attr('href')
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

                cat2_nodes = cat1_node.children('section .set a')
                for cat2_node in cat2_nodes.items():
                    cat2_name = cat2_node.text().strip()
                    # if 'ALL' in cat2_name:
                    #     break
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

            next_page = self._full_url(url_from=resp.url, path=pq('link[rel="next"]').attr('href'))
            if not next_page:
                break

            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#block-views-block-plp-plp .container .row-flex div.col-md-4')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path= detail.children('.product .product-title a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#slider .slides .field--item img').items():
            img_url = self._full_url(url_from=resp.url, path=img_node.attr('src'))
            if img_url:
                images.append(img_url)

        # 商品名称
        if pq('.pdpproductcontent .pdp-title'):
            name = pq('.pdpproductcontent .pdp-title').text().strip()
        else:
            name = pq('.pdpproductcontent h1').text().strip()

        # 商品价格
        now_price = pq('.pdppricewraptop .pdpcurrentprice .pdppricewrap').text().strip()

        # 商品介绍
        introduction = pq('#tab1default').text().strip()

        # 商品详情
        details = pq('#tab2default').text().strip() + pq('#tab3default').text().strip()

        # 商品颜色
        colors = []
        for color_node in pq('.color-swatch .color_field__swatch--circle').items():
            color = color_node.attr('colorclass')
            if color:
                colors.append(color)

        # 商品尺码
        sizes = []
        for size_node in pq('.pdpgram').items():
            size = size_node.text().strip()
            if size:
                sizes.append(size)

        # 商品库存
        stock = 0
        stock_text = pq('.product-atc').text().strip()
        if stock_text == 'Add to Bag':
            stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'now_price': now_price, 'introduction': introduction, 'details': details,
                'colors': colors, 'sizes': sizes, 'stock': stock, 'store': self.store, 'brand': self.brand,
                'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
