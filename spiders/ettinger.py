# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class EttingerCrawler(IndexListDetailCrawler):
    """

    """

    INDEX_URL = 'https://www.ettinger.co.uk/'

    WAIT = [1, 5]

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)

        cat1 = pq('.navmenu__parent-item')
        for cat1_item in cat1.items():
            cat1_name = cat1_item('a:eq(0)').text().strip()
            if cat1_name in ('About Us', 'Journal'):
                continue

            child_categories = cat1_item('.navmenu__submenu .container .navmenu__submenu-heading a')
            for cat2 in child_categories.items():
                cat2_name = cat2.text().strip()
                cat2_url = self._full_url(url_from=resp.url, path=cat2.attr('href'))
                if not cat2_name:
                    continue
                for cat3 in cat1_item('.navmenu__submenu .container ul a').items():
                    cat3_name = cat3.text().strip()
                    if not cat3_name:
                        continue

                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat3_url = self._full_url(url_from=resp.url, path=cat3.attr('href'))

                    yield cat3_url, headers, resp.cookies.get_dict(), \
                          {'categories': [(cat1_name,), (cat2_name, cat2_url), (cat3_name, cat3_url)]}

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫"""

        page, params = 1, None
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

            if not pq('.container .col-sm-2 a').text().strip():
                break

            page += 1
            params = {'page': page}

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        for product_card in pq('.category .container .category__grid .product-card').items():
            product_id = product_card('.product-color-swatches a:eq(0)').attr('href').strip('/').split('/')[-2]
            for url in [
                self._full_url(url_from=resp.url, path=a.attr('href'))
                for a in product_card('.product-color-swatches a').items()
            ]:
                meta['product_id'] = product_id
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        images = []
        thumbnails = []

        title = pq('.product-full__title .spaced-letters-sm')
        style = title('span:eq(0)').text()
        name = title('span:eq(1)').text()
        price = pq('.product-full__price .attribute-price').text()
        color = pq('.product-full__color p').text()
        item_code = pq('.product-full__item-code .ezstring-field').text()
        description = pq('.product-full__description .ezxmltext-field p').text()

        big_picture_node = pq('.gallery .carousel .item picture')
        for big_picture_url in big_picture_node.items():
            big_picture_link = big_picture_url('img').attr('src')
            images.append(big_picture_link)

        small_picture_node = pq('.carousel .carousel-indicators li')
        for small_picture in small_picture_node.items():
            small_picture_link = small_picture('img').attr('src')
            thumbnails.append(small_picture_link)

        return {
            'url': url, 'product_id': meta['product_id'], 'cat1_name': meta['categories'][0][0],
            'cat1_url': meta['categories'][0][1], 'cat2_name': meta['categories'][1][0],
            'cat2_url': meta['categories'][1][1], 'cat3_name': meta['categories'][2][0],
            'cat3_url': meta['categories'][2][1], 'title': title.text(), 'style': style, 'name': name,
            'price': price, 'color': color, 'item_code': item_code, 'description': description,
            'thumbnails': thumbnails, 'images': images,
        }
