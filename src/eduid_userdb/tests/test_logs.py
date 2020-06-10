# -*- coding: utf-8 -*-

from copy import deepcopy
from unittest import TestCase

from eduid_userdb.logs.db import ProofingLog
from eduid_userdb.logs.element import (
    LetterProofing,
    MailAddressProofing,
    PhoneNumberProofing,
    ProofingLogElement,
    SeLegProofing,
    SeLegProofingFrejaEid,
    TeleAdressProofing,
    TeleAdressProofingRelation,
)
from eduid_userdb.testing import MOCKED_USER_STANDARD, MongoTemporaryInstance
from eduid_userdb.user import User

__author__ = 'lundberg'


class TestProofingLog(TestCase):
    def setUp(self):
        self.tmp_db = MongoTemporaryInstance.get_instance()
        self.proofing_log_db = ProofingLog(db_uri=self.tmp_db.uri)
        self.user = User.from_dict(MOCKED_USER_STANDARD)

    def tearDown(self):
        self.proofing_log_db._drop_whole_collection()

    def test_id_proofing_data(self):

        proofing_element = ProofingLogElement(
            self.user, created_by='test', proofing_method='test', proofing_version='test'
        )
        self.proofing_log_db.save(proofing_element)

        result = list(self.proofing_log_db._coll.find({}))
        self.assertEqual(len(result), 1)
        hit = result[0]
        self.assertEqual(hit['eduPersonPrincipalName'], self.user.eppn)
        self.assertEqual(hit['created_by'], 'test')
        self.assertIsNotNone(hit['created_ts'])
        self.assertEqual(hit['proofing_method'], 'test')

    def test_teleadress_proofing(self):
        data = {
            'created_by': 'test',
            'reason': 'matched',
            'nin': 'some_nin',
            'mobile_number': 'some_mobile_number',
            'user_postal_address': {'response_data': {'some': 'data'}},
            'proofing_version': 'test',
        }
        proofing_element = TeleAdressProofing(self.user, **data)
        for key, value in data.items():
            self.assertIn(key, proofing_element.to_dict())
            self.assertEqual(value, proofing_element.to_dict().get(key))

        self.proofing_log_db.save(proofing_element)
        result = list(self.proofing_log_db._coll.find({}))
        self.assertEqual(len(result), 1)
        hit = result[0]
        self.assertEqual(hit['eduPersonPrincipalName'], self.user.eppn)
        self.assertEqual(hit['created_by'], 'test')
        self.assertIsNotNone(hit['created_ts'])
        self.assertEqual(hit['reason'], 'matched')
        self.assertEqual(hit['proofing_method'], 'TeleAdress')
        self.assertEqual(hit['proofing_version'], 'test')

    def test_teleadress_proofing_relation(self):
        data = {
            'created_by': 'test',
            'reason': 'matched_by_navet',
            'nin': 'some_nin',
            'mobile_number': 'some_mobile_number',
            'user_postal_address': {'response_data': {'some': 'data'}},
            'mobile_number_registered_to': 'registered_national_identity_number',
            'registered_relation': 'registered_relation_to_user',
            'registered_postal_address': {'response_data': {'some': 'data'}},
            'proofing_version': 'test',
        }
        proofing_element = TeleAdressProofingRelation(self.user, **data)
        for key, value in data.items():
            self.assertIn(key, proofing_element.to_dict())
            self.assertEqual(value, proofing_element.to_dict().get(key))

        self.proofing_log_db.save(proofing_element)
        result = list(self.proofing_log_db._coll.find({}))
        self.assertEqual(len(result), 1)
        hit = result[0]
        self.assertEqual(hit['eduPersonPrincipalName'], self.user.eppn)
        self.assertEqual(hit['created_by'], 'test')
        self.assertIsNotNone(hit['created_ts'])
        self.assertEqual(hit['reason'], 'matched_by_navet')
        self.assertEqual(hit['proofing_method'], 'TeleAdress')
        self.assertEqual(hit['proofing_version'], 'test')

    def test_teleadress_proofing_extend_bug(self):
        data_match = {
            'created_by': 'test',
            'reason': 'matched',
            'nin': 'some_nin',
            'mobile_number': 'some_mobile_number',
            'user_postal_address': {'response_data': {'some': 'data'}},
            'proofing_version': 'test',
        }

        data_relation = {
            'created_by': 'test',
            'reason': 'matched_by_navet',
            'nin': 'some_nin',
            'mobile_number': 'some_mobile_number',
            'user_postal_address': {'response_data': {'some': 'data'}},
            'mobile_number_registered_to': 'registered_national_identity_number',
            'registered_relation': 'registered_relation_to_user',
            'registered_postal_address': {'response_data': {'some': 'data'}},
            'proofing_version': 'test',
        }

        # Make a copy of the original required keys
        required_keys1 = deepcopy(TeleAdressProofing(self.user, **data_match)._required_keys)
        # Extend the required keys
        TeleAdressProofingRelation(self.user, **data_relation)
        # Make sure the required keys are instantiated as the original keys
        required_keys2 = TeleAdressProofing(self.user, **data_match)._required_keys
        self.assertEqual(required_keys1, required_keys2)

    def test_letter_proofing(self):
        data = {
            'created_by': 'test',
            'nin': 'some_nin',
            'letter_sent_to': {'name': {'some': 'data'}, 'address': {'some': 'data'}},
            'transaction_id': 'some transaction id',
            'user_postal_address': {'response_data': {'some': 'data'}},
            'proofing_version': 'test',
        }
        proofing_element = LetterProofing(self.user, **data)
        for key, value in data.items():
            self.assertIn(key, proofing_element.to_dict())
            self.assertEqual(value, proofing_element.to_dict().get(key))

        self.proofing_log_db.save(proofing_element)
        result = list(self.proofing_log_db._coll.find({}))
        self.assertEqual(len(result), 1)
        hit = result[0]
        self.assertEqual(hit['eduPersonPrincipalName'], self.user.eppn)
        self.assertEqual(hit['created_by'], 'test')
        self.assertIsNotNone(hit['created_ts'])
        self.assertIsNotNone(hit['letter_sent_to'])
        self.assertIsNotNone(hit['transaction_id'])
        self.assertEqual(hit['proofing_method'], 'letter')
        self.assertEqual(hit['proofing_version'], 'test')

    def test_mail_address_proofing(self):
        data = {
            'created_by': 'test',
            'mail_address': 'some_mail_address',
            'proofing_version': 'test',
            'reference': 'reference id',
        }
        proofing_element = MailAddressProofing(self.user, **data)
        for key, value in data.items():
            self.assertIn(key, proofing_element.to_dict())
            self.assertEqual(value, proofing_element.to_dict().get(key))

        self.proofing_log_db.save(proofing_element)
        result = list(self.proofing_log_db._coll.find({}))
        self.assertEqual(len(result), 1)
        hit = result[0]
        self.assertEqual(hit['eduPersonPrincipalName'], self.user.eppn)
        self.assertEqual(hit['created_by'], 'test')
        self.assertIsNotNone(hit['created_ts'])
        self.assertEqual(hit['proofing_method'], 'e-mail')
        self.assertEqual(hit['mail_address'], 'some_mail_address')

    def test_phone_number_proofing(self):
        data = {
            'created_by': 'test',
            'phone_number': 'some_phone_number',
            'proofing_version': 'test',
            'reference': 'reference id',
        }
        proofing_element = PhoneNumberProofing(self.user, **data)
        for key, value in data.items():
            self.assertIn(key, proofing_element.to_dict())
            self.assertEqual(value, proofing_element.to_dict().get(key))

        self.proofing_log_db.save(proofing_element)
        result = list(self.proofing_log_db._coll.find({}))
        self.assertEqual(len(result), 1)
        hit = result[0]
        self.assertEqual(hit['eduPersonPrincipalName'], self.user.eppn)
        self.assertEqual(hit['created_by'], 'test')
        self.assertIsNotNone(hit['created_ts'])
        self.assertEqual(hit['proofing_method'], 'sms')
        self.assertEqual(hit['phone_number'], 'some_phone_number')
        self.assertEqual(hit['proofing_version'], 'test')

    def test_se_leg_proofing(self):
        data = {
            'created_by': 'test',
            'proofing_version': 'test',
            'nin': 'national_identity_number',
            'vetting_by': 'provider',
            'transaction_id': 'transaction_id',
            'user_postal_address': {'response_data': {'some': 'data'}},
        }
        proofing_element = SeLegProofing(self.user, **data)
        for key, value in data.items():
            self.assertIn(key, proofing_element.to_dict())
            self.assertEqual(value, proofing_element.to_dict().get(key))

        self.proofing_log_db.save(proofing_element)
        result = list(self.proofing_log_db._coll.find({}))
        self.assertEqual(len(result), 1)
        hit = result[0]
        self.assertEqual(hit['eduPersonPrincipalName'], self.user.eppn)
        self.assertEqual(hit['created_by'], 'test')
        self.assertIsNotNone(hit['created_ts'])
        self.assertIsNotNone(hit['nin'])
        self.assertIsNotNone(hit['user_postal_address'])
        self.assertEqual(hit['vetting_by'], 'provider')
        self.assertEqual(hit['transaction_id'], 'transaction_id')
        self.assertEqual(hit['proofing_method'], 'se-leg')
        self.assertEqual(hit['proofing_version'], 'test')

    def test_se_leg_proofing_freja(self):
        data = {
            'created_by': 'test',
            'proofing_version': 'test',
            'nin': 'national_identity_number',
            'transaction_id': 'transaction_id',
            'opaque_data': 'some data',
            'user_postal_address': {'response_data': {'some': 'data'}},
        }
        proofing_element = SeLegProofingFrejaEid(self.user, **data)
        for key, value in data.items():
            self.assertIn(key, proofing_element.to_dict())
            self.assertEqual(value, proofing_element.to_dict().get(key))

        self.proofing_log_db.save(proofing_element)
        result = list(self.proofing_log_db._coll.find({}))
        self.assertEqual(len(result), 1)
        hit = result[0]
        self.assertEqual(hit['eduPersonPrincipalName'], self.user.eppn)
        self.assertEqual(hit['created_by'], 'test')
        self.assertIsNotNone(hit['created_ts'])
        self.assertIsNotNone(hit['nin'])
        self.assertIsNotNone(hit['user_postal_address'])
        self.assertEqual(hit['vetting_by'], 'Freja eID')
        self.assertEqual(hit['transaction_id'], 'transaction_id')
        self.assertEqual(hit['opaque_data'], 'some data')
        self.assertEqual(hit['proofing_method'], 'se-leg')
        self.assertEqual(hit['proofing_version'], 'test')

    def test_blank_string_proofing_data(self):
        data = {
            'created_by': 'test',
            'phone_number': 'some_phone_number',
            'proofing_version': 'test',
            'reference': 'reference id',
        }
        proofing_element = PhoneNumberProofing(self.user, **data)
        proofing_element._data['phone_number'] = ''

        self.assertFalse(self.proofing_log_db.save(proofing_element))

    def test_missing_proofing_data(self):
        data = {
            'created_by': 'test',
            'phone_number': 'some_phone_number',
            'proofing_version': 'test',
            'reference': 'reference id',
        }
        proofing_element = PhoneNumberProofing(self.user, **data)
        del proofing_element._data['created_by']

        self.assertFalse(self.proofing_log_db.save(proofing_element))

    def test_boolean_false_proofing_data(self):
        data = {
            'created_by': 'test',
            'phone_number': 'some_phone_number',
            'proofing_version': 'test',
            'reference': 'reference id',
        }
        proofing_element = PhoneNumberProofing(self.user, **data)
        proofing_element._data['phone_number'] = 0

        self.assertTrue(self.proofing_log_db.save(proofing_element))

        proofing_element = PhoneNumberProofing(self.user, **data)
        proofing_element._data['phone_number'] = False

        self.assertTrue(self.proofing_log_db.save(proofing_element))
