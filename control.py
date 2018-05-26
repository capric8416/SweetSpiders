# -*- coding: utf-8 -*-
# !/usr/bin/env python

import inspect

from SweetSpiders import spiders
from fire import Fire


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
    Fire(control)
