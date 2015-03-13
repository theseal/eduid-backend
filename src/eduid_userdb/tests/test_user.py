from bson import ObjectId
import datetime

from unittest import TestCase

from eduid_userdb.user import User

__author__ = 'ft'


class TestUser(TestCase):

    def setUp(self):
        self.data = {u'_id': ObjectId('547357c3d00690878ae9b620'),
                     u'eduPersonPrincipalName': u'guvat-nalif',
                     u'mail': u'user@example.net',
                     u'mailAliases': [{u'added_timestamp': datetime.datetime(2014, 12, 18, 11, 25, 19, 804000),
                                       u'email': u'user@example.net',
                                       u'verified': True}],
                     u'passwords': [{u'created_ts': datetime.datetime(2014, 11, 24, 16, 22, 49, 188000),
                                     u'id': ObjectId('54735b588a7d2a2c4ec3e7d0'),
                                     u'salt': u'$NDNv1H1$315d7$32$32$',
                                     u'source': u'dashboard'}],
                     u'subject': u'physical person'}
        self.user = User(self.data)

    def test_user_id(self):
        self.assertEqual(self.user.user_id, self.data['_id'])

    def test_eppn(self):
        self.assertEqual(self.user.eppn, self.data['eduPersonPrincipalName'])

    def test_given_name(self):
        self.fail()

    def test_display_name(self):
        self.fail()

    def test_sn(self):
        self.fail()

    def test_mail_addresses(self):
        self.assertEqual(self.user.mail_addresses.primary.email, self.data['mailAliases'][0]['email'])

    def test_mail_addresses_to_old_userdb_format(self):
        """
        Test that we get back a dict identical to the one we put in for old-style userdb data.
        """
        to_dict_result = self.user.mail_addresses.to_list_of_dicts(old_userdb_format=True)
        self.assertEqual(to_dict_result, self.data['mailAliases'])

    def test_phone_numbers(self):
        self.fail()

    def test_passwords(self):
        """
        Test that we get back a dict identical to the one we put in for old-style userdb data.
        """
        self.assertEqual(self.user.passwords.to_list_of_dicts(old_userdb_format=True), self.data['passwords'])