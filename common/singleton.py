# -*- coding: utf-8 -*-
# !/usr/bin/env python


class Singleton(type):
    """单例元类"""

    def __init__(cls, *args, **kwargs):
        cls._instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
