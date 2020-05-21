from unittest import TestCase
import copy

from eduid_userdb.dashboard import DashboardLegacyUser as User
from eduid_userdb.dashboard.user import DashboardUser
from eduid_userdb.data_samples import NEW_USER_EXAMPLE
from eduid_userdb.testing import MOCKED_USER_STANDARD


class TestUser(TestCase):
    def test_verify_mail_and_set_as_primary(self):
        user = User(MOCKED_USER_STANDARD)

        # Save the original information so that
        # we can restore it after this test.
        old_mail_aliases = user.get_mail_aliases()
        old_mail = user.get_mail()

        # Remove the existing aliases and add one unverified
        user.set_mail_aliases([])
        user.set_mail_aliases([{'email': 'testmail@example.com', 'verified': False,}])

        # Verify the only existing mail alias and since it
        # is the only existing mail address, set it as primary.
        user.add_verified_email('testmail@example.com')

        self.assertEqual(user.get_mail_aliases(), [{'verified': True, 'email': 'testmail@example.com'}])
        self.assertEqual(user.get_mail(), 'testmail@example.com')

        # Restore the old mail settings for other tests
        user.set_mail_aliases(old_mail_aliases)
        user.set_mail(old_mail)


class TestPdataUser(TestCase):
    def test_proper_user(self):
        userdata = copy.deepcopy(NEW_USER_EXAMPLE)
        user = DashboardUser(data=userdata)
        self.assertEqual(user.user_id, userdata['_id'])
        self.assertEqual(user.eppn, userdata['eduPersonPrincipalName'])

    def test_proper_new_user(self):
        userdata = copy.deepcopy(NEW_USER_EXAMPLE)
        userid = userdata.pop('_id')
        eppn = userdata.pop('eduPersonPrincipalName')
        user = DashboardUser.construct_user(userid=userid, eppn=eppn, **userdata)
        self.assertEqual(user.user_id, userid)
        self.assertEqual(user.eppn, eppn)

    def test_missing_id(self):
        userdata = copy.deepcopy(NEW_USER_EXAMPLE)
        userid = userdata.pop('_id')
        eppn = userdata.pop('eduPersonPrincipalName')
        user = DashboardUser.construct_user(eppn=eppn, **userdata)
        self.assertNotEqual(user.user_id, userid)

    def test_missing_eppn(self):
        userdata = copy.deepcopy(NEW_USER_EXAMPLE)
        userid = userdata.pop('_id')
        userdata.pop('eduPersonPrincipalName')
        with self.assertRaises(KeyError):
            DashboardUser.construct_user(userid=userid, **userdata)
