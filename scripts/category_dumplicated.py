# -*- coding: utf-8 -*-
# !/usr/bin/env python
import pymongo


class CategoryDumplicated:
    """分类去重"""

    def __init__(self, db, collection='products'):
        self.mongo = pymongo.MongoClient('localhost', 27017)
        self.db = self.mongo[db]
        self.collection = self.db[collection]

    def run(self):
        category_list = []
        for item in self.collection.find():
            each_category = item['categories']
            if each_category not in category_list:
                category_list.append(each_category)

                each_items = {'categories': category_item for category_item in category_list}
                print(each_items)


if __name__ == '__main__':
    c = CategoryDumplicated(db='HarrodsCrawler')
    c.run()
