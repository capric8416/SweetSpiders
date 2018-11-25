# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class CachecacheCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.cache-cache.fr/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(CachecacheCrawler, self).__init__()

        # 商品店铺
        self.store = "cache cache"

        # 商品品牌
        self.brand = "cache cache"

        # 店铺ID
        self.store_id = '3011'

        # 品牌ID
        self.brand_id = '746'

        # 货币ID
        self.coin_id = 3

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('#mainNav > .bigTtl span.collec')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name in ('Nouveautés', 'Petits prix'):
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

            if cat1_name == 'Offre du moment':
                break

            if cat1_name == 'Collection':
                cat1_url = self.INDEX_URL
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

                cat2_nodes = pq('.catalog:first .menuBox .sousCat .inner a')
                for cat2_node in cat2_nodes.items():
                    cat2_name = cat2_node.text().strip()
                    if (not cat2_name) or (cat2_name == 'Carte cadeau'):
                        continue
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

            if not pq('.pages:last li.pagin-number'):
                break

            if len(pq('.pages:last li.pagin-number')) == 2:
                next_page = self._full_url(url_from=resp.url,
                                           path=pq('.pages:last li.pagin-number:last a').attr('href'))
                if not next_page:
                    break
                url = next_page

            if len(pq('.pages:last li.pagin-number')) > 2:
                if pq('.pages:last li.pagin-number') and pq('.pages:last a.next'):
                    next_page = self._full_url(url_from=resp.url, path=pq('.pages:last a.next').attr('href'))
                    url = next_page
                else:
                    next_page = self._full_url(url_from=resp.url,
                                               path=pq('.pages:last li.pagin-number:last a').attr('href'))

                    if (not next_page) or (next_page == resp.url):
                        break

                    url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.grid li div.img').next('a')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail.attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1].partition('.')[0]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('.gal #gallery > ul > li img').items():
            img = img_node.attr('src')
            if img:
                images.append(img)

        # 商品价格(本网站没有原价)
        now_price = pq('.price .current').text().strip()

        # 商品名称
        name = pq('h1.stickyHide').text().strip()

        # 商品颜色
        color_links = []
        for color_link_node in pq('.colors li[dsp_e_reservation="1"] img').items():
            color_link = color_link_node.attr('src')
            if color_link:
                color_links.append(color_link)

        # 商品颜色文本
        colors = []
        for color_node in pq('.colors li[dsp_e_reservation="1"] img').items():
            color = color_node.attr('alt')
            if color:
                colors.append(color)

        # 商品尺寸
        sizes = []
        color_size = {}
        for each in pq('ul.sizes li').items():
            key = each.attr('couleur')
            value = each.text().strip()

        # 商品介绍
        introduction = pq('.content .innerContent .desc').text().replace('\n', '').strip()

        # 商品详情
        details = pq('.content .innerContent .ref').text().strip() + pq('.content .innerContent .comp').text().strip()

        # 商品库存
        stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'now_price': now_price, 'color_links': color_links, 'colors': colors, 'sizes': sizes,
                'introduction': introduction, 'details': details, 'stock': stock, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
