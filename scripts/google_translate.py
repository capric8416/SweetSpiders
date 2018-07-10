# -*- coding: utf-8 -*-
# !/usr/bin/env python

import requests


class GoogleTranslate:
    def __init__(self):
        self.url = 'http://translate.google.cn/translate_a/single'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        }
        self.max_len = 5000

    def query(self, source, sl='jap', tl='zh-CN', hl='zh-CN'):
        _len = len(source)
        assert _len <= self.max_len, f'翻译的长度({_len})超过限制({self.max_len})！！！'

        params = [
            ('q', source),
            ('tk', self.tk(source=source)),
            ('client', 't'),
            ('sl', sl),
            ('tl', tl),
            ('hl', hl),
            ('ie', 'UTF-8'),
            ('oe', 'UTF-8'),
            ('srcrom', 0),
            ('ssel', 0),
            ('tsel', 0),
            ('clearbtn', 1),
            ('otf', 1),
            ('pc', 1),
            ('kc', 2),
            ('dt', 't'),
            ('dt', 'at'),
            ('dt', 'bd'),
            ('dt', 'ex'),
            ('dt', 'ld'),
            ('dt', 'md'),
            ('dt', 'qca'),
            ('dt', 'rw'),
            ('dt', 'rm'),
            ('dt', 'ss'),
        ]

        resp = requests.get('http://translate.google.cn/translate_a/single', params=params, timeout=5)
        target = ''.join([a for a, b, *_ in resp.json()[0] if b])

        print('[source]  ', source)
        print('[target]  ', target)

        return target

    def tk(self, source):
        return self._tk1(a=source)

    def _tk1(self, a):
        i = 0
        c = []
        while i < len(a):
            m = ord(a[i])

            if 128 > m:
                c.append(m)
            else:
                if 2048 > m:
                    c.append(m >> 6 | 192)
                else:
                    if 55296 == (m & 64512) and i + 1 < a.length and 56320 == (ord(a[i + 1]) & 64512):
                        i += 1
                        m = 65536 + ((m & 1023) << 10) + (ord(a[i]) & 1023)

                        c.extend([m >> 18 | 240, m >> 12 & 63 | 128])
                    else:
                        c.extend([m >> 12 | 224, m >> 6 & 63 | 128])

                    c.append(m & 63 | 128)

            i += 1

        b = 406644
        a = b

        for f in range(len(c)):
            a += c[f]
            a = self._tk2(a, '+-a^+6')

        a = self._tk2(a, '+-3^+b+-f')

        a ^= 3293161072 or 0

        if 0 > a:
            a = (a & 2147483647) + 2147483648

        a %= int(1e6)

        return f'{a}.{a ^ b}'

    @staticmethod
    def _tk2(c, d):
        alpha = 'a'
        plus = '+'

        i = 0
        while i < len(d) - 2:
            e = d[i + 2]
            e = ord(e[0]) - 87 if e >= alpha else int(e)
            e = c >> e if d[i + 1] == plus else c << e

            c = c + e & 4294967295 if d[i] == plus else c ^ e

            i += 3

        return c

    def batch_query(self, categories_list):
        for category in categories_list:
            yield self.query(source=category)


if __name__ == '__main__':
    g = GoogleTranslate()
