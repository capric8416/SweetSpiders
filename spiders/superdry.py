# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class SuperdryCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.superdry.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(SuperdryCrawler, self).__init__()

        # 商品店铺
        self.store = "Superdry"

        # 商品品牌
        self.brand = "Superdry"

        # 店铺ID
        self.store_id = 613

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 451

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('#main-menu > .menu > li')
        for cat1_node in top.items():
            cat1_name = cat1_node('span:eq(0)').text().strip()
            if cat1_name in ('Home', 'new in'):
                continue
            if cat1_name == 'mens':
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))

                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name)}
                cat2_node = pq('#holdermens .menu-section li')
                for cat2s in cat2_node.items():
                    cat2_name = cat2s.text().strip()
                    if cat2_name in (
                            'New In', 'Trending Now', 'Holiday Shop', 'Festival Style', 'Superdry Sport', 'outerwear',
                            'tops',
                            'bottoms', 'accessories', 'Footwear'):
                        continue
                    cat2_url = self._full_url(url_from=resp.url, path=cat2s.children('a').attr('href'))

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
            if cat1_name == 'womens':
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))

                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name)}
                cat2_node = pq('#holderwomens .menu-section li')
                for cat2s in cat2_node.items():
                    cat2_name = cat2s.text().strip()
                    if cat2_name in (
                            'New In', 'Trending Now', 'Holiday Shop', 'Festival Style', 'Superdry Sport', 'outerwear',
                            'tops',
                            'bottoms', 'accessories', 'Footwear'):
                        continue
                    cat2_url = self._full_url(url_from=resp.url, path=cat2s.children('a').attr('href'))

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
            if cat1_name == 'Sport':
                cat1_url = self._full_url(url_from=resp.url, path=cat1_node.children('a').attr('href'))
                cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}
                headers = copy.copy(self.headers)
                headers['Referer'] = resp.url
                resp = self._request(url=cat1_url, headers=headers, cookies=resp.cookies.get_dict())
                pq = PyQuery(resp.text)
                cat2_node = pq('#ul12027 li.parent')
                for cat2s in cat2_node.items():
                    cat2_name = cat2s.children('span').text().strip()
                    cat2_url = None
                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }
                    for cat3s in cat2s.children('ul li').items():
                        cat3_name = cat3s.children('a').text().strip()
                        if cat3_name == 'View All':
                            break
                        cat3_url = self._full_url(url_from=resp.url, path=cat3s.children('a').attr('href'))

                        headers = copy.copy(self.headers)
                        headers['Referer'] = resp.url

                        cat2['children'].append({
                            'name': cat3_name, 'url': cat3_url,
                            'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                        })

                        results.append([
                            cat3_url, headers, resp.cookies.get_dict(),
                            {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url), (cat3_name, cat3_url)]}
                        ])

                    cat1['children'].append(cat2)

                categories.append(cat1)

        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies,
                rollback=self.push_category_info, meta=meta)
            if not resp:
                return
            pq = PyQuery(resp.text)
            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url, path=pq('link[rel="next"]').attr('href'))
            if len(pq('.category-products ul.products-grid li.item')) < 48:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#product-list div.table li.hproduct div.info')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail.children('a').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img in pq(
                '.left-hand-column .product_images .thumbnail_scroller .thumbnail_item img.product_image_thumbnail').items():
            img_url = img.attr('src').replace('products/', 'products/zoom/')
            if img_url:
                images.append(img_url)

        # 商品名称
        name = pq('.right-col-container .product-header h1.sidebar-header').text().strip()

        # 商品价格
        now_price = pq('.right-col-container .product-header span.price').text().strip()

        # 商品颜色
        colors = []
        for color_node in pq('.right-col-container .alternate-colour-container .thumbnail_item img').items():
            color_url = color_node.attr('src')
            if color_url:
                colors.append(color_url)

        # 商品尺码
        sizes = []
        for size_node in pq('.size-box-container:eq(0) div[class!="size-box invalid"]').items():
            size = size_node.text().strip()
            if size:
                sizes.append(size)
        for size_node in pq('.size-box-container:eq(0) div[class="size-box invalid"]').items():
            size = size_node.text().strip() + ' -- out of stock'
            if size:
                sizes.append(size)

        # 商品介绍
        introduction = pq(
            '.product_information_container .product_information .descriptionContainer').text().strip()

        # 商品详情
        detail1 = pq(
            '.product_information_container .product_information .accordion-container .bottom-accordion:eq(0) .accordion-content .specification-row:eq(0) .col-md-6:eq(1) table').text().strip()

        detail2 = pq(
            '.product_information_container .product_information .accordion-container .bottom-accordion:eq(0) .accordion-content .specification-row:eq(1) .col-md-6:eq(0) table').text().strip()
        detail = detail1 + ';' + detail2

        # 尺寸指导
        # 尺寸指导是两张图片
        size_guide = []
        for guide in pq(
                '.product_information_container .product_information .accordion-container .bottom-accordion:eq(1) .accordion-content img').items():
            size_guide_img = guide.attr('src')
            if size_guide_img:
                size_guide.append(size_guide_img)

        # 商品库存
        stock = 999

        return {
            'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'now_price': now_price, 'colors': colors, 'sizes': sizes, 'introduction': introduction,
            'detail': detail, 'size_guide': size_guide, 'stock': stock, 'store': self.store, 'brand': self.brand,
            'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
