# -*- coding: utf-8 -*-
# !/usr/bin/env python

import inspect
import os
from urllib.parse import urlparse

from SweetSpiders import spiders
from SweetSpiders.config import TEMPLATE
from fire import Fire


class Manger:
    @staticmethod
    def create(file_name=None, class_name=None, comment=None, index_url=None, wait=None):
        """
        根据模板创建爬虫, 如果有参数缺失，进入交互模式
        :param file_name: str, 爬虫文件名
        :param class_name: str, 爬虫类名
        :param comment: str, 爬虫注释
        :param index_url: str, 首页链接
        :param wait: None|int|float|tuple|list, 休眠区间
        :return: None
        """

        if not file_name:
            file_name = input('file_name: ')
        if not class_name:
            class_name = input('class_name: ')
        if not comment:
            comment = input('comment: ')
        if not index_url:
            index_url = input('index_url: ')
        if not wait:
            wait = input('wait: ')

        # 检查休眠区间
        wait = eval(wait)
        assert wait is None or isinstance(wait, (int, float, tuple, list)), '休眠区间无效'

        # 检查首页链接
        p = urlparse(index_url)
        assert all([p.scheme, p.netloc]), '首页链接无效'

        # 检查文件路径是否存在
        path = f'{os.path.dirname(inspect.getabsfile(spiders))}/{file_name}.py'
        assert not os.path.exists(path), '文件已存在'

        # 检查爬虫是否存在
        postfix = 'Crawler'
        if not class_name.endswith(postfix):
            class_name += postfix
        class_name = class_name[0].upper() + class_name[1:]
        assert not hasattr(spiders, class_name), '爬虫已存在'

        # 爬虫文件写入源码
        source = TEMPLATE.format(class_name=class_name, comment=comment, index_url=index_url, wait=wait)
        with open(path, mode='w') as fp:
            fp.write(source.strip())
            fp.write('\n')

        # 爬虫类追加到包导入文件
        with open(inspect.getabsfile(spiders), mode='a') as fp:
            fp.write(f'from .{file_name} import *\n')

    @staticmethod
    def control(crawler=None, method=None):
        """
        如果制定爬虫方法，则直接调用，否则，进入交互模式
        :param crawler: str, 爬虫类名
        :param method: str, 爬虫方法名
        :return: None
        """

        if crawler and method:
            return getattr(getattr(spiders, crawler)(), method)()

        objects = [
            getattr(spiders, name) for name in dir(spiders)
            if name.endswith('Crawler') and not name.startswith('Index')
        ]

        print('=' * 30)
        for i, o in enumerate(objects):
            print(f'{i}. {o.__name__}')

        print('-' * 30)
        index = int(input('spider: '))
        assert 0 <= index < len(objects), '爬虫不存在'
        print('=' * 30)

        crawler = objects[index]()

        methods = [
            getattr(crawler, name) for name in dir(crawler)
            if not name.startswith('_') and inspect.ismethod(getattr(crawler, name))
        ]

        print()
        print('=' * 30)
        for i, m in enumerate(methods):
            print(f'{i}. {m.__name__}')

        print('-' * 30)
        index = int(input('method: '))
        assert 0 <= index < len(methods), '方法不存在'
        print('=' * 30)

        methods[index]()


if __name__ == '__main__':
    Fire(Manger)
