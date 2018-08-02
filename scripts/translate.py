# -*- coding: utf-8 -*-
# !/usr/bin/env python
import execjs
import requests
from pyquery import PyQuery


class Py4Js:

    def __init__(self):
        ir, cookies = self.get_ir()
        self.context = self.get_jr(ir=ir)

    @staticmethod
    def get_ir():
        resp = requests.get('https://translate.google.cn/')

        cookies = resp.cookies.get_dict()

        pq = PyQuery(resp.text)
        script = pq('script:contains(TKK)').text()
        ir = execjs.eval(f'''function () {{ {script}; return TKK; }}()''')

        return ir, cookies

    @staticmethod
    def get_jr(ir):
        return execjs.compile(
            f'ir = {ir};'
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

    def get_tk(self, text):
        return self.context.call('jr', text)


def translate(tk, content):
    if len(content) > 4891:
        print("翻译的长度超过限制！！！")
        return

    param = {'tk': tk.lstrip('&tk='), 'q': content}

    result = requests.get("""http://translate.google.cn/translate_a/single?client=t&sl=en
        &tl=zh-CN&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss
        &dt=t&ie=UTF-8&oe=UTF-8&clearbtn=1&otf=1&pc=1&srcrom=0&ssel=0&tsel=0&kc=2""", params=param)

    # 返回的结果为Json，解析为一个嵌套列表
    for text in result.json():
        print(text)


def main():
    js = Py4Js()

    content = 'Prêt-à-porter'

    tk = js.get_tk(content)
    translate(tk, content)


if __name__ == "__main__":
    main()
