# -*- coding: utf-8 -*-


from celery import Celery

app = Celery('app', include=['SweetSpiders.tasks'])
app.config_from_object('SweetSpiders.config.celery')
