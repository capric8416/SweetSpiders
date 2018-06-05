# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
from urllib.parse import urlparse

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

        pq = PyQuery(resp.text)
        results = []
        categories = []

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
                            {'categories': [(cat1_name, cat1_url), (cat2_name, cat2_url), (cat3_name, cat3_url)]}
                        ])

                    cat1['children'].append(cat2)

            categories.append(cat1)
        return categories, results

    def _get_product_list(self, url, headers, cookies, meta):
        """列表页面爬虫，实现翻页请求"""

        params = None

        resp = self._request(
            url=url, params=params, headers=headers, cookies=cookies,
            rollback=self.push_category_info, meta=meta
        )
        if not resp:
            return

        pq = PyQuery(resp.text)

        for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
            self.push_product_info(info)

        search = pq('script:contains("yTos.search")').text().strip().partition('yTos.search')[-1].strip(' \n=;')
        search = json.loads(search)

        sitecode = pq('script:contains("yTos.navigation")').text().strip()
        sitecode = sitecode[sitecode.index('yTos.navigation'):sitecode.index('yTos.configuration')].partition('=')[
            -1].strip(' \n;')
        sitecode = json.loads(sitecode)['SiteCode']
        search['siteCode'] = sitecode
        totalpage = int(search.get('totalPages'))
        page = int(search.get('page'))

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

        node = pq('#wcrssbdbgs_spl .shelfContainer  .products  article. item')
        for detail in node.items():
            url = self._full_url(url_from=resp.url, path=detail('a').attr('href'))
            meta['product_id'] = urlparse(url).path.split('/')[-1][:-5]
            yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta):
        """详情页解析器"""

        raise NotImplementedError
