# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import json
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl

from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class AlexandermcqueenCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.alexandermcqueen.com/gb/'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(AlexandermcqueenCrawler, self).__init__()

        # 商品店铺
        self.store = "Alexander McQueen"

        # 商品品牌
        self.brand = "Alexander McQueen"

        # 店铺ID
        self.store_id = 313

        # 货币ID
        self.coin_id = 1

        # 品牌ID
        self.brand_id = 441

    def _parse_index(self, resp):
        """首页解析器"""

        self.headers['Accept-Language'] = 'en-GB'

        pq = PyQuery(resp.text)
        results = []
        categories = []

        sitecode = pq('script:contains("yTos.navigation")').text().strip()
        sitecode = sitecode[sitecode.index('yTos.navigation'):sitecode.index(
            'yTos.configuration')].partition('=')[-1].strip(' \n;')
        sitecode = json.loads(sitecode)['SiteCode'].replace('GROUP', '')

        level_0 = pq('.main_menu .top_menu .level-0 > .menuItem')
        for cat1 in level_0.items():
            cat1_id = cat1.attr('id')
            cat1_name = cat1('a .text').text().strip()
            if cat1_name == 'GIFTS':
                break
            cat1_url = cat1('a').attr('href')
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            level_tmp = pq(f'[data-parent-id="{cat1_id}"] > .menuItem')
            for cat_tmp in level_tmp.items():
                cat_tmp_id = cat_tmp.attr('id')

                level_1 = pq(f'[data-parent-id="{cat_tmp_id}"] > .menuItem')
                for cat2 in level_1.items():
                    cat2_id = cat2.attr('id')
                    cat2_name = pq(f'[id="{cat2_id}"] > a .text').text().strip()
                    if not cat2_name:
                        cat2_name = pq(f'[id="{cat2_id}"] > div .text').text().strip()
                    cat2_url = pq(f'[id="{cat2_id}"] > a').attr('href')
                    cat2 = {
                        'name': cat2_name, 'url': cat2_url, 'children': [],
                        'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                    }

                    level_2 = pq(f'[data-parent-id="{cat2_id}"] > .menuItem')
                    for cat3 in level_2.items():
                        cat3_id = cat3.attr('id')
                        cat3_name = pq(f'[id="{cat3_id}"] > a .text').text().strip()
                        cat3_url = pq(f'[id="{cat3_id}"] > a').attr('href')

                        headers = copy.copy(self.headers)
                        headers['Referer'] = resp.url

                        cat2['children'].append({
                            'name': cat3_name, 'url': cat3_url,
                            'uuid': self.cu.get_or_create(cat1_name, cat2_name, cat3_name)
                        })

                        results.append([
                            cat3_url, headers, resp.cookies.get_dict(),
                            {
                                'sitecode': sitecode,
                                'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url), (cat3_name, cat3_url)]
                            }
                        ])

                    cat1['children'].append(cat2)

            categories.append(cat1)
        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        params = None

        resp = self._request(
            url=url, params=params, headers=headers,
            cookies=cookies, allow_redirects=False,
            rollback=self.push_category_info, meta=meta
        )
        if not resp:
            return

        pq = PyQuery(resp.text)

        for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
            self.push_product_info(info)

        search = pq('script:contains("yTos.search")').text().strip().partition(
            'yTos.search')[-1].partition('typeof')[0].strip(' \n=;if(') or \
                 pq('script:contains("yTos.search")').text().strip().partition('yTos.search')[-1].strip(' \n=;')
        if not search:
            return

        search = json.loads(search)
        search['siteCode'] = meta['sitecode']
        totalpage = int(search.get('totalPages'))

        url = 'https://www.alexandermcqueen.com/Search/RenderProducts'
        params = {
            q: search.get(q)
            for q in [
            'ytosQuery',
            'department',
            'gender',
            'season',
            'site',
            'yurirulename',
            'agerange',
            'page',
            'productsPerPage',
            'suggestion',
            'facetsvalue',
            'totalPages',
            'totalItems',
            'partialLoadedItems',
            'itemsToLoadOnNextPage',
            'siteCode',
            'emptySearchResult'
        ]
        }

        for page in range(2, totalpage + 1):
            params['page'] = page
            resp = self._request(url=url, params=params, headers=headers, meta=meta)

            pq = PyQuery(resp.text)
            for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                self.push_product_info(info)

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        node = pq('article.item')
        if node:
            for detail in node.items():
                url = self._full_url(url_from=resp.url, path=detail('a').attr('href'))
                meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
                yield url, headers, resp.cookies.get_dict(), meta
        else:
            node = pq('.columns-row .outro-section-inner-wrapper')
            for detail in node.items():
                url = self._fix_url(self._full_url(url_from=resp.url, path=detail('a').attr('href')))
                meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
                yield url, headers, resp.cookies.get_dict(), meta

    @staticmethod
    def _fix_url(url):
        p = urlparse(url)
        q = dict(parse_qsl(p.query))

        if 'siteCode' in q and not q['siteCode'].endswith('_GB'):
            q['siteCode'] = q['siteCode'][:-2] + 'GB'
        else:
            return url

        return urlunparse(p._replace(query=urlencode(q)))

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img in pq('.productImages .alternativeImages li').items():
            img_url = img('img').attr('src').replace('_9_', '_18_')
            images.append(img_url)

        # 商品名称
        name = pq('.productName .inner').text().strip()

        # 商品价格
        price = pq('.itemPriceContainer .price .value').text().strip()
        if price == 'Complimentary':
            price = '999999999'  # 没有价格

        # 商品详细介绍
        introduction = pq('.descriptionsContainer .attributesUpdater .value').text().strip()

        #  商品简介
        p1 = pq('.moreDescriptionsContent .fittingWrapper span').text().strip()
        p2 = pq('.moreDescriptionsContent .compositionWrapper span').text().strip()
        p3 = pq('.moreDescriptionsContent .modelFabricColor span').text().strip()
        description = p1 + p2 + p3

        params = {}
        params['siteCode'] = meta['sitecode']

        code10 = urlparse(url).path.split('/')[-1].split('.')[0].partition('cod')[-1]
        params['code10'] = code10
        if not code10:
            params['code10'] = dict(parse_qsl(urlparse(url).query))['cod10']

        link = 'https://www.alexandermcqueen.com/yTos/api/Plugins/ItemPluginApi/GetCombinationsAsync/'
        resp = self._request(url=link, params=params, headers=extra['headers'], cookies=extra['cookies'])
        data = resp.json()

        # 商品颜色
        colors = [c['Description'] for c in data['Colors']]

        # 商品尺寸
        sizes = []
        for s in data['Sizes']:
            if s['Labeled']:
                size = s['Description']
            else:
                size = s['Alternative']['Description']
            if size not in ('', None, 'OneSize'):
                sizes.append(size)

        # 商品库存
        issoldout = data['IsSoldOut']
        if issoldout:
            stock = 0
        else:
            stock = 999

        return {
            'url': url, 'product_id': meta['product_id'], 'categories': meta['categories'], 'images': images,
            'name': name, 'price': price, 'introduction': introduction, 'description': description, 'color': colors,
            'sizes': sizes, 'stock': stock, 'store': self.store, 'brand': self.brand, 'store_id': self.store_id,
            'brand_id': self.brand_id, 'coin_id': self.coin_id
        }
