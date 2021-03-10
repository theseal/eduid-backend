import logging
from pathlib import PurePath

from eduid.common.api.mail_relay import MailRelay
from eduid.common.api.msg import MsgRelay
from eduid.common.config.base import EduIDBaseAppConfig, MailConfigMixin, MsgConfigMixin
from eduid.common.config.workers import MsgConfig
from eduid.userdb.testing import MongoTestCase
from eduid.workers.msg.common import MsgWorkerSingleton

logger = logging.getLogger(__name__)


class MsgTestConfig(MsgConfig, MsgConfigMixin):
    pass


class MailTestConfig(EduIDBaseAppConfig, MailConfigMixin):
    pass


class MsgMongoTestCase(MongoTestCase):
    def setUp(self, init_msg=True):
        super().setUp()
        data_path = PurePath(__file__).with_name('tests') / 'data'
        if init_msg:
            settings = {
                'app_name': 'testing',
                'celery': {
                    'broker_transport': 'memory',
                    'broker_url': 'memory://',
                    'task_eager_propagates': True,
                    'task_always_eager': True,
                    'result_backend': 'cache',
                    'cache_backend': 'memory',
                },
                'mongo_uri': self.tmp_db.uri,
                'mongo_dbname': 'test',
                'sms_acc': 'foo',
                'sms_key': 'bar',
                'sms_sender': 'Test sender',
                'template_dir': str(data_path),
                'message_rate_limit': 2,
            }
            self.msg_settings = MsgTestConfig(**settings)

            MsgWorkerSingleton.update_config(self.msg_settings)
            logger.debug(f'Initialised message_relay with config:\n{self.msg_settings}')

            self.msg_relay = MsgRelay(self.msg_settings)
            self.mail_relay = MailRelay(MailTestConfig(**settings, token_service_url='foo'))
