# -*- coding: utf-8 -*-
# !/usr/bin/env python
import copy
import json
from urllib.parse import urlparse
from urllib.parse import unquote
from SweetSpiders.common import IndexListDetailCrawler
from pyquery import PyQuery


class AlexanderwangCrawler(IndexListDetailCrawler):
    """
    
    """

    INDEX_URL = 'https://www.alexanderwang.com/fr'  # 首页链接

    WAIT = [1, 3]  # 动态休眠区间

    def __init__(self):
        super(AlexanderwangCrawler, self).__init__()

        # 商品店铺
        self.store = "Alexander Wang"

        # 商品品牌
        self.brand = "Alexander Wang"

        # 店铺ID
        self.store_id = 1845

        # 品牌ID
        self.brand_id = '暂无'

        # 货币ID
        self.coin_id = 3

    def _parse_index(self, resp):
        """首页解析器"""

        pq = PyQuery(resp.text)
        results = []
        categories = []

        tops = pq('.mainMenu .level-0 > ul > li.menuItem')
        for cat1_node in tops.items():
            cat1_name = cat1_node.children('a').text().strip()
            if cat1_name == 'HOME':
                continue
            if cat1_name == 'LOOKBOOK':
                break
            cat1_url = cat1_node.children('a').attr('href')
            cat1 = {'name': cat1_name, 'url': cat1_url, 'children': [], 'uuid': self.cu.get_or_create(cat1_name)}

            cat2_nodes = cat1_node.children('div.level-1 > ul > li.menuItem')
            for cat2_node in cat2_nodes.items():
                cat2_name = cat2_node.children('a').text().strip()
                if cat2_name == 'NOUVEAUTÉS':
                    continue
                cat2_url = cat2_node.children('a').attr('href')

                cat2 = {
                    'name': cat2_name, 'url': cat2_url, 'children': [],
                    'uuid': self.cu.get_or_create(cat1_name, cat2_name)
                }

                cat3_nodes = cat2_node.children('div.level-2 > ul > li.menuItem')
                for cat3_node in cat3_nodes.items():
                    cat3_name = cat3_node.children('a').text().strip()
                    cat3_url = cat3_node.children('a').attr('href')

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

        params = None

        resp = self._request(
            url=url, params=params, headers=headers,
            cookies=cookies, allow_redirects=False
        )
        if not resp:
            return

        pq = PyQuery(resp.text)

        for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
            self.push_product_info(info)

        search = pq('script:contains("yTos.search")').text().strip().partition(
            'yTos.search')[-1].partition('typeof')[0].strip(' \n=;if(') or \
                 pq('script:contains("yTos.search")').text().strip().partKokontozaiCrawlerition('yTos.search')[
                     -1].strip(' \n=;')
        if not search:
            return

        search = json.loads(search)
        totalpage = int(search.get('totalPages'))
        if totalpage > 1:
            items = {
                q: search.get(q)
                for q in [
                'ytosQuery',
                'department',
                'gender',
                'season',
                'yurirulename',
                'page',
                'productsPerPage',
                'suggestion',
                'facetsvalue',
                'totalPages',
                'rsiUsed',
                'totalItems',
                'partialLoadedItems',
                'itemsToLoadOnNextPage'
            ]
            }

            headers = copy.copy(headers)
            headers['Referer'] = resp.url
            json_items = unquote(json.dumps(items))
            next_url = url + '#' + json_items

            for page in range(2, totalpage + 1):
                resp = self._request(url=next_url, headers=headers)

                pq = PyQuery(resp.text)
                for info in self._parse_product_list(pq=pq, resp=resp, headers=headers, meta=meta):
                    self.push_product_info(info)

    def _parse_product_list(self, pq, resp, headers, meta):
        """列表页解析器"""

        headers = copy.copy(headers)
        headers['Referer'] = resp.url

        if pq('#searchContainer ul.products li.item'):
            node = pq('#searchContainer ul.products li.item')
            for detail in node.items():
                url = self._full_url(url_from=resp.url, path=detail.children('.titleContainer a').attr('href'))
                if url:
                    meta['product_id'] = urlparse(url).path.partition('.')[0].split('/')[-1]
                    yield url, headers, resp.cookies.get_dict(), meta
        else:
            node = pq('.priceUpdater script')
            for each in node.items():
                each_node = each.text().strip()
                data = json.loads(each_node)
                url = data['@id']
                if url:
                    meta['product_id'] = urlparse(url).path.partition('.')[0].split('/')[-1]
                    yield url, headers, resp.cookies.get_dict(), meta

    def _parse_product_detail(self, url, resp, meta, **extra):
        """详情页解析器"""

        _ = self
        pq = PyQuery(resp.text)

        # 商品图片
        images = []
        for img_node in pq('#itemImages ul.alternativeImages > li > img').items():
            img_url = img_node.attr('src')
            if '12202815go' in img_url:
                img_url = img_url.replace('12202815go', '12202815cg')
            images.append(img_url)

        # 商品名称
        name = pq('#productImagesWrapper .productInfo .productName span.modelName').text().strip()

        # 商品价格
        was_price = pq('#productImagesWrapper .productInfo .itemBoxPrice span.full').text().strip()
        now_price = pq('#productImagesWrapper .productInfo .itemBoxPrice span.discounted').text().strip()

        if not (was_price and now_price):
            now_price = pq('#productImagesWrapper .productInfo .itemBoxPrice span.price').text().strip()

        # 商品介绍
        introduction = pq('#productImagesWrapper .productInfo ul.accordion li:eq(0) .descriptionContent').text().strip()

        # 商品颜色
        code10 = url.partition('.html')[0].partition('_cod')[-1]
        params = {'siteCode': 'ALEXANDERWANG_FR', 'code10': code10, 'langId': 5}
        link = 'https://www.alexanderwang.com/yTos/api/Plugins/ItemPluginApi/GetCombinationsAsync/'
        resp = self._request(url=link, params=params, headers=extra['headers'], cookies= extra['cookies'])
        if resp.status_code == 200:
            data = resp.json()

            colors = []
            for eacn_color in data.get('ColorsFull'):
                color = eacn_color.get('Description')
                if color:
                    colors.append(color)

            # 商品尺寸
            sizes = []
            if data['SizesByCode10']:
                for size_node in data.get('SizesByCode10')[0].get('Sizes'):
                    size = size_node['Description']
                    if size:
                        sizes.append(size)

            # 商品库存
            isSoldout = data['ItemsAvailabilityInfo'][0]['IsSoldOut']
            if isSoldout:
                stock = 0
            else:
                stock = 999
            return {'url': url, 'categories': meta['categories'], 'product_id': meta['product_id'], 'images': images,
                    'name': name, 'was_price': was_price, 'now_price': now_price, 'introduction': introduction,
                    'colors': colors, 'sizes': sizes, 'stock': stock, 'store': self.store, 'brand': self.brand,
                    'store_id': self.store_id, 'brand_id': self.brand_id, 'coin_id': self.coin_id
            }
