# -*- coding: utf-8 -*-
# !/usr/bin/env python

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'

BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/8'
RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/9'
