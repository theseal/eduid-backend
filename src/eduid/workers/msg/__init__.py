"""
The eduID messaging package.

Copyright (c) 2013, 2014, 2015, 2018 SUNET. All rights reserved.
See the file LICENSE.txt for full license statement.
"""
from typing import TYPE_CHECKING, Optional

from celery import Celery

import eduid.workers.msg.common as common
from eduid.common.config.base import CeleryConfig
from eduid.common.rpc.celery import init_celery as _init_celery

if TYPE_CHECKING:
    from eduid.workers.msg.tasks import MessageSender


def init_app(config: Optional[CeleryConfig]) -> Celery:
    common.celery = _init_celery('eduid_msg', config)
    return common.celery
