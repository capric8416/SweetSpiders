# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class WarehouseCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.warehouse.co.uk/gb'  # 首页链接

    WAIT = [3, 5]  # 动态休眠区间

    COOKIES = {'__cfduid': 'd4ac5977ea1c569acd8a0ba4a8c77401a1538991679',
               'dwanonymous_f758a46cbb0dd959721d3545bae0bd49': 'abOJqMOIvLPMNTtUtFAcmhVGGT',
               'cqcid': 'abOJqMOIvLPMNTtUtFAcmhVGGT',
               'siteConfig': 'GB/en',
               '__cq_dnt': '0',
               'dw_dnt': '0',
               'optimizelyEndUserId': 'oeu1539781514864r0.5881001638386643',
               'optimizelyBuckets': '%7B%7D',
               'BVImplmain_site': '4039',
               'BVBRANDID': 'd16d5111-ad29-44a2-b7f1-b040382280b1',
               'dw': '1',
               'dw_cookies_accepted': '1',
               '_ga': 'GA1.3.1140892028.1539781535',
               '_gid': 'GA1.3.559967101.1539781535',
               'cPol': '1539781575799',
               '_cs_c': '1',
               'fm-sess-live': 'eyJ2aXNpdElkIjoiNDk4YjEwOTgtNzc0Zi1hMzk4LWFmNzgtOWY2ZTFjODhhNmMwIn0=',
               'dwac_bcJIkiaaidU1Qaaadm6TUrJI6H': 'UPW-u3XFrq8uBfOZFbxB_XOrFV_lGQL3nmY%3D|dw-only|||GBP|false|Etc%2FGMT|true',
               'sid': 'UPW-u3XFrq8uBfOZFbxB_XOrFV_lGQL3nmY',
               'dwsid': 'lbiRvp5bUhfHA3uzQ1umiLbmOloOh_5Pd2Ao-xEMmODv4B5vOwuNxy36oBe_lEqzi9-asoD53SC0dWe07SHbXQ==',
               'cookie_policy_displayed': '1',
               'closed_dc_popup': '1',
               'OUTFOX_SEARCH_USER_ID_NCOO': '1345510651.4132576',
               'dwsecuretoken_f758a46cbb0dd959721d3545bae0bd49': 'BTlszkf-pFzP1wMWphydUNxNM0g6MCMHJQ==',
               '___rl__test__cookies': '1539833582601',
               'optimizelySegments': '%7B%224946760282%22%3A%22referral%22%2C%226505610611%22%3A%22true%22%2C%224901416268%22%3A%22false%22%2C%224953272502%22%3A%22gc%22%2C%224941102662%22%3A%22none%22%7D',
               'BVBRANDSID': 'ae59b0c2-0d1b-4179-a711-c03633c70723',
               '_cs_id': '38a6a792-6702-a93d-cc5d-4987e63e2029.1539781803.5.1539835473.1539835444.1513937458.1573945803654',
               '_cs_s': '3.0',
               'stc111904': 'env:1539835465%7C20181118040425%7C20181018043433%7C2%7C1018432:20191018040433|uid:1539781535294.1072745320.191833.111904.1590101022.:20191018040433|srchist:1018433%3A1539829592%3A20181118022632%7C1018432%3A1539835465%3A20181118040425:20191018040433|tsa:1539835465543.1026036157.9892097.7257133501007678.:20181018043433',
               '_ceg.s': 'pgs0nm',
               '_ceg.u': 'pgs0nm',
               'eds': 'INS-vn18-710111774:596771291-1539835476',
               'ecos.dt': '1539835994820'}

    def __init__(self):
        super(WarehouseCrawler, self).__init__()

        # 商品店铺
        self.store = "Warehouse London"

        # 商品品牌
        self.brand = "Warehouse London"

        # 店铺ID
        self.store_id = '675'

        # 品牌ID
        self.brand_id = '230'

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('ul.header_navigation > li')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('.menu-wrapper > .content_wrapper > ul > li.first')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('a').text().strip()
                cat2_url = cat1_url
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                cat3_nodes = cat2_node.children('ul > li')
                for cat3_node in cat3_nodes.items():
                    cat3_name = cat3_node.children('a').text().strip()
                    if ('all' or 'All' or 'Seasonal') in cat3_name:
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
            if pq('.bottom .pagination .page-last .page-next'):
                next_page = self._full_url(url_from=resp.url,
                                           path=pq('.bottom .pagination .page-last .page-next').attr('href'))
                if next_page:
                    url = next_page
                else:
                    break
            else:
                break

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('.grid-tile .product-tile-grid .product-tile .product-name')
        for detail in node.items():
            url = self._full_url(url_from=resp.url,
                                 path=detail.children('a.name-link').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1].partition('.')[0]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('ul.main_image_carousel > li .image_crop_content .image_crop a').items():
            img = self._full_url(url_from=resp.url, path=img_node.attr('href'))
            if img:
                images.append(img)

        # 商品名称
        name = pq('.product_details .product_title_content .product_name').text().strip()

        # 商品价格
        was_price = pq('.price-container .product-price .price-standard').text().strip()
        now_price = pq('.price-container .product-price .price-sales').text().strip()
        if not (was_price and now_price):
            now_price = pq('.price-container .price-sales').text().strip()

        # 商品颜色链接
        color_links = []
        for color_node in pq('.colour-swatches-container li a').items():
            color_link = self._full_url(url_from=resp.url,
                                        path=color_node.attr('style').partition('(')[-1].partition(')')[0])
            if color_link:
                color_links.append(color_link)

        # 商品颜色文字
        colors = []
        for color_node in pq('.colour-swatches-container li a').items():
            color = color_node.attr('title')
            if color:
                colors.append(color)

        # 商品尺寸
        sizes = []
        for size_node in pq('.size li[class="emptyswatch unselectable out-of-stock"]').items():
            size = size_node.children('a').text().strip() + ' - out of stock'
            sizes.append(size)
        for size_node in pq('.size li[class!="emptyswatch unselectable out-of-stock"]').items():
            size = size_node.children('a').text().strip()
            sizes.append(size)

        # 商品介绍
        introduction = pq('#product_description .toggle_content').text().strip()

        # 商品详情
        details = pq('#product_description .product-additional-info').text().strip()

        # 尺寸指导

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'was_price': was_price, 'now_price': now_price, 'color_links': color_links,
                'colors': colors, 'sizes': sizes, 'introduction': introduction, 'details': details, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
