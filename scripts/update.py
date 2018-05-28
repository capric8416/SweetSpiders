# -*- coding: utf-8 -*-
# !/usr/bin/env python
import requests


def do_update():
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
    url = 'http://sw.danaaa.com/test_spider_category.html'
    jsonCategory = [

        {
            "uuid": "uuid-1",
            "name": "WOMEN'S",
            "url": "http://www.baidu.com",
            "children": [
                {
                    "uuid": "uuid-2",
                    "name": "TOPS AND T-SHIRTS",
                    "url": "http: //www.ccc.com",
                    "children": [
                        {
                            "uuid": "uuid-3",
                            "name": "DRESSES",
                            "url": "http://www.bbb.com"
                        },
                        {
                            "uuid": "uuid-4",
                            "name": "DRESSES",
                            "url": "http://www.bbb.com"
                        }
                    ]
                }
            ]
        },

        {
            "uuid": "uuid-5",
            "name": "WOMEN'S",
            "url": "http://www.baidu.com",
            "children": [
                {
                    "uuid": "uuid-6",
                    "name": "TOPS AND T-SHIRTS",
                    "url": "http: //www.ccc.com",
                    "children": [
                        {
                            "uuid": "uuid-7",
                            "name": "DRESSES",
                            "url": "http://www.bbb.com"
                        },
                        {
                            "uuid": "uuid-8",
                            "name": "DRESSES",
                            "url": "http://www.bbb.com"
                        }
                    ]
                }
            ]
        }
    ]

    data = {'provider': 'Kokon to Zai', 'storeId': 1120, 'jsonCategory': jsonCategory}
    resp = requests.post(url=url, headers=headers, data=data)
    print(resp.text)


do_update()
