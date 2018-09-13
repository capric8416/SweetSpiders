# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class HarveynicholsCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.harveynichols.com/int/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    COOKIES = {'_ga': 'GA1.2.571249973.1536298292',
               'bfx.notice': '1',
               'pxvid': '4783b010-b25f-11e8-bbb3-03121100c723',
               '_pxvid': '4783b010-b25f-11e8-bbb3-03121100c723',
               'CACHED_FRONT_FORM_KEY': 'GRhAhXn1RExNyvnb',
               'CACHED_FRONT_FORM_KEY': 'GRhAhXn1RExNyvnb',
               'bfx.country': 'CN',
               'bfx.currency': 'CNY',
               '_gid': 'GA1.2.274605429.1536635833',
               'frontend': 'pme3a53t5bih63hv3ajm5j75ed',
               'cookies_populated': '1',
               'CART_ITEMS_QUANTITY': '%7B%22default%22%3A0%2C%22int%22%3A0%7D',
               'CART_TOTAL': '%7B%22default%22%3A%7B%22subtotal%22%3A0%2C%22grand_total%22%3Anull%2C%22giftwrapping%22%3A0%7D%2C%22int%22%3A%7B%22subtotal%22%3A0%2C%22grand_total%22%3Anull%2C%22giftwrapping%22%3A0%7D%7D',
               'bfx.apiKey': '905a6eb0-39f3-11e5-9401-4dc36b918636',
               'bfx.currency': 'CNY',
               'bfx.language': 'zh',
               'bfx.sessionId': '5df132b1-b38e-430b-8867-08a16a408946',
               'bfx.isInternational': 'true',
               'bfx.currencyQuoteId': '60096984',
               'bfx.lcpRuleId': '',
               'cbt-consent-banner': 'CROSS-BORDER%20Consent%20Banner',
               '_pxff_tm': '1',
               ' _dc_gtm_UA-1006476-1': '1',
               '_px2': 'eyJ1IjoiZmQ1M2Y1NzAtYjU3MS0xMWU4LWFhM2MtMmRiZGVlODE4MjEyIiwidiI6IjQ3ODNiMDEwLWIyNWYtMTFlOC1iYmIzLTAzMTIxMTAwYzcyMyIsInQiOjE1MzY2MzY2ODM4MTYsImgiOiI1M2IzMjVhOGE1ZWFjZTIxYmRjYzQwZDYzYjI4MGFhNjkwM2Q1NWE1OGJhOTFhZDFkODFiNDZlMmI5ZGQxYjRmIn0=',
               '_px3': 'a95e3aff24a99f423c87f5294e94e1cf2f8c7fad3d96c6d1e79dcd46c24ee15c:Hscaou84GlnuzatIvisqgoOFxL8ZU0UaEgryPpqkU4rEFXOjv+Ds4/v4UvvI/pfJ1zz4pKfoF+brYrE20x2YwA==:1000:Bd2NptS0/ySDJZ0CMy/7sz2XGDPZqecPa2sOeBWWbRd3h3v4O7fN6JEQmu7lRaDwC19XBik1GwCgjLd1DdlTaFWVfLTOiEkHOVz6Y9ZE+XajZxhtMpRvhTkOHaSIlnAy8pMBrK1p/8GWKT64LSqEfzP9YYI0QBqk9ZINe3i2870='}

    def __init__(self):
        super(HarveynicholsCrawler, self).__init__()

        # 商品店铺
        self.store = "Harvey Nichols"

        # 商品品牌
        self.brand = "Harvey Nichols"

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

        tops = pq('.nav-cats ul.nav-cats__list--lv1 > li.nav-cats__item--lv1')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a.nav-cats__link--lv1 .nav-cats__item-text-1').text().strip()
            if cat1_name == 'News':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a.nav-cats__link--lv1').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('div.nav-cats__wrap--lv2 > ul.nav-cats__list--lv2 > li.nav-cats__item--lv2')
            for cat2_node in cat2_nodes.items():
                if cat2_node.children('a.nav-cats__link--lv2 .nav-cats__item-text-1'):
                    cat2_name = cat2_node.children('a.nav-cats__link--lv2 .nav-cats__item-text-1').text().strip()
                    if not cat2_name:
                        continue
                    cat2_url = self._full_url(url_from=resp.url,
                                              path=cat2_node.children('a.nav-cats__link--lv2').attr('href'))
                else:
                    cat2_name = cat2_node.children('p.nav-cats__text--lv2 .nav-cats__item-text-1').text().strip()
                    if not cat2_name:
                        continue
                    cat2_url = self.INDEX_URL
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                cat3_nodes = cat2_node.children(
                    'div.nav-cats__wrap--lv3 > ul.nav-cats__list--lv3 > li.nav-cats__item--lv3')
                for cat3_node in cat3_nodes.items():
                    cat3_name = cat3_node.children('a.nav-cats__link--lv3 .nav-cats__item-text-1').text().strip()
                    if not cat3_name:
                        continue
                    cat3_url = self._full_url(url_from=resp.url,
                                              path=cat3_node.children('a.nav-cats__link--lv3').attr('href'))

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
            if pq('ul.pagination__links li.pagination__item:last a.pagination__link'):
                next_page = self.INDEX_URL + pq(
                    'ul.pagination__links li.pagination__item:last a.pagination__link').attr(
                    'href')
                if next_page:
                    url = next_page
            else:
                break

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.items .items__list div.items__item')
        for detail in node.items():
            url = self.INDEX_URL + detail.children('a').attr('href')
            if url:
                meta['product_id'] = urlparse(url).path.strip('/').split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('.p-images__preview-swatches li img').items():
            img_url = img_node.attr('src').split('?')[0]
            if img_url:
                images.append(img_url)

        # 商品名称
        product_brand = pq('.p-details .p-details__content .p-details__meta-brand').text().strip()
        product_name = pq('.p-details .p-details__content .p-details__name-wishlist-wrap').text().strip()
        name = product_brand + ':' + product_name

        # 商品价格
        now_price = pq(
            '.p-details .p-details__content .p-details__price .product-price .product-price__regular').text().strip()

        # 商品介绍
        introduction = pq(
            '.pdp__moreinfo .p-more-info__content .p-more-info__inner .p-more-info__html--details').text().strip()

        # 商品详情
        details = pq(
            '.pdp__moreinfo .p-more-info__content .p-more-info__inner .p-more-info__html--infocare').text().strip()

        # 商品颜色文字
        colors = []
        for color_node in pq('.sku-swatches__list li.sku-swatches__item--selected .sku-swatches__tooltip').items():
            color = color_node.text().strip()
            if color:
                colors.append(color)

        # 商品颜色链接　
        color_links = []
        for color_link_node in pq('.sku-swatches__list li.sku-swatches__item--selected .sku-swatches__image').items():
            color_link = color_link_node.attr('src')
            if color_link:
                color_links.append(color_link)

        # 商品尺寸
        sizes = []
        if pq('.sku-labels .sku-labels__list .sku-labels__item'):
            for size_node in pq('.sku-labels .sku-labels__list .sku-labels__item').items():
                size = size_node.text().strip()
                sizes.append(size)
        else:
            for size_node in pq(
                    '.sku-dropdown__fake-select:first .sku-dropdown__available-options .sku-dropdown__option--sold-out').items():
                size = size_node.text().strip() + '--sold out'
                if size:
                    sizes.append(size)
            for size_node in pq(
                    '.sku-dropdown__fake-select:first .sku-dropdown__available-options li[class!="sku-dropdown__option  sku-dropdown__option--sold-out"]').items():
                size = size_node.text().strip()
                if size:
                    sizes.append(size)

        # 商品库存
        stock = 0
        stock_text = pq('.p-details__add-to-bag').text().strip()
        if stock_text == 'Add to bag':
            stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'now_price': now_price, 'introduction': introduction, 'details': details,
                'colors': colors, 'color_links': color_links, 'sizes': sizes, 'stock': stock, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
