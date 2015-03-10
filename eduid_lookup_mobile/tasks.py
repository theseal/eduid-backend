from __future__ import absolute_import
from eduid_lookup_mobile.celery import app
from eduid_lookup_mobile.client.mobile_lookup_client import MobileLookupClient

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@app.task
def find_mobiles_by_NIN(national_identity_number, number_region=None):
    """
    Searches mobile numbers registered to the given nin
    :param national_identity_number:
    :return: a list of formatted mobile numbers. Empty list if no numbers was registered to the nin
    """
    lookup_client = MobileLookupClient(logger)
    return lookup_client.find_mobiles_by_NIN(national_identity_number, number_region)

@app.task
def find_NIN_by_mobile(mobile_number):
    """
    Searches nin with the registered mobile number
    :param mobile_number:
    :return: the nin with the registered mobile number
    """
    lookup_client = MobileLookupClient(logger)
    return lookup_client.find_NIN_by_mobile(mobile_number)
