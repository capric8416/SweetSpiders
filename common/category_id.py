# -*- coding: utf-8 -*-
# !/usr/bin/env python

import json
import random
import time
import uuid

import redis
import redis_lock
from SweetSpiders.config import REDIS_URL

from .singleton import Singleton


class CategoryUUID(metaclass=Singleton):
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL)
        self.lock = f'lock:{self.__class__.__name__.lower()}:'
        self.name = 'category:uuid'
        self.dump = 'category:uuid:aa'
        self.expire = 20

    def get_or_create(self, *categories):
        key = json.dumps(categories)
        with redis_lock.Lock(redis_client=self.redis, name=self.lock + key, expire=self.expire):
            uuid1 = self.redis.hget(name=self.name, key=key)
            if uuid1 and len(uuid1) == 36:
                uuid1 = uuid1.decode()
            else:
                while True:
                    uuid1 = str(uuid.uuid1())
                    if self.redis.sadd(self.dump, uuid1):
                        self.redis.hset(self.name, key, uuid1)
                        break
                    time.sleep(random.randrange(1, 10) / 100)
            return uuid1
