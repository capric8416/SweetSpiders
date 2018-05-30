# -*- coding: utf-8 -*-
# !/usr/bin/env python

from SweetSpiders.common import CategoryUUID

if __name__ == '__main__':
    import string
    import random

    c = CategoryUUID()
    for _ in range(100):
        for s in random.choice(string.ascii_letters):
            print(s, c.get_or_create(s))
