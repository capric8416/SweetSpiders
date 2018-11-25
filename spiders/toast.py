# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class ToastCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.toa.st/uk/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    COOKIES = {'BNI_persistence': '0000000000000000000000000d6fa8c00000bb01',
               '__cfduid': 'd0e8342b78f8c37bf26952131731926a81536908092',
               'Commerce_TestPersistentCookie': 'TestCookie',
               'Commerce_TestSessionCookie': 'TestCookie',
               'MSCSProfile': '1D3D06FBE7C3B4A12BF6B506208442D2341F799A581991E156A94D4A06B5664073D9676D3C3A3A89B6BBE2941AB81EE663D0CF20538310F0C0E35B1C4DD88B2B2DBD25F55F65F5F1A6BB0A2C0476DBCE9DE800868D2388DD7E1B850C251708D54DCBAD60638EB2096EEA93EA2601FA1825D78E09B59D5041DD40CF496FFD13E9D89D0414E6A55E29',
               'urlcountry': 'us',
               'basketCookieTOAST_UK_L': 'basketSubtotal=0.0000&basketItems=0',
               'BNI_persistence': '000000000000000000000000716fa8c00000bb01',
               'cookie-banner-dismissed17': 'true',
               '_vwo_uuid_v2': 'D19C148063B1088FB7825AC9C927D1E63|e707a7a36969e1dc8da4e13bcc18d0c9',
               '__utma': '73633175.133783293.1536908096.1536908096.1536908096.1',
               '__utmc': '73633175',
               '__utmz': '73633175.1536908096.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
               '__utmt': '1',
               '__insp_wid': '1916516971',
               '__insp_slim': '1536908097297',
               '__insp_nv': 'true',
               '__insp_targlpu': 'aHR0cHM6Ly93d3cudG9hLnN0L3VzLw%3D%3D',
               '__insp_targlpt': 'VE9BU1QgfCBXb21lbuKAmXMgQ2xvdGhpbmcsIExvdW5nZXdlYXIgYW5kIEZ1bmN0aW9uYWwgSG9tZXdhcmU%3D',
               '__insp_norec_sess': 'true',
               'V1v4': '{"V1":"218091407545111897","V3":"0"}',
               'earlySpringOverlay': 'true',
               'tms_VisitorID': 's6g06neu3g',
               'tms_wsip': '1',
               'selectedCountry': 'GG',
               '__utmb': '73633175.2.9.1536908131067'}

    def __init__(self):
        super(ToastCrawler, self).__init__()

        # 商品店铺
        self.store = "Toast"

        # 商品品牌
        self.brand = "Toast"

        # 店铺ID
        self.store_id = 887

        # 品牌ID
        self.brand_id = 423

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('.primary-categories ul.new-cat-nav > li.nav-option > div.relative')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a.expandable').text().strip()
            if not cat1_name:
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a.expandable').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('.new-sub-nav .new-sub-nav-list > ul > li.new-sub-nav-list-heading')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.text().strip()
                cat2_url = self.INDEX_URL
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                cat3_nodes = cat2_node.next_all()
                for cat3_node in cat3_nodes.items():
                    cat3_name = cat3_node.children('a').text().strip()
                    if not cat3_name:
                        break
                    if 'All' in cat3_name:
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

        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)
            if pq('.next'):
                next_page = self._full_url(url_from=resp.url, path=pq('.next').attr('href'))
                if next_page:
                    url = next_page
            else:
                break

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#mainContent .category-product-items .product')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('.productHolder .productInfo .productTitle a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1].partition('.')[0]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('.next').items():
            img = img_node

        # 商品名称
        name = pq('.product-details .product-info h1').text().strip()

        # 商品价格
        now_price = pq('#nowPrice').text().strip()

        # 商品颜色文字
        colors = []
        for color_node in pq('ul.product-swatches li.swatch img').items():
            color = color_node.attr('alt')
            if color:
                colors.append(color)

        # 商品颜色链接
        color_links = []
        for color_link_node in pq('ul.product-swatches li.swatch img').items():
            color_link = self._full_url(url_from=resp.url, path=color_link_node.attr('src'))
            if color_link:
                color_links.append(color_link)

        # 商品尺寸
        sizes = []
        if pq('#ctabs-2 ul.product-sizes > li[class="grid-10 tablet-grid-10 mobile-grid-10 size pre-order"]'):
            for size_node in pq(
                    '#ctabs-2 ul.product-sizes > li[class="grid-10 tablet-grid-10 mobile-grid-10 size pre-order"]').items():
                size = size_node.text().strip()
                if size:
                    sizes.append(size)

        if pq('#ctabs-2 ul.product-sizes > li[class="grid-10 tablet-grid-10 mobile-grid-10 size "]'):
            for size_node in pq(
                    '#ctabs-2 ul.product-sizes > li[class="grid-10 tablet-grid-10 mobile-grid-10 size "]').items():
                size = size_node.text().strip()
                if size:
                    sizes.append(size)

        if pq('#ctabs-2 ul.product-sizes > li[class="grid-10 tablet-grid-10 mobile-grid-10 size low-stock"]'):
            for size_node in pq(
                    '#ctabs-2 ul.product-sizes > li[class="grid-10 tablet-grid-10 mobile-grid-10 size low-stock"]').items():
                size = size_node.text().strip()
                if size:
                    sizes.append(size)

        if pq('#ctabs-2 ul.product-sizes > li[class="grid-10 tablet-grid-10 mobile-grid-10 size out-of-stock"]'):
            for size_node in pq(
                    '#ctabs-2 ul.product-sizes > li[class="grid-10 tablet-grid-10 mobile-grid-10 size out-of-stock"]').items():
                size = size_node.text().strip() + ' - out of stock'
                if size:
                    sizes.append(size)

        # 商品介绍
        introduction = pq('.content:first').text().strip()

        # 商品详情
        details = pq('.content:eq(1)').text().strip()

        # 商品库存
        stock = 0
        stock_text = pq('#addToBasket').text().strip()
        if stock_text == 'Add to bag':
            stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'now_price': now_price, 'colors': colors, 'color_links': color_links, 'sizes': sizes,
                'introduction': introduction, 'details': details, 'stock': stock, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
