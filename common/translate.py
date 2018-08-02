# -*- coding: utf-8 -*-
# !/usr/bin/env python
import time

import execjs
import requests
from pyquery import PyQuery


class GoogleTranslate:
    def __init__(self, alive=1000):
        self.index = 'https://translate.google.cn/'

        self.url = 'http://translate.google.cn/translate_a/single'

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        }

        self.max_len = 5000

        self.context = None
        self.cookies = None

        self.alive = alive
        self.elapsed = alive

        self.get_context()

    def query(self, source, sl='en', tl='zh-CN', hl='zh-CN'):
        self.check_alive()

        _len = len(source)
        assert _len <= self.max_len, f'翻译的长度({_len})超过限制({self.max_len})！！！'

        params = [
            ('q', source),
            ('tk', self.get_tk(source=source)),
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

        while True:
            try:
                resp = requests.get(self.url, params=params, headers=self.headers, cookies=self.cookies, timeout=5)
                assert resp.status_code == 200, resp.text

                target = ''.join([a for a, b, *_ in resp.json()[0] if b])

                print('[source]  ', source)
                print('[target]  ', target)
            except Exception as e:
                print(e)
                time.sleep(0.5)
            else:
                break

        return target

    def batch_query(self, categories_list):
        for category in categories_list:
            yield self.query(source=category)

    def get_tk(self, source):
        return self.context.call('jr', source).lstrip('&tk=')

    def check_alive(self):
        self.elapsed -= 1
        if not self.elapsed:
            print('** RESET **')
            self.get_context()
            self.elapsed = self.alive

    def get_context(self):
        self.context = execjs.compile(
            f'ir = {self.get_ir()};'
            +
            '''
            gr = function (a) {
                return function () {
                    return a
                }
            };

            jr = function (a) {
                var b = ir;
                var d = gr(String.fromCharCode(116));
                c = gr(String.fromCharCode(107));
                d = [d(), d()];
                d[1] = c();
                c = "&" + d.join("") + "=";
                d = b.toString().split(".");
                b = Number(d[0]) || 0;
                for (var e = [], f = 0, g = 0; g < a.length; g++) {
                    var l = a.charCodeAt(g);
                    128 > l ? e[f++] = l : (2048 > l ? e[f++] = l >> 6 | 192 : 
                    (55296 == (l & 64512) && g + 1 < a.length && 56320 == (a.charCodeAt(g + 1) & 64512) ? 
                    (l = 65536 + ((l & 1023) << 10) + (a.charCodeAt(++g) & 1023),
                        e[f++] = l >> 18 | 240,
                        e[f++] = l >> 12 & 63 | 128) : e[f++] = l >> 12 | 224,
                        e[f++] = l >> 6 & 63 | 128),
                        e[f++] = l & 63 | 128)
                }
                a = b;
                for (f = 0; f < e.length; f++)
                    a += e[f],
                        a = hr(a, "+-a^+6");
                a = hr(a, "+-3^+b+-f");
                a ^= Number(d[1]) || 0;
                0 > a && (a = (a & 2147483647) + 2147483648);
                a %= 1E6;
                return c + (a.toString() + "." + (a ^ b))
            };


            hr = function (a, b) {
                for (var c = 0; c < b.length - 2; c += 3) {
                    var d = b.charAt(c + 2);
                    d = "a" <= d ? d.charCodeAt(0) - 87 : Number(d);
                    d = "+" == b.charAt(c + 1) ? a >>> d : a << d;
                    a = "+" == b.charAt(c) ? a + d & 4294967295 : a ^ d
                }
                return a
            };
        '''
        )

    def get_ir(self):
        resp = requests.get(self.index)

        self.cookies = resp.cookies.get_dict()

        pq = PyQuery(resp.text)
        script = pq('script:contains(TKK)').text()
        ir = execjs.eval(f'''function () {{ {script}; return TKK; }}()''')

        return ir


if __name__ == '__main__':
    g = GoogleTranslate(alive=20)
    while True:
        g.query(source='Prêt-à-porter', sl='fr')
