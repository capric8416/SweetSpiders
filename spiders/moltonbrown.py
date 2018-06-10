# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class MoltonbrownCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.moltonbrown.co.uk/store/index.jsp'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(MoltonbrownCrawler, self).__init__()

        # 商品店铺
        self.store = "Molton Brown"

        # 商品品牌
        self.brand = "Molton Brown"

        # 店铺ID
        self.store_id = 210

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 364

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('.mainmenu .nav li.dropdown')
        for cat1_node in top.items():
            cat1_name = cat1_node('a:eq(0)').text().strip()
            if cat1_name == 'Fragrance':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node('a:eq(0)').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            child = cat1_node('.sub-menu > div > div a')
            for cat2_node in child.items():
                cat2_name = cat2_node.text().strip()
                if 'Bestsellers' in cat2_name:
                    break
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node('a').attr('href'))

                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url

                cat1['children'].append({
                    'name': cat2_name, 'url': cat2_url,
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                })

                results.append([
                    cat2_url, headers, resp.cookies.get_dict(),
                    {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url)]}
                ])

            categories.append(cat1)

        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""
        pageSize = 12
        params = {}
        p = 1
        while True:
            resp = self._request(
                url=url, params=params, headers=headers, cookies=cookies,
                rollback=self.push_category_info, meta=meta
            )
            if not resp:
                return

            pq = PyQuery(resp.text)

            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            pagination = pq('#viewAllBottom #atg_store_pagination')
            li = pagination('li')
            li_active = pagination('li.active')
            li_next = pagination('li.atg_store_paginationNext')

            if any([not li, li_active and li[-1] == li_active[0], li_next and li[-2] == li_active[0]]):
                break

            p += 1
            params.update({'p': p, 'pageSize': pageSize})

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#atg_store_prodList ul.atg_store_product li.item')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('#catQuickView a:eq(0)').attr('href'))
            meta['product_id'] = urlparse(url.strip('/')).path.split('/')[-1]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img in pq('.prod-img-section .alternate-carousel .treat-items img').items():
            img_url = self._full_url(url_from=resp.url, path=img.attr('src').replace('_S', '_XL'))
            images.append(img_url)

        # 商品名称
        name = pq('.product-detail .header-position h2').text().strip()

        # 商品价格
        price = pq('#addToCart .pricePoint').text().strip().split()[0]

        # 商品介绍
        introduction = []
        for p in pq('.product-detail > .productDetail .productDetailTabs li.collapsible').items():
            title_text = p('h3').text().strip()
            if title_text == 'DELIVERY':
                break
            content = p('.collapsibleContent').text().strip()
            full_content = title_text + ':' +  content
            introduction.append(full_content)

        # 商品规格
        size = pq('.productDetail .Pcodespaceremove span').text().strip().partition(':')[-1].strip()

        # 商品库存
        stock_text = pq('#addToCart > li .atg_store_pickerActions .atg_store_availability span').text().strip()
        if not stock_text:
            stock = 999
        else:
            stock = 0

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'price': price, 'introduction': introduction, 'size': size, 'stock': stock,
            'store': self.store, 'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id,
            'coin_id': self.coin_id
        }
