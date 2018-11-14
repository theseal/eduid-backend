from eduid_userdb.db import MongoDB
from pymongo.errors import ConnectionFailure
from inspect import isclass
from datetime import datetime


class TransactionAudit(object):
    enabled = False
    collection = None

    def __init__(self, db_uri, db_name='eduid_msg', collection_name='transaction_audit'):
        self.conn = None
        self.db_uri = db_uri
        self.db_name = db_name
        self.collection_name = collection_name

    def __call__(self, f):
        if not self.enabled:
            return f

        def audit(*args, **kwargs):
            ret = f(*args, **kwargs)
            if not isclass(ret):  # we can't save class objects in mongodb
                date = datetime.utcnow()
                doc = {'function': f.__name__,
                       'data': self._filter(f.__name__, ret, *args, **kwargs),
                       'created_at': date}
                self.collection.insert(doc)
            return ret
        if self.collection is None or not self.is_healthy():
            self.conn = MongoDB(self.db_uri)
            db = self.conn.get_database(self.db_name)
            self.collection = db[self.collection_name]
        return audit

    @classmethod
    def enable(cls):
        cls.enabled = True

    @classmethod
    def disable(cls):
        cls.enabled = False

    def _filter(self, func, data, *args, **kwargs):
        if data is False:
            return data
        if func == '_get_navet_data':
            return {'identity_number': args[1]}
        elif func == 'send_message':
            return {'type': args[1], 'recipient': args[4], 'transaction_id': data, 'audit_reference': args[2],
                    'template': args[5]}
        elif func == 'sendmail':
            return {'type': 'mail', 'recipient': args[1], 'send_errors': data, 'audit_reference': args[3]}
        elif func == 'sendsms':
            return {'type': 'sms', 'recipient': args[1], 'transaction_id': data, 'audit_reference': args[3]}
        return data

    def is_healthy(self):
        try:
            return self.conn.get_connection().admin.command('ismaster')
        except ConnectionFailure:
            return False
