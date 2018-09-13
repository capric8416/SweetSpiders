# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class CathkidstonCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.cathkidston.com/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(CathkidstonCrawler, self).__init__()

        # 商品店铺
        self.store = "Cath Kidston"

        # 商品品牌
        self.brand = "Cath Kidston"

        # 店铺ID
        self.store_id = 1218

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 357

    def _parse_index(self, resp):
        """首页解析器"""
        pq = PyQuery(resp.text)
        results = []
        categories = []

        top = pq('#navigation ul.level_1 li.level_1')
        for cat1_node in top.items():
            cat1_name = cat1_node('a.level_1').text().strip()
            if cat1_name in ('New In', 'Disney', 'Collections'):
                continue
            if cat1_name == 'Blog':
                break
            cat1_url = self._full_url(url_from=resp.url, path=cat1_node('a.level_1').attr('href'))
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            child = cat1_node('div.level_2 > ul.level_2 > li.level_2')
            for cat2_node in child.items():
                cat2_name = cat2_node('a.level_2').text().strip()
                if 'View All' in cat2_name:
                    continue
                if cat2_name == 'Gift Wrap Service':
                    break
                cat2_url = self._full_url(url_from=resp.url, path=cat2_node('a.level_2').attr('href'))
                if not cat2_node('div.level_3'):
                    headers = copy.copy(self.headers)
                    headers['Referer'] = resp.url

                    cat1['children'].append({
                        'name': cat2_name, 'url': cat2_url,
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    })

                    results.append([
                        cat2_url, headers, resp.cookies.get_dict(),
                        {
                            'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url)],
                        }
                    ])

                else:
                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }
                    for cat3_node in cat2_node('div.level_3 > ul.level_3 > li.level_3').items():
                        cat3_name = cat3_node('a').text().strip()
                        if 'View All' in cat3_name:
                            continue
                        cat3_url = self._full_url(url_from=resp.url, path=cat3_node('a').attr('href'))

                        headers = copy.copy(self.headers)
                        headers['Referer'] = resp.url

                        cat2['children'].append({
                            'name': cat3_name, 'url': cat3_url,
                            'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                        })

                        results.append([
                            cat3_url, headers, resp.cookies.get_dict(),
                            {
                                'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url), (cat3_name, cat3_url)]
                            }
                        ])

                    cat1['children'].append(cat2)

            categories.append(cat1)
        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        while True:
            resp = self._request(
                url=url, headers=headers, cookies=cookies,
                 meta=meta)
            if not resp:
                return
            pq = PyQuery(resp.text)
            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

            next_page = self._full_url(url_from=resp.url,
                                       path=pq('#results .summary_and_sort .pagination:eq(0) .page-next').attr('href'))
            if not next_page:
                break
            url = next_page

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('#results .product_list li.product')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('.product_info .product_title').attr('href'))
            if url:
                meta['product_id'] = urlparse(url).path.split('/')[-1]
                yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        headers = copy.copy(extra['headers'])
        headers['Referer'] = resp.url
        if resp.status_code == 301:
            return
        if not pq('#main_image_container #main_image'):
            return
        img_url = self._full_url(url_from=resp.url,
                                 path=pq('#main_image_container #main_image').attr('src').replace('xlarge', 'zoom'))
        images.append(img_url)
        count = 1
        while True:
            new_img = img_url.replace('.jpg', '_%s.jpg') % count
            resp = self._request(method='head', url=new_img, headers=headers, cookies=resp.cookies.get_dict())
            if resp.status_code == 403:
                break
            count += 1

            images.append(new_img)

        # 商品名称
        name = pq('#info > h1').text().strip()

        # 商品价格
        was_price = pq('#info p[itemprop="offerDetails"]').text()
        if 'Was' in was_price:
            now_price = was_price.partition('Now')[-1].strip()
            was_price = was_price.partition('Was')[-1].partition('Now')[0].strip()

        else:
            now_price = was_price
            was_price = ''

        # 商品尺寸
        sizes = []
        for size_node in pq('.matrix_table td label span').items():
            size = ''.join(size_node.text().strip().split(',')[0].split()[1:])
            sizes.append(size)

        # 尺寸指导
        size_guide = {}
        if pq('.pm_aside a'):
            size_guide_url = self.INDEX_URL + pq('.pm_aside a').attr('href').strip('/')
            resp = self._request(url=size_guide_url, headers=extra['headers'], cookies=extra['cookies'])
            pq = PyQuery(resp.text)

            table1_name = pq('#cms_content .ck-size-guide-item:eq(0) .ck-size-guide-table:eq(0) caption').text().strip()
            table1 = []
            for tr in pq('#cms_content .ck-size-guide-item:eq(0) .ck-size-guide-table:eq(0) tr').items():
                each_size = tr.text().strip()
                table1.append(each_size.replace('\n', ','))

            table2 = []
            for tr in pq('#cms_content .ck-size-guide-item:eq(0) .ck-size-guide-table:eq(1) tr').items():
                each_size = tr.text().strip()
                table2.append(each_size.replace('\n', ','))

            table3_name = pq('#cms_content .ck-size-guide-item:eq(1) .ck-size-guide-table caption').text().strip()
            table3 = []
            for tr in pq('#cms_content .ck-size-guide-item:eq(1) .ck-size-guide-table tr').items():
                each_size = tr.text().strip()
                table3.append(each_size.replace('\n', ','))

            table4_name = pq('#cms_content .ck-size-guide-item:eq(2) .ck-size-guide-table:eq(0) caption').text().strip()
            table4 = []
            for tr in pq('#cms_content .ck-size-guide-item:eq(2) .ck-size-guide-table:eq(0) tr').items():
                each_size = tr.text().strip()
                table4.append(each_size.replace('\n', ','))

            table5_name = pq('#cms_content .ck-size-guide-item:eq(2) .ck-size-guide-table:eq(1) caption').text().strip()
            table5 = []
            for tr in pq('#cms_content .ck-size-guide-item:eq(2) .ck-size-guide-table:eq(1) tr').items():
                each_size = tr.text().strip()
                table5.append(each_size.replace('\n', ','))

            table6_name = pq('#cms_content .ck-size-guide-item:last .ck-size-guide-table:eq(0) caption').text().strip()
            table6 = []
            for tr in pq('#cms_content .ck-size-guide-item:last .ck-size-guide-table:eq(0) tr').items():
                each_size = tr.text().strip()
                table6.append(each_size.replace('\n', ','))

            table7_name = pq('#cms_content .ck-size-guide-item:last .ck-size-guide-table:eq(1) caption').text().strip()
            table7 = []
            for tr in pq('#cms_content .ck-size-guide-item:last .ck-size-guide-table:eq(1) tr').items():
                each_size = tr.text().strip()
                table7.append(each_size.replace('\n', ','))

            size_guide = {'table1_info': {'table1_name': table1_name, 'table1': table1, 'table2': table2},
                          'table3_info': {'table3_name': table3_name, 'table3': table3},
                          'table4_info': {'table4_name': table4_name, 'table4': table4},
                          'table5_info': {'table5_name': table5_name, 'table5': table5},
                          'table6_info': {'table6_name': table6_name, 'table6': table6},
                          'table7_info': {'table7_name': table7_name, 'table7': table7}}
        else:
            size_guide = size_guide

        # 商品介绍
        introduction = pq('#product_info_tabs #tabs-1 p').text().strip()

        # 商品描述
        details = pq('#tabs-2').text().strip()

        # 商品库存
        stock_text = pq('.stock-status-message').text().strip()
        if stock_text == 'Sorry this item is out of stock':
            stock = 0
        else:
            stock = 999

        return {
            'url': url, 'catgories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
            'name': name, 'was_price': was_price, 'now_price': now_price, 'sizes': sizes, 'introduction': introduction,
            'details': details, 'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id, 'size_guide': size_guide
        }
