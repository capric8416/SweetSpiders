# -*- coding: utf-8 -*-
# !/usr/bin/env python
import oss2
import pymongo


class TransferImage:
    def __init__(self):
        self.mongo = pymongo.MongoClient('localhost', 27017)
        self.db = self.mongo['LasciviousCrawler']
        self.collection = self.db['products']

    def transfer_image_url(self):
        auth = oss2.Auth('pHrZGmZxcbOqvnod', 'dXzTR9DeVPZ5DeMShrNUIqKTKF7Eg5')
        bucket = oss2.Bucket(auth, 'http://res.danaaa.com', 'dana1')

