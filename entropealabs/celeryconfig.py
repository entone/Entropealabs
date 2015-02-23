from kombu import Exchange, Queue
import datetime

BROKER_URL = "amqp://guest:guest@mq"

CELERY_ACCEPT_CONTENT = ['json']

CELERY_TASK_SERIALIZER = "json"

CELERY_IGNORE_RESULT = True
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True

CELERY_IMPORTS = (
    'entropealabs.workers',
)
default_q = Queue('default', Exchange('default'), routing_key='default')

CELERY_QUEUES = (
    default_q,
)

CELERY_ROUTES = ()

CELERY_DEFAULT_QUEUE = 'default'
CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'
CELERY_DEFAULT_ROUTING_KEY = 'default'

CELERYBEAT_SCHEDULE = {
    'update_insights': {
        'task': 'entropealabs.workers.get_insights',
        'schedule': datetime.timedelta(minutes=10),
    },
    'update_feeds': {
        'task': 'entropealabs.workers.get_feeds',
        'schedule': datetime.timedelta(minutes=10),
    },
    'update_fitness': {
        'task': 'entropealabs.workers.get_fitness',
        'schedule': datetime.timedelta(minutes=1),
    },
}
