# -*- coding: utf-8 -*-


import inspect
from collections import namedtuple

from celery.schedules import crontab
from kombu import Queue

from .singleton import Singleton


def default_namedtuple(typename, field_names, default=None, repeat=None):
    """可选默认值的命名元组"""
    n = namedtuple(typename=typename, field_names=field_names)

    if isinstance(default, (tuple, list)):
        n.__new__.__defaults__ = default
    else:
        if repeat is None:
            repeat = len(getattr(n, '_fields'))
        n.__new__.__defaults__ = (default,) * repeat

    return n


def define_queue(name):
    """定义task queue"""
    return Queue(name, routing_key=f'sweet_spiders_task_{name}.#')


def get_beat_schedule(*configs):
    """配置task方法运行时间"""

    def _get_schedule(task, schedule, options, args=None, dummy=None):
        assert schedule, 'schedule(namedtuple)不允许为空'
        assert options, 'options(dict)不允许为空'

        key = f'{inspect.getmodule(task.__wrapped__).__name__}.{task.__name__}'

        value = {'task': key, 'schedule': crontab(**schedule._asdict()), 'options': options}
        if args:
            value['args'] = args

        if dummy:
            key += f'.dummy_{dummy}'

        return key, value

    return {k: v for k, v in (_get_schedule(**conf._asdict()) for conf in configs)}


class NamedTaskQueues(metaclass=Singleton):
    """命名任务工作队列"""

    def __init__(self, queues):
        for q in queues:
            setattr(self, q.name, q.name)

    def __getattribute__(self, item):
        return {'queue': super().__getattribute__(item)}


# 任务调度配置
Schedule = default_namedtuple(
    typename='Schedule', repeat=2,
    field_names=['task', 'schedule', 'options', 'args', 'dummy'])

# 任务调度时间配置
CronTable = default_namedtuple(
    typename='CronTable', default='*',
    field_names=['minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year'])
