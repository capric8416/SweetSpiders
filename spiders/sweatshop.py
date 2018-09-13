# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class SweatshopCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.sweatshop.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(SweatshopCrawler, self).__init__()

        # 商品店铺
        self.store = "Sweat Shop"

        # 商品品牌
        self.brand = "Sweat Shop"

        # 店铺ID
        self.store_id = 1283

        # 品牌ID
        self.brand_id = 379

        # 货币ID
        self.coin_id = 1

    def _parse_index(self, resp):
        """首页解析器"""

        results = []
        categories = []
        index_link = 'https://www.sweatshop.com/DesktopModules/SharedControls/API/CommonService/GetMenuMarkup?MenuType=desktop'
        resp = self._request(url=index_link, headers=self.headers)
        nodes = resp.json()['Nodes']
        for top in nodes:
            cat1_name = top['Name']
            cat1_url = self.INDEX_URL.strip('/') + top['Url']
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name)}

            for cat2_node in top['Children']:
                cat2_name = cat2_node.get('Name')
                if (not cat2_name) or ('ViewAll' in cat2_name):
                    break
                cat2_url = self.INDEX_URL.strip('/') + cat2_node['Url']
                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                for cat3_node in cat2_node['Children']:
                    cat3_name = cat3_node.get('Name')
                    if (not cat3_name) or ('ViewAll' in cat3_name):
                        break
                    cat3_url = self.INDEX_URL.strip('/') + cat3_node['Url']

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
            if pq('.PageNumberInner:last a.swipeNextClick'):
                next_page = self.INDEX_URL.strip('/') + pq('.PageNumberInner:last a.swipeNextClick').attr('href')
                if next_page:
                    url = next_page
            else:
                break

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#navlist > li')
        if node('.s-productthumbbox .TextSizeWrap .s-producttext-top-wrapper > a'):
            for detail in node.items():
                url = self.INDEX_URL.strip('/') + detail.children(
                    '.s-productthumbbox .TextSizeWrap .s-producttext-top-wrapper > a').attr('href')
                if url:
                    meta['product_id'] = urlparse(url).path.split('/')[-1]
                    yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#piThumbList > li > a').items():
            img = img_node.attr('href')
            if img:
                images.append(img)

        # 商品名称
        product_brand = pq('#lblProductBrand').text().strip()
        product_name = pq('#lblProductName').text().strip()
        name = product_brand + ':' + product_name

        # 商品价格
        was_price = pq('.pdpPriceRating .originalprice').text().strip()
        now_price = pq('.pdpPriceRating .pdpPrice').text().strip()

        # 商品介绍
        introduction = pq('#divProductInfoTab').text().strip()

        # 商品颜色文字
        colors = []
        if pq('.colourImages > li.variantHighlight img'):
            for color_node in pq('.colourImages > li.variantHighlight img').items():
                color = color_node.attr('alt')
                if color:
                    colors.append(color)
        else:
            color = pq('#divColour .s-productextras-column-2-3').text().strip()
            colors.append(color)

        # 商品颜色链接
        color_links = []
        for color_link_node in pq('.colourImages > li.variantHighlight img').items():
            color_link = color_link_node.attr('src')
            if color_link:
                color_links.append(color_link)

        # 商品尺寸
        sizes = []
        for size_node in pq('ul.sizeButtons > li[class="tooltip sizeButtonli "] a').items():
            size = size_node.text().strip()
            if size:
                sizes.append(size)
        for size_node in pq('ul.sizeButtons > li[class="tooltip sizeButtonli greyOut"] a').items():
            size = size_node.text().strip() + '--sold out'
            if size:
                sizes.append(size)

        # 商品库存
        stock = 0
        stock_text = pq('.ImgButWrap .addToBag').text().strip()
        if stock_text == 'Add to bag':
            stock = 999

        return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
                'colors': colors, 'color_links': color_links, 'sizes': sizes, 'stock': stock, 'store': self.store,
                'brand': self.brand, 'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
                }
