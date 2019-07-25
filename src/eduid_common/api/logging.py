# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import time
from os import environ
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from flask import current_app
from eduid_common.session import session
from eduid_common.api.exceptions import BadConfiguration

__author__ = 'lundberg'

"""
Adds the following entries to logging context:
system_hostname - Set with environment variable SYSTEM_HOSTNAME
app_name - Flask app name
eppn - Available if a session initiated
"""


# Default to RFC3339/ISO 8601 with tz
class EduidFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime('%Y-%m-%dT%H:%M:%S', ct)
            tz = time.strftime('%z', ct)  # Can evaluate to empty string
            if tz:
                tz = '{0}:{1}'.format(tz[:3], tz[3:])  # Need colon to follow the rfc/iso
            s = '{}.{:03.0f}{}'.format(t, record.msecs, tz)
        return s


class AppFilter(logging.Filter):

    def __init__(self, app):
        logging.Filter.__init__(self)
        self.app = app

    def filter(self, record):
        record.system_hostname = environ.get('SYSTEM_HOSTNAME', '')  # Underlying hosts name for containers
        record.hostname = environ.get('HOSTNAME', '')  # Actual hostname or container id
        with self.app.app_context():
            record.app_name = current_app.name
        return True


class UserFilter(logging.Filter):

    def __init__(self, app):
        logging.Filter.__init__(self)
        self.app = app

    def filter(self, record):
        record.eppn = ''
        if session:
            record.eppn = session.get('user_eppn', '')
        return True


# Root log config
root_handler = logging.StreamHandler()
root_formatter = EduidFormatter('%(asctime)s | %(levelname)s | %(module)s | %(message)s')
root_handler.setFormatter(root_formatter)
root = logging.getLogger()
root.addHandler(root_handler)


def rotating(app):
    """
    :param app: Flask app

    :type app: flask.app.Flask

    :return: Flask app with rotating log handler
    :rtype: flask.app.Flask

    Override the following config settings if needed:
    LOG_TYPE = ['rotating']
    LOG_FILE = None
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    LOG_MAX_BYTES = 1000000
    LOG_BACKUP_COUNT = 10
    """

    if app.config.log_file:
        try:
            handler = RotatingFileHandler(app.config.log_file, maxBytes=app.config.log_max_bytes,
                                          backupCount=app.config.log_backup_count)
            handler.setLevel(app.config.log_level)
            formatter = EduidFormatter(app.config.log_format)
            handler.setFormatter(formatter)
            app.logger.addHandler(handler)
            app.logger.info('Rotating log handler initiated')
        except AttributeError as e:
            raise BadConfiguration(e)
    return app


def stream(app):
    """
    :param app: Flask app

    :type app: flask.app.Flask

    :return: Flask app with rotating log handler
    :rtype: flask.app.Flask
    """
    try:
        handler = StreamHandler()
        handler.setLevel(app.config.log_level)
        formatter = EduidFormatter(app.config.log_format)
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.info('Stream log handler initiated')
    except AttributeError as e:
        raise BadConfiguration(e)
    return app


def init_logging(app):
    """
    :param app: Flask app
    :type app: flask.app.Flask
    :return: Flask app with log handlers
    :rtype: flask.app.Flask
    """
    root.setLevel(app.config.log_level)
    app.logger.handlers = []  # Remove any handler that Flask set up
    app.logger.setLevel(app.config.log_level)
    # Add extra context
    app.logger.addFilter(AppFilter(app))
    app.logger.addFilter(UserFilter(app))

    for log_type in app.config.log_type:
        init_handler = globals().get(log_type)
        if init_handler:
            app = init_handler(app)
    return app
