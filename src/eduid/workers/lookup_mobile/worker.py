import eduid.workers.lookup_mobile.common as common
from eduid.common.config.workers import MobConfig
from eduid.common.rpc.celery import init_celery
from eduid.common.rpc.worker import get_worker_config

worker_config: MobConfig = MobConfig(app_name='app_name_NOT_SET')

if common.celery is None:
    worker_config = get_worker_config('lookup_mobile', config_class=MobConfig)
    celery = init_celery(
        'eduid_lookup_mobile', config=worker_config.celery, include=['eduid.workers.lookup_mobile.tasks']
    )

    # When Celery starts the worker, it expects there to be a 'celery' in the module it loads,
    # but our tasks expect to find the Celery instance in common.celery - so copy it there
    common.celery = celery
