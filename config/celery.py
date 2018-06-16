# -*- coding: utf-8 -*-


from multiprocessing import cpu_count

from SweetSpiders.common import CronTable, Schedule, define_queue, get_beat_schedule
from SweetSpiders.config.redis import BROKER_URL, RESULT_BACKEND
from SweetSpiders.tasks.spiders import get_spider_tasks

# broker
broker_url = BROKER_URL
# 结果储存
result_backend = RESULT_BACKEND

# 序列化
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

# 超时
result_expires = 60 * 60 * 24
broker_transport_options = {'visibility_timeout': 60 * 60 * 12}

# Maximum number of tasks a pool worker process can execute before it’s replaced with a new one
worker_max_tasks_per_child = 10

# If enabled the worker pool can be restarted using the pool_restart remote control command
worker_pool_restarts = True

# 时区
timezone = 'Asia/Shanghai'
enable_utc = False

# 任务所在的包
imports = ['SweetSpiders.tasks']

# 任务工作队列
task_queues = [
    define_queue(f'queue_{i:02d}')
    for i in range(cpu_count())
]

# 任务工作调度
beat_schedule = get_beat_schedule(*[
    Schedule(task=task, schedule=CronTable(minute='*/10'), options={'queue': task_queues[q].name})
    for q, task in get_spider_tasks(queues=len(task_queues))
])
