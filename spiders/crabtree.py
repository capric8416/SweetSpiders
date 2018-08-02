# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from SweetSpiders.scripts.google_translate import GoogleTranslate
from pyquery import PyQuery


class CrabtreeCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'http://www.crabtree-evelyn.com/uk/en'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(CrabtreeCrawler, self).__init__()

        # 商品店铺
        self.store = "Crabtree & Evelyn"

        # 商品品牌
        self.brand = "Crabtree & Evelyn"

        # 店铺ID
        self.store_id = 541

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 270

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []
        g = GoogleTranslate()

        top = pq('.accordion-topmenu:eq(1) .sub-level .menu-vertical .accordion-submenus')
        for top_node in top.items():
            cat1_name = top_node('a.accordion-submenu-toggle').text().strip()
            if cat1_name == 'Fragrance':
                continue
            elif cat1_name == 'Collection Rituals':
                break
            elif cat1_name in ('Hair Care', "Men's", 'Gifts'):
                cat1_url = top_node('a.accordion-submenu-toggle').attr('href').strip()
                cat1 = {'name': cat1_name, 'name_cn': g.query(source=cat1_name), 'url': cat1_url,
                        'uuid': self.cu.get_or_create(cat1_name)}

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                cookies = resp.cookies.get_dict()

                results.append([
                    cat1_url, headers, cookies,
                    {'categories': [(cat1_name, g.query(source=cat1_name), cat1_url)]}
                ])

                categories.append(cat1)

            else:
                cat1_url = top_node('a.accordion-submenu-toggle').attr('href').strip()
                cat1 = {'name': cat1_name, 'name_cn': g.query(source=cat1_name), 'url': cat1_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name)}
                child = top_node('ul.level-3 .accordion-childmenu-label')
                for child_node in child.items():
                    cat2_name = child_node('a.sliding-u-click').text().strip()
                    cat2_url = child_node('a.sliding-u-click').attr('href').strip()

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url
                    cookies = resp.cookies.get_dict()

                    cat1['children'].append({
                        'name': cat2_name, 'name_cn': g.query(source=cat2_name), 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.extend([
                        [
                            cat1_url, headers, cookies,
                            {'categories': [(cat1_name, g.query(source=cat1_name), cat1_url)]}
                        ],
                        [
                            cat2_url, headers, cookies,
                            {'categories': [(cat1_name, g.query(source=cat1_name), cat1_url),
                                            (cat2_name, g.query(source=cat2_name), cat2_url)]}
                        ]
                    ])

                categories.append(cat1)

        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""
        # http://www.crabtree-evelyn.com/uk/en/body-care/bath-soaks/?sz=12&start=0&format=page-element
        start = 0
        sz = 12
        format = 'page-element'
        params = {'sz': sz, 'start': start, 'format': format}
        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies, params=params,
                rollback=self.push_category_info, meta=meta
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            if not pq('.infinite-scroll-placeholder').attr('data-grid-url'):
                break

            start += 12
            params.update({'start': start})

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.product-tile-wrapper')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail(
                '.product-info .product-list-item .product-name .name-link').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        imgs = []
        # if pq('.product-add-to-cart .product-variations .attribute .value .variation-select  option'):
        #     for img in pq(
        #             '.product-add-to-cart .product-variations .attribute .value .variation-select  option').items():
        #         img_url = json.loads(img.attr('data-lgimg'))['url']
        #         imgs.append(img_url)
        # else:
        for img in pq('#pdpMain .product-image .primary-image').items():
            img_url = img.attr('src')
            if img_url.startswith('http://media'):
                imgs.append(img_url)
        imgs = list(set(imgs))

        # 商品名称
        name = pq('.cols .product-detail .product-name').text().strip()

        # 商品原价
        was_prices = []
        was_price = pq('.product-content .product-price-amount .price-standard').text().strip()

        # 商品现价
        now_prices = []
        now_price = pq(
            '.purchase-area .product-content .product-price .price-sales-pinned').text().strip()
        if not (was_price and now_price):
            now_price = pq(
                '.product-col-2 .purchase-area .product-content .product-price .price-sales').text().strip() or pq(
                '.set-purchase-area .product-price .salesprice').text().strip()
        was_prices.append(was_price)
        now_prices.append(now_price)

        # 商品介绍
        introduction = pq('.product-content .short-description p').text().strip()
        if pq('.product-content .short-description ul'):
            for li in pq('.product-content .short-description ul li').items():
                li_text = li('b').text().strip()
                introduction += li_text

        # 商品描述
        p1 = pq('.cae__container .cae__explore-further-content .cae__h2').text().strip()
        p2 = pq('.cae__container .cae__explore-further-content .cae__content').text().strip()
        p3 = pq('.cae__hidden-mobile .cae__h4').text().strip()
        p4 = pq('.cae__container .cae__hidden-mobile .cae__explore-further-usage .cae__content').text().strip()
        description = p1 + p2 + p3 + p4

        # 商品尺寸
        if not pq('.set-purchase-area .product-price .salesprice') and len(
                pq(
                    '.product-col-2 .product-add-to-cart .product-variations .attribute .value .variation-select option')) > 1:
            size = [s.text().strip() for s in
                    pq(
                        '.product-col-2 .product-add-to-cart .product-variations .attribute .value .variation-select option:selected').items()]
            if not size:
                size = [pq('.product-variations .attribute .value input').attr('value')]

            options = pq(
                '.product-col-2 .product-add-to-cart .product-variations .attribute .value .variation-select  option:not(:selected)').items()
            for option in options:
                link = option.attr('value')
                resp = self._request(url=link, headers=extra['headers'], cookies=extra['cookies'])
                pq = PyQuery(resp.text)
                size_2 = pq(
                    '.product-col-2 .product-add-to-cart .product-variations .attribute .value .variation-select  option:selected').text().strip()
                size.append(size_2)
                was_price_2 = pq('.purchase-area .product-content .product-price .price-standard').text().strip()
                now_price_2 = pq('.purchase-area .product-content .product-price .price-sales-pinned').text().strip()
                if not (was_price_2 and now_price_2):
                    now_price_2 = pq('.purchase-area .product-content .product-price .price-sales').text().strip()
                was_prices.append(was_price_2)
                now_prices.append(now_price_2)
                img_50ml = pq('.product-primary-image .pdp-image-slides .primary-image')
                for img_2 in img_50ml.items():
                    img_new = img_2.attr('src')
                    if img_new.startswith('http://media') and img_new.endswith('$large$'):
                        imgs.append(img_new)
        else:
            size = [s.text().strip() for s in
                    pq(
                        '.product-col-2 .product-add-to-cart .product-variations .attribute .value .variation-select option:selected').items()]
            if not size:
                size = [pq('.product-col-2 .product-variations .attribute .value input').attr('value')]
                size = [siz for siz in size if siz]

        # 商品库存
        stock_text = pq('.pdpForm .product-add-to-cart .availability-msg .not-available-msg .status').text().strip()
        if stock_text:
            stock = 0
        else:
            stock = 999

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': imgs,
            'name': name, 'was_price': was_prices, 'now_price': now_prices, 'introduction': introduction,
            'description': description, 'size': size, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id, 'stock': stock
        }


if __name__ == '__main__':
    import requests

    url = 'http://www.crabtree-evelyn.com/uk/en/product/citron-coriander-energising-hand-therapy/citron-coriander-energising-hand-therapy.html?cgid=hand-care'
    resp = requests.get(url)
    spider = CrabtreeCrawler()
    spider._parse_product_detail(url=url, resp=resp, meta={'product_id': None, 'categories': None}, headers={},
                                 cookies={})
